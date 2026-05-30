-- =============================================================================
-- Project Nuance — Cultural Divergence Profile (multi-axis CDS)  [ADR-0003]
-- =============================================================================
-- Per (event_tag, language pair) we compute THREE orthogonal axes:
--   * topical_overlap     — cosine similarity of text-embedding centroids.
--                           "Are they discussing the same thing?" (usually high).
--   * frame_divergence    — Jensen-Shannon divergence (base 2, [0,1]) between the
--                           two languages' cultural-frame distributions. HEADLINE.
--   * sentiment_divergence— scaled |mean-sentiment difference|, in [0,1].
-- Plus a human-readable situation_label and a sample-size confidence.
--
-- Why multi-axis: the old single metric was cosine distance between text-embedding
-- centroids, which measures TOPIC, not cultural stance — every language pair scored
-- < 0.20 even though framing/sentiment diverge strongly. See ADR-0003 and
-- docs/07_audit_and_fixes.md.
--
-- Frame distributions are computed on DEDUPLICATED posts (one row per distinct
-- post_text) and Laplace/Dirichlet-smoothed (alpha from config) so sparse
-- per-(event,language) histograms don't inflate JSD.
--
-- `cds_score` = `headline_score` = `frame_divergence` (kept so existing consumers
-- and drift detection keep working).
--
-- Prereq: Snowpark UDFs deployed (`python snowpark/deploy.py`) registering
--   nuance_db.outputs.vector_avg (UDAF) and nuance_db.outputs.cosine_distance (UDF).
-- Cost: negligible (compute only).
-- =============================================================================

USE DATABASE nuance_db;
USE WAREHOUSE nuance_dev_wh;

-- Pipeline run tracking.
INSERT INTO internal.pipeline_runs (run_id, pipeline_name, started_at, status)
SELECT UUID_STRING(), 'cds_computation', CURRENT_TIMESTAMP(), 'running';

-- ---------------------------------------------------------------------------
-- 1. Per-(event_tag, language) text-embedding centroid (axis: topical_overlap).
--    min_posts threshold read inline from config (also gates which pairs exist).
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
-- 2. Smoothed, DEDUPLICATED frame probability distribution per (event, language).
--    p_i = (n_i + alpha) / (N + alpha*K) over the dense grid of all K frames.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE enriched._cds_frame_prob AS
WITH distinct_posts AS (
    SELECT event_tag, detected_language, post_text,
           ANY_VALUE(cultural_frame) AS cultural_frame
    FROM enriched.cultural_frames
    WHERE event_tag IS NOT NULL
    GROUP BY event_tag, detected_language, post_text
),
counts AS (
    SELECT event_tag, detected_language, cultural_frame, COUNT(*) AS n
    FROM distinct_posts
    GROUP BY 1, 2, 3
),
event_lang AS (SELECT DISTINCT event_tag, detected_language FROM counts),
frames AS (
    SELECT DISTINCT cultural_frame
    FROM enriched.cultural_frames
    WHERE cultural_frame IS NOT NULL
),
grid AS (
    SELECT el.event_tag, el.detected_language, f.cultural_frame
    FROM event_lang el CROSS JOIN frames f
),
params AS (
    SELECT
        -- TO_DOUBLE, not TO_NUMBER: TO_NUMBER defaults to scale 0 and would round 0.5 -> 1.
        (SELECT TO_DOUBLE(config_value) FROM internal.config WHERE config_key = 'frame_smoothing_alpha') AS alpha,
        (SELECT COUNT(*) FROM frames) AS k
)
SELECT
    g.event_tag,
    g.detected_language,
    g.cultural_frame,
    (COALESCE(c.n, 0) + p.alpha)
        / (SUM(COALESCE(c.n, 0)) OVER (PARTITION BY g.event_tag, g.detected_language) + p.alpha * p.k) AS prob
FROM grid g
LEFT JOIN counts c
    ON g.event_tag = c.event_tag
   AND g.detected_language = c.detected_language
   AND g.cultural_frame = c.cultural_frame
CROSS JOIN params p;

-- ---------------------------------------------------------------------------
-- 3. DEDUPLICATED mean sentiment per (event, language) (axis: sentiment_divergence).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE enriched._cds_lang_sentiment AS
WITH distinct_posts AS (
    SELECT event_tag, detected_language, post_text, AVG(sentiment_score) AS s
    FROM enriched.cultural_frames
    WHERE event_tag IS NOT NULL
    GROUP BY event_tag, detected_language, post_text
)
SELECT event_tag, detected_language, COUNT(*) AS distinct_posts, AVG(s) AS mean_sentiment
FROM distinct_posts
GROUP BY 1, 2;

-- ---------------------------------------------------------------------------
-- 4. Pairwise divergence profile per event (language_a < language_b).
--    Append a NEW batch each run (do NOT truncate) so drift detection can look
--    back at a prior reading. Consumers select the latest computed_at batch.
-- ---------------------------------------------------------------------------
INSERT INTO outputs.cultural_divergence_scores (
    cds_id, event_tag, language_a, language_b, posts_lang_a, posts_lang_b,
    cds_score, cds_confidence, topical_overlap, frame_divergence,
    sentiment_divergence, headline_score, situation_label, computed_at
)
WITH frame_jsd AS (
    SELECT
        pa.event_tag,
        pa.detected_language AS language_a,
        pb.detected_language AS language_b,
        0.5 * SUM(pa.prob * LOG(2, pa.prob / ((pa.prob + pb.prob) / 2)))
      + 0.5 * SUM(pb.prob * LOG(2, pb.prob / ((pa.prob + pb.prob) / 2))) AS jsd
    FROM enriched._cds_frame_prob pa
    JOIN enriched._cds_frame_prob pb
        ON pa.event_tag = pb.event_tag
       AND pa.cultural_frame = pb.cultural_frame
       AND pa.detected_language < pb.detected_language
    GROUP BY 1, 2, 3
),
thresholds AS (
    -- TO_DOUBLE, not TO_NUMBER: these are decimals; TO_NUMBER would round them to 0.
    SELECT
        (SELECT TO_DOUBLE(config_value) FROM internal.config WHERE config_key = 'frame_div_threshold') AS fdt,
        (SELECT TO_DOUBLE(config_value) FROM internal.config WHERE config_key = 'sentiment_div_threshold') AS sdt,
        (SELECT TO_DOUBLE(config_value) FROM internal.config WHERE config_key = 'cds_confidence_saturation') AS csat
)
SELECT
    UUID_STRING(),
    a.event_tag,
    a.detected_language,
    b.detected_language,
    a.post_count,
    b.post_count,
    j.jsd,                                                            -- cds_score (= headline)
    LEAST(LEAST(a.post_count, b.post_count) / t.csat, 1.0),          -- cds_confidence (saturation from config; post_count == distinct posts on the dedup'd corpus)
    1 - nuance_db.outputs.cosine_distance(a.centroid, b.centroid),    -- topical_overlap
    j.jsd,                                                            -- frame_divergence
    LEAST(ABS(sa.mean_sentiment - sb.mean_sentiment) / 2.0, 1.0),     -- sentiment_divergence
    j.jsd,                                                            -- headline_score
    CASE
        WHEN j.jsd >= t.fdt
             AND LEAST(ABS(sa.mean_sentiment - sb.mean_sentiment) / 2.0, 1.0) >= t.sdt
            THEN 'Divergent'
        WHEN j.jsd < t.fdt
             AND LEAST(ABS(sa.mean_sentiment - sb.mean_sentiment) / 2.0, 1.0) >= t.sdt
            THEN 'Shared lens, split mood'
        WHEN j.jsd >= t.fdt
             AND LEAST(ABS(sa.mean_sentiment - sb.mean_sentiment) / 2.0, 1.0) < t.sdt
            THEN 'Same verdict, different reasons'
        ELSE 'Aligned'
    END,
    CURRENT_TIMESTAMP()
FROM enriched.language_centroids a
JOIN enriched.language_centroids b
    ON a.event_tag = b.event_tag
   AND a.detected_language < b.detected_language
JOIN frame_jsd j
    ON j.event_tag = a.event_tag
   AND j.language_a = a.detected_language
   AND j.language_b = b.detected_language
JOIN enriched._cds_lang_sentiment sa
    ON sa.event_tag = a.event_tag AND sa.detected_language = a.detected_language
JOIN enriched._cds_lang_sentiment sb
    ON sb.event_tag = b.event_tag AND sb.detected_language = b.detected_language
CROSS JOIN thresholds t;

-- ---------------------------------------------------------------------------
-- 5. Close the run.
-- ---------------------------------------------------------------------------
UPDATE internal.pipeline_runs
SET ended_at = CURRENT_TIMESTAMP(),
    status   = 'completed',
    rows_processed = (SELECT COUNT(*) FROM outputs.cultural_divergence_scores)
WHERE pipeline_name = 'cds_computation'
  AND status = 'running';

-- ---------------------------------------------------------------------------
-- 6. Sanity check — latest batch, highest frame divergence first.
-- ---------------------------------------------------------------------------
SELECT event_tag, language_a, language_b,
       ROUND(headline_score, 3)       AS frame_div,
       ROUND(sentiment_divergence, 3) AS sentiment_div,
       ROUND(topical_overlap, 3)      AS topical_overlap,
       situation_label
FROM outputs.cultural_divergence_scores
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_tag, language_a, language_b
                           ORDER BY computed_at DESC) = 1
ORDER BY frame_div DESC
LIMIT 20;
