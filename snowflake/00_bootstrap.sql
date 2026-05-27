-- =============================================================================
-- Project Nuance — Bootstrap (single-file setup)
-- =============================================================================
-- Run this once in a Snowflake worksheet (click "Run All").
-- Idempotent: safe to re-run. Uses XS warehouse with auto-suspend for safety.
-- Total runtime: ~90s. Total credit cost: < 0.05.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Use ACCOUNTADMIN for setup, then grant to a role for daily use.
--    If you're on the trial, your default user is already ACCOUNTADMIN.
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 1. Resource monitor — caps total trial spend at 300 credits as a safety net.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE RESOURCE MONITOR nuance_trial_monitor
    WITH CREDIT_QUOTA = 300
    FREQUENCY = NEVER
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 50 PERCENT DO NOTIFY
        ON 80 PERCENT DO NOTIFY
        ON 95 PERCENT DO SUSPEND
        ON 100 PERCENT DO SUSPEND_IMMEDIATE;

-- ---------------------------------------------------------------------------
-- 2. Warehouse — XS only, 60s auto-suspend.
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS nuance_dev_wh
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Nuance development warehouse — XS, auto-suspend 60s';

ALTER WAREHOUSE nuance_dev_wh SET RESOURCE_MONITOR = nuance_trial_monitor;

USE WAREHOUSE nuance_dev_wh;

-- ---------------------------------------------------------------------------
-- 3. Database + schemas.
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS nuance_db
    COMMENT = 'Project Nuance — cultural intelligence engine';

USE DATABASE nuance_db;

CREATE SCHEMA IF NOT EXISTS raw_data    COMMENT = 'Raw multilingual content';
CREATE SCHEMA IF NOT EXISTS enriched    COMMENT = 'AI-enriched derived tables';
CREATE SCHEMA IF NOT EXISTS outputs     COMMENT = 'User-facing outputs (CDS, PLCS, briefs)';
CREATE SCHEMA IF NOT EXISTS internal    COMMENT = 'Configuration, logs, monitoring';
CREATE SCHEMA IF NOT EXISTS library     COMMENT = 'Curated content (analog corpus, taxonomies)';

-- ---------------------------------------------------------------------------
-- 4. Config table — centralized model identifiers and tunable parameters.
--    Edit values here if Snowflake renames a Cortex model in your region.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.internal.config (
    config_key   VARCHAR PRIMARY KEY,
    config_value VARCHAR NOT NULL,
    updated_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    notes        VARCHAR
);

MERGE INTO nuance_db.internal.config t
USING (
    SELECT * FROM VALUES
        ('model_large',      'claude-4-sonnet',
            'Primary LLM for PLCS, Cultural Translator, AI Brief. ' ||
            'Verify with SELECT * FROM SNOWFLAKE.CORTEX.LIST_MODELS()'),
        ('model_small',      'mistral-7b',
            'Bulk classification first pass'),
        ('model_medium',     'mistral-large2',
            'Fallback if model_large unavailable'),
        ('embedding_model',  'snowflake-arctic-embed-l-v2.0',
            '1024-dim multilingual embedding model'),
        ('embedding_dims',   '1024',                    'Vector dimensionality'),
        ('cds_threshold',    '0.35',                    'CDS >= this = meaningful divergence'),
        ('cds_risk',         '0.55',                    'CDS >= this = cultural risk signal'),
        ('plcs_high_risk',   '60',                      'PLCS >= this triggers Translator suggestion'),
        ('plcs_critical',    '80',                      'PLCS >= this triggers urgent alert'),
        ('batch_size',       '5000',                    'Pipeline batch size'),
        ('min_posts_for_centroid', '10',                'Min posts/lang/event for valid CDS'),
        ('drift_alert_default_delta', '0.10',           'Default drift alert threshold on the headline (frame_divergence) scale'),
        ('frame_div_threshold', '0.23',                 'frame_divergence (JSD) >= this = meaningful divergence (HEADLINE). Calibrated 2026-05-26 (~top third); re-derive after a data rebuild'),
        ('frame_div_risk',      '0.34',                 'frame_divergence (JSD) >= this = cultural risk signal. Calibrated 2026-05-26 (~top 10%)'),
        ('sentiment_div_threshold', '0.13',             'sentiment_divergence >= this = markets feel differently. Calibrated 2026-05-26 (~top 25%)'),
        ('frame_smoothing_alpha', '0.5',                'Dirichlet/Laplace alpha added to each frame count before normalizing (tames sparse-data JSD inflation). Read with TO_DOUBLE, not TO_NUMBER')
    AS s(config_key, config_value, notes)
) s
ON t.config_key = s.config_key
WHEN NOT MATCHED THEN
    INSERT (config_key, config_value, notes)
    VALUES (s.config_key, s.config_value, s.notes);

-- ---------------------------------------------------------------------------
-- 5. Apply raw / enriched / outputs / internal table definitions.
--    Each of these is fully defined in its own file but inlined here so the
--    bootstrap is a single click. The files in this directory are kept in sync.
-- ---------------------------------------------------------------------------

-- 5a. raw_data.social_posts ----------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.raw_data.social_posts (
    post_id           VARCHAR        NOT NULL PRIMARY KEY,
    post_text         VARCHAR        NOT NULL,
    detected_language VARCHAR(8),                   -- ISO 639-1 like 'en','ja','zh'
    source_platform   VARCHAR,                      -- 'twitter','reddit','news','reviews','support'
    source_url        VARCHAR,
    author_handle     VARCHAR,
    post_timestamp    TIMESTAMP_NTZ,
    event_tag         VARCHAR,                      -- user-assigned event label
    country_hint      VARCHAR(8),                   -- optional ISO country guess
    ingested_at       TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
    raw_metadata      VARIANT
);

-- 5b. enriched.post_embeddings -------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.enriched.post_embeddings (
    post_id              VARCHAR PRIMARY KEY,
    post_text            VARCHAR,
    detected_language    VARCHAR(8),
    event_tag            VARCHAR,
    post_timestamp       TIMESTAMP_NTZ,
    embedding            VECTOR(FLOAT, 1024),
    embedding_model      VARCHAR,
    embedded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5c. enriched.cultural_frames -------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.enriched.cultural_frames (
    post_id             VARCHAR PRIMARY KEY,
    post_text           VARCHAR,
    detected_language   VARCHAR(8),
    event_tag           VARCHAR,
    cultural_frame      VARCHAR,        -- one of the 12 taxonomy values
    frame_confidence    FLOAT,
    sentiment_score     FLOAT,          -- [-1, 1]
    emotional_tone      VARCHAR,        -- one of Plutchik's 7
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5d. outputs.cultural_divergence_scores ---------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.outputs.cultural_divergence_scores (
    cds_id              VARCHAR PRIMARY KEY,
    event_tag           VARCHAR,
    language_a          VARCHAR(8),
    language_b          VARCHAR(8),
    posts_lang_a        INTEGER,
    posts_lang_b        INTEGER,
    cds_score           FLOAT,        -- = headline_score (frame_divergence); kept for back-compat
    cds_confidence      FLOAT,        -- scales with smaller sample size, capped at 1.0
    topical_overlap      FLOAT,       -- axis 1: cosine similarity of text-embedding centroids ("same conversation")
    frame_divergence     FLOAT,       -- axis 2 (HEADLINE): Jensen-Shannon divergence of frame distributions
    sentiment_divergence FLOAT,       -- axis 3: scaled |mean-sentiment difference| in [0,1]
    headline_score       FLOAT,       -- = frame_divergence (the primary metric shown in the UI)
    situation_label      VARCHAR,     -- Aligned / Divergent / Shared lens, split mood / Same verdict, different reasons
    computed_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5e. outputs.pre_launch_risk_scores -------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.outputs.pre_launch_risk_scores (
    plcs_id             VARCHAR PRIMARY KEY,
    requested_by        VARCHAR,
    draft_content       VARCHAR,
    source_language     VARCHAR(8),
    target_market       VARCHAR(8),
    plcs_score          INTEGER,        -- 0..100
    plcs_confidence     FLOAT,
    top_frames          ARRAY,          -- ['historical_grievance','threat_framing','collectivist']
    nearest_analogs     ARRAY,          -- post_ids of historical neighbors
    risk_narrative      VARCHAR,        -- LLM-synthesized
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inputs_json         VARIANT,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5f. outputs.cultural_translator_runs ----------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.outputs.cultural_translator_runs (
    run_id              VARCHAR PRIMARY KEY,
    requested_by        VARCHAR,
    source_content      VARCHAR,
    source_language     VARCHAR(8),
    target_market       VARCHAR(8),
    target_frame_hint   VARCHAR,
    adapted_variants    ARRAY,          -- [{variant_text, frame_shift, rationale}]
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5g. outputs.ai_briefs ---------------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.outputs.ai_briefs (
    brief_id            VARCHAR PRIMARY KEY,
    requested_by        VARCHAR,
    event_tag           VARCHAR,
    target_languages    ARRAY,
    brief_markdown      VARCHAR,
    source_post_ids     ARRAY,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5h. library.analog_corpus -----------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.library.analog_corpus (
    analog_id           VARCHAR PRIMARY KEY,
    case_name           VARCHAR,        -- 'HSBC Assume Nothing 2009'
    company             VARCHAR,
    year                INTEGER,
    description         VARCHAR,
    affected_markets    ARRAY,
    failure_frames      ARRAY,
    outcome_summary     VARCHAR,
    source_url          VARCHAR,
    embedding           VECTOR(FLOAT, 1024),
    embedded_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5i. library.tracked_entities --------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.library.tracked_entities (
    entity_id           VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    entity_name         VARCHAR NOT NULL,
    entity_type         VARCHAR DEFAULT 'brand',  -- 'brand','product','campaign','event'
    owner_email         VARCHAR NOT NULL,
    languages           ARRAY,
    cds_threshold_delta FLOAT DEFAULT 0.15,
    cds_threshold_abs   FLOAT DEFAULT 0.55,
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5j. library.frame_taxonomy ----------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.library.frame_taxonomy (
    frame_name      VARCHAR PRIMARY KEY,
    description     VARCHAR,
    example_phrases ARRAY,
    hofstede_dim    VARCHAR
);

MERGE INTO nuance_db.library.frame_taxonomy t
USING (
    SELECT 'individualist' AS frame_name,
           'Emphasizes personal autonomy, individual rights, self-expression' AS description,
           ARRAY_CONSTRUCT('my choice','live your truth','be yourself') AS example_phrases,
           'individualism' AS hofstede_dim
    UNION ALL
    SELECT 'collectivist',
           'Emphasizes group harmony, family/community obligations, shared identity',
           ARRAY_CONSTRUCT('our community','for the family','together we'),
           'individualism'
    UNION ALL
    SELECT 'nationalist',
           'Invokes national pride, in-group preference, cultural sovereignty',
           ARRAY_CONSTRUCT('our country','national pride','foreign interference'),
           'in_group_loyalty'
    UNION ALL
    SELECT 'globalist',
           'Embraces cross-cultural exchange, international cooperation, cosmopolitanism',
           ARRAY_CONSTRUCT('global citizen','one world','cross-border'),
           'in_group_loyalty'
    UNION ALL
    SELECT 'threat_framing',
           'Frames event as danger, loss, or vulnerability',
           ARRAY_CONSTRUCT('we must protect','at risk','under attack'),
           'uncertainty_avoidance'
    UNION ALL
    SELECT 'opportunity_framing',
           'Frames event as benefit, growth, or possibility',
           ARRAY_CONSTRUCT('great opportunity','chance to grow','exciting future'),
           'uncertainty_avoidance'
    UNION ALL
    SELECT 'historical_grievance',
           'Invokes past wrongs, colonial memory, ethnic or political grievance',
           ARRAY_CONSTRUCT('never forget','they always','since history'),
           'long_term_orientation'
    UNION ALL
    SELECT 'status_quo',
           'Supports preservation of current order, tradition, established norms',
           ARRAY_CONSTRUCT('the way things should be','traditional values','dont change'),
           'long_term_orientation'
    UNION ALL
    SELECT 'reform_seeking',
           'Calls for change, progress, structural improvement',
           ARRAY_CONSTRUCT('we need to change','time for reform','better future'),
           'long_term_orientation'
    UNION ALL
    SELECT 'spiritual_ethical',
           'Frames event in moral, religious, or ethical terms',
           ARRAY_CONSTRUCT('its wrong','moral obligation','spiritual meaning'),
           'indulgence'
    UNION ALL
    SELECT 'pragmatic',
           'Focuses on practical outcomes, efficiency, results',
           ARRAY_CONSTRUCT('lets get it done','whatever works','show me results'),
           'indulgence'
    UNION ALL
    SELECT 'ambiguous',
           'No clear frame detectable; mixed or unclear signaling',
           ARRAY_CONSTRUCT(),
           NULL
) s
ON t.frame_name = s.frame_name
WHEN NOT MATCHED THEN
    INSERT (frame_name, description, example_phrases, hofstede_dim)
    VALUES (s.frame_name, s.description, s.example_phrases, s.hofstede_dim);

-- 5k. internal.pipeline_runs (observability) ------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.internal.pipeline_runs (
    run_id              VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    pipeline_name       VARCHAR NOT NULL,
    started_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    ended_at            TIMESTAMP_NTZ,
    status              VARCHAR DEFAULT 'running',  -- 'running','completed','failed'
    rows_processed      INTEGER,
    rows_failed         INTEGER DEFAULT 0,
    credits_estimated   FLOAT,
    error_message       VARCHAR
);

-- 5l. internal.inference_logs --------------------------------------------
CREATE TABLE IF NOT EXISTS nuance_db.internal.inference_logs (
    log_id              VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    pipeline_name       VARCHAR,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    input_summary       VARCHAR,
    output_summary      VARCHAR,
    tokens_estimated    INTEGER,
    latency_ms          INTEGER,
    logged_at           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------------
-- 6. Helper view: credit status (read-only summary).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW nuance_db.internal.credit_status AS
SELECT
    DATE_TRUNC('DAY', start_time)::DATE       AS usage_date,
    SUM(credits_used)                          AS credits_used,
    SUM(SUM(credits_used)) OVER (ORDER BY DATE_TRUNC('DAY', start_time)) AS credits_cumulative
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE warehouse_name = 'NUANCE_DEV_WH'
  AND start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY DATE_TRUNC('DAY', start_time)
ORDER BY usage_date DESC;

-- ---------------------------------------------------------------------------
-- 7. Least-privilege role for the MCP server (and any external API client).
--
--    WHY THIS EXISTS:
--    The MCP server connects to Snowflake on behalf of API callers (AI agents,
--    Claude Desktop, etc.). It should never run as ACCOUNTADMIN — that role can
--    drop tables, read billing data, and modify account settings. NUANCE_APP_ROLE
--    is locked down to exactly what the MCP server needs: read the data, call
--    the stored procedures, write results.
--
--    AFTER RUNNING THIS SECTION:
--    Replace <YOUR_SNOWFLAKE_USERNAME> below with your actual username, then
--    run the GRANT. To find your username: top-right corner of the Snowflake UI
--    shows your name; click it → "Profile" to see the exact username.
-- ---------------------------------------------------------------------------

-- 7a. Create the role.
CREATE ROLE IF NOT EXISTS nuance_app_role
    COMMENT = 'Least-privilege role for the Nuance MCP server. Can read data, call stored procedures, and write output rows. Cannot drop objects, modify account settings, or access billing.';

-- 7b. Allow the role to use the warehouse (required to run any query at all).
GRANT USAGE ON WAREHOUSE nuance_dev_wh TO ROLE nuance_app_role;

-- 7c. Allow the role to see the database and all its schemas.
GRANT USAGE ON DATABASE nuance_db                   TO ROLE nuance_app_role;
GRANT USAGE ON SCHEMA nuance_db.raw_data            TO ROLE nuance_app_role;
GRANT USAGE ON SCHEMA nuance_db.enriched            TO ROLE nuance_app_role;
GRANT USAGE ON SCHEMA nuance_db.outputs             TO ROLE nuance_app_role;
GRANT USAGE ON SCHEMA nuance_db.library             TO ROLE nuance_app_role;
GRANT USAGE ON SCHEMA nuance_db.internal            TO ROLE nuance_app_role;

-- 7d. Read access on all tables (for list_events, list_tracked_entities,
--     get_divergence, and the dashboard queries).
GRANT SELECT ON ALL TABLES IN SCHEMA nuance_db.raw_data  TO ROLE nuance_app_role;
GRANT SELECT ON ALL TABLES IN SCHEMA nuance_db.enriched  TO ROLE nuance_app_role;
GRANT SELECT ON ALL TABLES IN SCHEMA nuance_db.outputs   TO ROLE nuance_app_role;
GRANT SELECT ON ALL TABLES IN SCHEMA nuance_db.library   TO ROLE nuance_app_role;
GRANT SELECT ON ALL TABLES IN SCHEMA nuance_db.internal  TO ROLE nuance_app_role;

-- 7e. Write access: stored procedures need to INSERT rows into output tables,
--     and the Drift Alerts page needs to INSERT/UPDATE tracked_entities.
GRANT INSERT        ON ALL TABLES IN SCHEMA nuance_db.outputs TO ROLE nuance_app_role;
GRANT INSERT, UPDATE ON nuance_db.library.tracked_entities    TO ROLE nuance_app_role;

-- 7f. Future-proof: any NEW tables created later in these schemas automatically
--     get the same read/write grants without needing another GRANT command.
GRANT SELECT ON FUTURE TABLES IN SCHEMA nuance_db.raw_data  TO ROLE nuance_app_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA nuance_db.enriched  TO ROLE nuance_app_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA nuance_db.outputs   TO ROLE nuance_app_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA nuance_db.library   TO ROLE nuance_app_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA nuance_db.internal  TO ROLE nuance_app_role;
GRANT INSERT ON FUTURE TABLES IN SCHEMA nuance_db.outputs   TO ROLE nuance_app_role;

-- 7g. Allow the role to call the stored procedures (PLCS, Translator, Analogs,
--     Brief). The procedures themselves run under owner's rights (ACCOUNTADMIN),
--     so this role never directly touches Cortex — it just triggers the call.
GRANT USAGE ON ALL PROCEDURES IN SCHEMA nuance_db.outputs TO ROLE nuance_app_role;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA nuance_db.outputs TO ROLE nuance_app_role;

-- 7h. Assign the role to your Snowflake user.
--     *** EDIT THIS LINE: replace <YOUR_SNOWFLAKE_USERNAME> with your username ***
--     Example: GRANT ROLE nuance_app_role TO USER mike_boozer;
GRANT ROLE nuance_app_role TO USER MIKEBOOZER;

-- Verify the role was created and granted.
SHOW GRANTS TO ROLE nuance_app_role;

-- ---------------------------------------------------------------------------
-- 8. Cortex availability check.
--    Run these manually in a separate worksheet after bootstrap completes.
--    They are not included here because Cortex may require separate enablement.
--
--    To test manually, run:
--      SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-7b', 'Say OK.') AS test;
--      SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', 'test') AS test;
--
--    If you get "not available for trial accounts", contact Snowflake support
--    or upgrade to a paid account — Cortex is required for the full pipeline.
--
--    To list available models in your region:
--      SELECT * FROM TABLE(SNOWFLAKE.CORTEX.LIST_MODELS());
-- ---------------------------------------------------------------------------

SELECT 'Bootstrap complete. Tables created: ' || COUNT(*) AS status
FROM nuance_db.information_schema.tables
WHERE table_schema IN ('RAW_DATA','ENRICHED','OUTPUTS','INTERNAL','LIBRARY');

-- Expected output: ~13 tables.
