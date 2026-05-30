-- =============================================================================
-- Project Nuance — Native App setup_script
-- =============================================================================
-- Runs inside the consumer's Snowflake account when they install Nuance from
-- Marketplace. Creates the app's schemas, tables, procedures, and Streamlit.
-- Idempotent.
-- =============================================================================

-- App role used internally for permissions.
CREATE APPLICATION ROLE IF NOT EXISTS app_user;
CREATE APPLICATION ROLE IF NOT EXISTS app_admin;

-- App schemas.
CREATE OR ALTER VERSIONED SCHEMA app_instance;
GRANT USAGE ON SCHEMA app_instance TO APPLICATION ROLE app_user;
GRANT USAGE ON SCHEMA app_instance TO APPLICATION ROLE app_admin;

CREATE SCHEMA IF NOT EXISTS app_data;
GRANT USAGE ON SCHEMA app_data TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Application config table (copied from the dev bootstrap).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE app_data.config (
    config_key   VARCHAR PRIMARY KEY,
    config_value VARCHAR NOT NULL,
    updated_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    notes        VARCHAR
);

MERGE INTO app_data.config t
USING (
    SELECT * FROM VALUES
        ('model_large',     'claude-4-sonnet',               'Primary LLM'),
        ('model_small',     'mistral-7b',                    'Bulk classification'),
        ('embedding_model', 'snowflake-arctic-embed-l-v2.0', '1024-dim multilingual'),
        ('embedding_dims',  '1024',                          'Vector dims'),
        ('frame_div_threshold',       '0.23',                'frame_divergence (JSD headline) >= this = meaningful [ADR-0003]'),
        ('frame_div_risk',            '0.34',                'frame_divergence (JSD headline) >= this = cultural risk signal'),
        ('sentiment_div_threshold',   '0.13',                'sentiment_divergence >= this = markets feel differently'),
        ('frame_smoothing_alpha',     '0.5',                 'Dirichlet/Laplace alpha for frame-distribution smoothing. Read with TO_DOUBLE'),
        ('min_posts_for_centroid',    '10',                  'Min posts/lang/event for a valid CDS pair'),
        ('cds_confidence_saturation', '25',                  'cds_confidence = LEAST(min(posts_a,posts_b)/this, 1.0)'),
        ('plcs_high_risk',  '60',                            'PLCS high-risk'),
        ('plcs_critical',   '80',                            'PLCS critical')
    AS s(config_key, config_value, notes)
) s ON t.config_key = s.config_key
WHEN NOT MATCHED THEN INSERT (config_key, config_value, notes)
VALUES (s.config_key, s.config_value, s.notes);

-- ---------------------------------------------------------------------------
-- Enriched / outputs / library tables (same DDL as the dev bootstrap; the
-- application stores its data in app_data.* tables inside the consumer's account).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_data.post_embeddings (
    post_id           VARCHAR PRIMARY KEY,
    post_text         VARCHAR,
    detected_language VARCHAR(8),
    event_tag         VARCHAR,
    post_timestamp    TIMESTAMP_NTZ,
    embedding         VECTOR(FLOAT, 1024),
    embedding_model   VARCHAR,
    embedded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.cultural_frames (
    post_id             VARCHAR PRIMARY KEY,
    post_text           VARCHAR,
    detected_language   VARCHAR(8),
    event_tag           VARCHAR,
    cultural_frame      VARCHAR,
    frame_confidence    FLOAT,
    sentiment_score     FLOAT,
    emotional_tone      VARCHAR,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.cultural_divergence_scores (
    cds_id              VARCHAR PRIMARY KEY,
    event_tag           VARCHAR,
    language_a          VARCHAR(8),
    language_b          VARCHAR(8),
    posts_lang_a        INTEGER,
    posts_lang_b        INTEGER,
    cds_score           FLOAT,        -- = headline_score (frame_divergence); kept for back-compat
    cds_confidence      FLOAT,        -- scales with smaller sample size, capped at 1.0
    topical_overlap      FLOAT,       -- axis 1: cosine similarity of text-embedding centroids ("same conversation")
    frame_divergence     FLOAT,       -- axis 2 (HEADLINE): Jensen-Shannon divergence of frame distributions [ADR-0003]
    sentiment_divergence FLOAT,       -- axis 3: scaled |mean-sentiment difference| in [0,1]
    headline_score       FLOAT,       -- = frame_divergence (the primary metric shown in the UI)
    situation_label      VARCHAR,     -- Aligned / Divergent / Shared lens, split mood / Same verdict, different reasons
    computed_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.pre_launch_risk_scores (
    plcs_id             VARCHAR PRIMARY KEY,
    requested_by        VARCHAR,
    draft_content       VARCHAR,
    source_language     VARCHAR(8),
    target_market       VARCHAR(8),
    plcs_score          INTEGER,
    plcs_confidence     FLOAT,
    top_frames          ARRAY,
    nearest_analogs     ARRAY,
    risk_narrative      VARCHAR,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inputs_json         VARIANT,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.cultural_translator_runs (
    run_id              VARCHAR PRIMARY KEY,
    requested_by        VARCHAR,
    source_content      VARCHAR,
    source_language     VARCHAR(8),
    target_market       VARCHAR(8),
    target_frame_hint   VARCHAR,
    adapted_variants    ARRAY,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.ai_briefs (
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

CREATE TABLE IF NOT EXISTS app_data.tracked_entities (
    entity_id           VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    entity_name         VARCHAR NOT NULL,
    entity_type         VARCHAR DEFAULT 'brand',
    owner_email         VARCHAR NOT NULL,
    languages           ARRAY,
    cds_threshold_delta FLOAT DEFAULT 0.10,   -- drift delta on the headline (frame_divergence) scale [ADR-0003]
    cds_threshold_abs   FLOAT DEFAULT 0.34,   -- = frame_div_risk
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS app_data.drift_events (
    drift_id     VARCHAR DEFAULT UUID_STRING() PRIMARY KEY,
    entity_id    VARCHAR,
    entity_name  VARCHAR,
    language_a   VARCHAR,
    language_b   VARCHAR,
    prev_cds     FLOAT,
    new_cds      FLOAT,
    delta_cds    FLOAT,
    detected_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    notified     BOOLEAN DEFAULT FALSE
);

-- Grant read+write on data to admins, read-only to users.
GRANT SELECT ON ALL TABLES IN SCHEMA app_data TO APPLICATION ROLE app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_data TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Reference callbacks for the bound consumer objects.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE app_instance.register_consumer_raw_data(
    ref_name STRING, operation STRING, ref_or_alias STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    rv STRING;
BEGIN
    IF (operation = 'ADD') THEN
        SELECT SYSTEM$SET_REFERENCE(:ref_name, :ref_or_alias) INTO :rv;
    ELSEIF (operation = 'REMOVE') THEN
        SELECT SYSTEM$REMOVE_REFERENCE(:ref_name) INTO :rv;
    ELSEIF (operation = 'CLEAR') THEN
        SELECT SYSTEM$REMOVE_REFERENCE(:ref_name) INTO :rv;
    ELSE
        RETURN 'unknown operation';
    END IF;
    RETURN 'OK';
END;
$$;

CREATE OR REPLACE PROCEDURE app_instance.config_consumer_raw_data(ref_name STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    RETURN OBJECT_CONSTRUCT(
        'type', 'CONFIGURATION',
        'payload', OBJECT_CONSTRUCT(
            'host_ports', ARRAY_CONSTRUCT(),
            'allowed_secrets', 'NONE'
        )
    )::STRING;
END;
$$;

CREATE OR REPLACE PROCEDURE app_instance.register_consumer_notification(
    ref_name STRING, operation STRING, ref_or_alias STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    rv STRING;
BEGIN
    IF (operation = 'ADD') THEN
        SELECT SYSTEM$SET_REFERENCE(:ref_name, :ref_or_alias) INTO :rv;
    ELSEIF (operation = 'REMOVE') THEN
        SELECT SYSTEM$REMOVE_REFERENCE(:ref_name) INTO :rv;
    ELSEIF (operation = 'CLEAR') THEN
        SELECT SYSTEM$REMOVE_REFERENCE(:ref_name) INTO :rv;
    ELSE
        RETURN 'unknown operation';
    END IF;
    RETURN 'OK';
END;
$$;

GRANT USAGE ON PROCEDURE app_instance.register_consumer_raw_data(STRING, STRING, STRING)
    TO APPLICATION ROLE app_admin;
GRANT USAGE ON PROCEDURE app_instance.config_consumer_raw_data(STRING)
    TO APPLICATION ROLE app_admin;
GRANT USAGE ON PROCEDURE app_instance.register_consumer_notification(STRING, STRING, STRING)
    TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Streamlit
-- ---------------------------------------------------------------------------
CREATE STREAMLIT IF NOT EXISTS app_instance.nuance_app
    FROM '/streamlit'
    MAIN_FILE = 'nuance_app.py';

GRANT USAGE ON STREAMLIT app_instance.nuance_app TO APPLICATION ROLE app_user;
GRANT USAGE ON STREAMLIT app_instance.nuance_app TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Note: PLCS, Cultural Translator, AI Brief, and Find Analogs stored procedures
-- should be packaged here too. For brevity, those are in companion files that
-- the publisher should include in this setup script before submitting to
-- Marketplace. See `snowpark/deploy_plcs.py` etc. for the procedure bodies —
-- adapt the function definitions into pure SQL CREATE PROCEDURE statements,
-- or use Snowpark Python sproc files staged with the app.
-- ---------------------------------------------------------------------------
