-- =============================================================================
-- Project Nuance — Cortex Search service
-- =============================================================================
-- Powers Narrative Search, Pre-Launch Risk Score retrieval, and Analog Retrieval.
-- Hybrid (lexical + vector) search over the full enriched corpus.
--
-- Cost: ~1 credit to build, ~0.1/day to maintain on 25K-row corpus.
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;
USE SCHEMA enriched;

-- ---------------------------------------------------------------------------
-- 1. Main search service over enriched posts.
--    Attributes are filterable; the embedding column is indexed for vector search.
-- ---------------------------------------------------------------------------
-- Note: EMBEDDING_MODEL is omitted so Cortex Search picks the appropriate
-- multilingual embedding model automatically (defaults to arctic-embed-l-v2.0
-- as of late 2024). Uncomment the EMBEDDING_MODEL line below only if your
-- region supports the explicit override.
CREATE OR REPLACE CORTEX SEARCH SERVICE nuance_post_search
ON post_text
ATTRIBUTES detected_language, cultural_frame, emotional_tone,
           event_tag, post_timestamp, sentiment_score, frame_confidence
WAREHOUSE = nuance_dev_wh
TARGET_LAG = '1 hour'
-- EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
AS (
    SELECT
        cf.post_id,
        cf.post_text,
        cf.detected_language,
        cf.cultural_frame,
        cf.emotional_tone,
        cf.event_tag,
        sp.post_timestamp,
        cf.sentiment_score,
        cf.frame_confidence
    FROM enriched.cultural_frames cf
    JOIN raw_data.social_posts sp ON cf.post_id = sp.post_id
);

-- ---------------------------------------------------------------------------
-- 2. Analog library search service.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE CORTEX SEARCH SERVICE nuance_analog_search
ON description
ATTRIBUTES company, year, affected_markets, failure_frames
WAREHOUSE = nuance_dev_wh
TARGET_LAG = '24 hours'
-- EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
AS (
    SELECT analog_id, case_name, description, company, year,
           affected_markets, failure_frames, outcome_summary
    FROM library.analog_corpus
);

-- ---------------------------------------------------------------------------
-- 3. Test the services.
-- ---------------------------------------------------------------------------
SELECT
    PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'NUANCE_DB.ENRICHED.NUANCE_POST_SEARCH',
            '{"query": "product launch reaction in Japan", "limit": 5}'
        )
    ):"results" AS preview_results;
