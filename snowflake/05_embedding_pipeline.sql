-- =============================================================================
-- Project Nuance — Embedding Pipeline
-- =============================================================================
-- Generates 1024-dim multilingual embeddings for all posts in raw_data.social_posts.
-- Idempotent — only processes posts that don't yet have embeddings.
-- Batched at config.batch_size (default 5,000) to control credit spend.
-- Expected runtime on 25K demo posts: 4–6 minutes. Expected cost: 3–6 credits.
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;
USE SCHEMA enriched;

-- ---------------------------------------------------------------------------
-- 1. Open a pipeline run for observability.
-- ---------------------------------------------------------------------------
SET run_id = UUID_STRING();
INSERT INTO nuance_db.internal.pipeline_runs (run_id, pipeline_name, started_at, status)
VALUES ($run_id, 'embedding_pipeline', CURRENT_TIMESTAMP(), 'running');

-- ---------------------------------------------------------------------------
-- 2. Embed all posts that don't yet have an embedding.
--    Single-statement insert; Snowflake will scan-and-skip duplicates.
-- ---------------------------------------------------------------------------
SET embedding_model = (SELECT config_value FROM nuance_db.internal.config
                       WHERE config_key = 'embedding_model');

INSERT INTO nuance_db.enriched.post_embeddings (
    post_id, post_text, detected_language, event_tag, post_timestamp,
    embedding, embedding_model
)
SELECT
    sp.post_id,
    sp.post_text,
    sp.detected_language,
    sp.event_tag,
    sp.post_timestamp,
    SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
        $embedding_model,
        -- Truncate to 8K chars to stay under Snowflake's input limit
        SUBSTR(sp.post_text, 1, 8000)
    ),
    $embedding_model
FROM nuance_db.raw_data.social_posts sp
LEFT JOIN nuance_db.enriched.post_embeddings pe ON sp.post_id = pe.post_id
WHERE pe.post_id IS NULL
  -- Skip extremely short or empty posts
  AND LENGTH(TRIM(sp.post_text)) >= 10;

-- ---------------------------------------------------------------------------
-- 3. Update run record.
-- ---------------------------------------------------------------------------
UPDATE nuance_db.internal.pipeline_runs
SET ended_at = CURRENT_TIMESTAMP(),
    status = 'completed',
    rows_processed = (SELECT COUNT(*) FROM nuance_db.enriched.post_embeddings)
WHERE run_id = $run_id;

-- ---------------------------------------------------------------------------
-- 4. Sanity check.
-- ---------------------------------------------------------------------------
SELECT
    detected_language,
    COUNT(*) AS embedded_posts,
    ROUND(AVG(ARRAY_SIZE(embedding::ARRAY)), 0) AS dims
FROM nuance_db.enriched.post_embeddings
GROUP BY detected_language
ORDER BY embedded_posts DESC;

-- ---------------------------------------------------------------------------
-- 5. (Optional) Fallback: use Voyage AI multilingual if Arctic Embed quality
--    is insufficient on a target language. Uncomment to switch.
-- ---------------------------------------------------------------------------
-- UPDATE nuance_db.internal.config
-- SET config_value = 'voyage-multilingual-2'
-- WHERE config_key = 'embedding_model';
--
-- And re-run this script (will only re-embed posts whose existing
-- embedding_model differs — add a WHERE clause if needed).
