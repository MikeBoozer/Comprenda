-- =============================================================================
-- Project Nuance — Cultural Divergence Score (CDS)
-- =============================================================================
-- Proprietary metric: cosine distance between per-language embedding centroids
-- for the same event_tag. CDS in [0, 1]; > 0.35 = meaningful, > 0.55 = risk.
--
-- Prereq: deploy Snowpark UDFs first via:
--     python snowpark/deploy.py
-- which registers `nuance_db.outputs.vector_avg` (UDAF) and
-- `nuance_db.outputs.cosine_distance` (UDF).
--
-- Cost: negligible (compute only).
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;

-- Pipeline run tracking (INSERT...SELECT avoids the SET subquery limitation).
INSERT INTO internal.pipeline_runs (run_id, pipeline_name, started_at, status)
SELECT UUID_STRING(), 'cds_computation', CURRENT_TIMESTAMP(), 'running';

-- ---------------------------------------------------------------------------
-- 1. Per-(event_tag, language) centroid.
--    VECTOR_AVG accepts ARRAY (Snowflake UDAFs don't support VECTOR type),
--    so we cast embedding::ARRAY going in and ::VECTOR(FLOAT,1024) coming out.
--    min_posts threshold read inline from config to avoid SET subquery issue.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE enriched.language_centroids AS
SELECT
    pe.event_tag,
    pe.detected_language,
    COUNT(*) AS post_count,
    nuance_db.outputs.vector_avg(pe.embedding::ARRAY)::VECTOR(FLOAT, 1024) AS centroid
FROM enriched.post_embeddings pe
WHERE pe.event_tag IS NOT NULL
GROUP BY pe.event_tag, pe.detected_language
HAVING COUNT(*) >= (
    SELECT TO_NUMBER(config_value)
    FROM internal.config
    WHERE config_key = 'min_posts_for_centroid'
);

-- ---------------------------------------------------------------------------
-- 2. Pairwise CDS across language pairs per event.
--    Append a NEW row each run (do NOT truncate) so drift detection in
--    09_alerts_and_tasks.sql can look back 23+ hours for a prior reading.
-- ---------------------------------------------------------------------------
INSERT INTO outputs.cultural_divergence_scores (
    cds_id, event_tag, language_a, language_b,
    posts_lang_a, posts_lang_b,
    cds_score, cds_confidence, computed_at
)
SELECT
    UUID_STRING(),
    a.event_tag,
    a.detected_language,
    b.detected_language,
    a.post_count,
    b.post_count,
    nuance_db.outputs.cosine_distance(a.centroid, b.centroid),
    -- Confidence proxy: scales with the smaller of the two sample sizes,
    -- capped at 1.0 once both languages exceed 100 posts.
    LEAST(LEAST(a.post_count, b.post_count) / 100.0, 1.0),
    CURRENT_TIMESTAMP()
FROM enriched.language_centroids a
JOIN enriched.language_centroids b
    ON a.event_tag = b.event_tag
    AND a.detected_language < b.detected_language;

-- ---------------------------------------------------------------------------
-- 3. Close the run.
-- ---------------------------------------------------------------------------
UPDATE internal.pipeline_runs
SET ended_at = CURRENT_TIMESTAMP(),
    status   = 'completed',
    rows_processed = (SELECT COUNT(*) FROM outputs.cultural_divergence_scores)
WHERE pipeline_name = 'cds_computation'
  AND status = 'running';

-- ---------------------------------------------------------------------------
-- 4. Top divergences for sanity check.
-- ---------------------------------------------------------------------------
SELECT event_tag, language_a, language_b,
       ROUND(cds_score, 3) AS cds,
       posts_lang_a, posts_lang_b,
       ROUND(cds_confidence, 2) AS conf
FROM outputs.cultural_divergence_scores
ORDER BY cds_score DESC
LIMIT 20;
