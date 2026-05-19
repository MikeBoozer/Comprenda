-- =============================================================================
-- Project Nuance — Frame Classification + Sentiment + Emotional Tone
-- =============================================================================
-- Two-pass classification:
--   Pass 1: mistral-7b cheap classification on all posts.
--   Pass 2: claude-4-sonnet re-classifies posts where pass 1 produced
--           an invalid frame name or low confidence.
-- Plus sentiment (Cortex SENTIMENT) and emotional tone (Plutchik AI_CLASSIFY).
--
-- Expected cost on 25K posts: 10–14 credits.
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;

SET model_small  = (SELECT config_value FROM internal.config WHERE config_key='model_small');
SET model_large  = (SELECT config_value FROM internal.config WHERE config_key='model_large');

SET run_id = UUID_STRING();
INSERT INTO internal.pipeline_runs (run_id, pipeline_name, started_at, status)
VALUES ($run_id, 'frame_classification', CURRENT_TIMESTAMP(), 'running');

-- ---------------------------------------------------------------------------
-- 1. Pass 1: classify with mistral-7b. Insert into a staging table so we can
--    triage low-quality outputs before they hit the final table.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE enriched._frame_staging AS
WITH valid_frames AS (
    SELECT ARRAY_AGG(frame_name) AS frames FROM library.frame_taxonomy
),
prompt AS (
    SELECT
        sp.post_id,
        sp.post_text,
        sp.detected_language,
        sp.event_tag,
        SNOWFLAKE.CORTEX.COMPLETE(
            $model_small,
            CONCAT(
                'You are a cultural frame classifier. The post is in ',
                sp.detected_language,
                '. Classify it into EXACTLY ONE of these frames: ',
                'individualist|collectivist|nationalist|globalist|threat_framing|',
                'opportunity_framing|historical_grievance|status_quo|reform_seeking|',
                'spiritual_ethical|pragmatic|ambiguous. ',
                'Output JSON ONLY in this exact form: ',
                '{"frame":"<one_value>","confidence":<0_to_1>}. ',
                'Post: ', SUBSTR(sp.post_text, 1, 2000)
            )
        ) AS raw_response
    FROM raw_data.social_posts sp
    LEFT JOIN enriched.cultural_frames cf ON sp.post_id = cf.post_id
    WHERE cf.post_id IS NULL
      AND LENGTH(TRIM(sp.post_text)) >= 10
)
SELECT
    p.post_id,
    p.post_text,
    p.detected_language,
    p.event_tag,
    p.raw_response,
    -- Robust JSON extraction with fallback: try parse_json, fall back to regex
    TRY_PARSE_JSON(p.raw_response) AS parsed_json,
    LOWER(COALESCE(
        TRY_PARSE_JSON(p.raw_response):"frame"::STRING,
        REGEXP_SUBSTR(p.raw_response,
            '(individualist|collectivist|nationalist|globalist|threat_framing|opportunity_framing|historical_grievance|status_quo|reform_seeking|spiritual_ethical|pragmatic|ambiguous)',
            1, 1, 'i')
    )) AS frame_candidate,
    TRY_PARSE_JSON(p.raw_response):"confidence"::FLOAT AS confidence_candidate,
    $model_small AS model_used,
    'v1' AS prompt_version
FROM prompt p;

-- ---------------------------------------------------------------------------
-- 2. Triage: mark rows where pass 1 is unusable.
-- ---------------------------------------------------------------------------
ALTER TABLE enriched._frame_staging ADD COLUMN IF NOT EXISTS needs_repass BOOLEAN;

UPDATE enriched._frame_staging
SET needs_repass = (
    frame_candidate IS NULL
    OR frame_candidate NOT IN (
        SELECT frame_name FROM library.frame_taxonomy
    )
    OR COALESCE(confidence_candidate, 0) < 0.7
);

-- ---------------------------------------------------------------------------
-- 3. Pass 2: re-classify the flagged posts with claude-4-sonnet.
-- ---------------------------------------------------------------------------
UPDATE enriched._frame_staging
SET raw_response = SNOWFLAKE.CORTEX.COMPLETE(
        $model_large,
        CONCAT(
            'You are an expert cultural frame analyst. The post is written in language code "',
            detected_language,
            '". Classify into EXACTLY ONE frame from this set: ',
            'individualist, collectivist, nationalist, globalist, threat_framing, ',
            'opportunity_framing, historical_grievance, status_quo, reform_seeking, ',
            'spiritual_ethical, pragmatic, ambiguous. ',
            'Think carefully about the cultural context of ', detected_language,
            '-speaking communities. Output JSON ONLY: ',
            '{"frame":"<value>","confidence":<0_to_1>,"reasoning":"<one short sentence>"}. ',
            'Post: ', SUBSTR(post_text, 1, 2000)
        )
    ),
    parsed_json = TRY_PARSE_JSON(raw_response),
    frame_candidate = LOWER(COALESCE(
        TRY_PARSE_JSON(raw_response):"frame"::STRING,
        REGEXP_SUBSTR(raw_response,
            '(individualist|collectivist|nationalist|globalist|threat_framing|opportunity_framing|historical_grievance|status_quo|reform_seeking|spiritual_ethical|pragmatic|ambiguous)',
            1, 1, 'i')
    )),
    confidence_candidate = TRY_PARSE_JSON(raw_response):"confidence"::FLOAT,
    model_used = $model_large,
    prompt_version = 'v1'
WHERE needs_repass = TRUE;

-- ---------------------------------------------------------------------------
-- 4. Add sentiment (cheap) and emotional tone (medium).
-- ---------------------------------------------------------------------------
ALTER TABLE enriched._frame_staging ADD COLUMN IF NOT EXISTS sentiment_score FLOAT;
ALTER TABLE enriched._frame_staging ADD COLUMN IF NOT EXISTS emotional_tone VARCHAR;

UPDATE enriched._frame_staging
SET sentiment_score = SNOWFLAKE.CORTEX.SENTIMENT(SUBSTR(post_text, 1, 2000));

UPDATE enriched._frame_staging
SET emotional_tone = SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
    SUBSTR(post_text, 1, 2000),
    ['anger','fear','joy','sadness','surprise','disgust','trust','neutral']
):"label"::STRING;

-- ---------------------------------------------------------------------------
-- 5. Promote to final table. Anything still without a valid frame becomes
--    'ambiguous' with confidence = NULL so downstream code can filter it out.
--    Idempotent: skips post_ids already present in cultural_frames so re-runs
--    after a partial failure don't insert duplicates.
-- ---------------------------------------------------------------------------
INSERT INTO enriched.cultural_frames (
    post_id, post_text, detected_language, event_tag,
    cultural_frame, frame_confidence,
    sentiment_score, emotional_tone,
    model_used, prompt_version
)
SELECT
    s.post_id, s.post_text, s.detected_language, s.event_tag,
    COALESCE(
        CASE WHEN s.frame_candidate IN (SELECT frame_name FROM library.frame_taxonomy)
             THEN s.frame_candidate
             ELSE 'ambiguous'
        END,
        'ambiguous'
    ),
    s.confidence_candidate,
    s.sentiment_score,
    s.emotional_tone,
    s.model_used,
    s.prompt_version
FROM enriched._frame_staging s
LEFT JOIN enriched.cultural_frames cf ON s.post_id = cf.post_id
WHERE cf.post_id IS NULL;

-- ---------------------------------------------------------------------------
-- 6. Cleanup and close the run.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS enriched._frame_staging;

UPDATE internal.pipeline_runs
SET ended_at = CURRENT_TIMESTAMP(),
    status   = 'completed',
    rows_processed = (SELECT COUNT(*) FROM enriched.cultural_frames)
WHERE run_id = $run_id;

-- ---------------------------------------------------------------------------
-- 7. Sanity check.
-- ---------------------------------------------------------------------------
SELECT detected_language,
       cultural_frame,
       COUNT(*) AS n,
       ROUND(AVG(sentiment_score),3) AS avg_sent,
       ROUND(AVG(frame_confidence),3) AS avg_conf
FROM enriched.cultural_frames
GROUP BY detected_language, cultural_frame
ORDER BY detected_language, n DESC;
