-- =============================================================================
-- Project Nuance — Native App setup_script
-- =============================================================================
-- Runs inside the consumer's Snowflake account when they install Comprenda from
-- Marketplace. Creates the app's schemas, tables, procedures, and Streamlit.
--
-- Idempotent AND upgrade-safe: this script re-runs on every version upgrade
-- against the consumer's EXISTING app, so it must never destroy consumer data or
-- config. Use CREATE ... IF NOT EXISTS / CREATE OR ALTER for anything that holds
-- consumer state; never CREATE OR REPLACE a table whose rows the consumer owns.
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
-- app_user needs schema USAGE too, or the in-app Streamlit can't read app_data
-- tables (SELECT on the tables alone is insufficient without schema USAGE).
GRANT USAGE ON SCHEMA app_data TO APPLICATION ROLE app_user;

-- ---------------------------------------------------------------------------
-- Application config table (copied from the dev bootstrap).
-- IF NOT EXISTS (not CREATE OR REPLACE): on a version upgrade this preserves any
-- values the consumer has tuned. The MERGE below seeds defaults for missing keys
-- only (INSERT WHEN NOT MATCHED, deliberately no UPDATE) so re-runs never clobber
-- consumer edits.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_data.config (
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

-- Raw corpus (the demo ships a synthetic slice; columns mirror the bundled
-- social_posts.parquet — see native_app/export_demo_data.py).
CREATE TABLE IF NOT EXISTS app_data.social_posts (
    post_id           VARCHAR PRIMARY KEY,
    post_text         VARCHAR,
    detected_language VARCHAR(8),
    source_platform   VARCHAR,
    post_timestamp    TIMESTAMP_NTZ,
    event_tag         VARCHAR,
    country_hint      VARCHAR(8),
    ingested_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Curated historical analog library (the Analog Retrieval moat). The `embedding`
-- column is kept nullable so the find_analogs cosine fallback still compiles, but
-- it is NOT bundled — the analog Cortex Search service indexes `description`.
CREATE TABLE IF NOT EXISTS app_data.analog_corpus (
    analog_id        VARCHAR PRIMARY KEY,
    case_name        VARCHAR,
    company          VARCHAR,
    year             INTEGER,
    description      VARCHAR,
    affected_markets ARRAY,
    failure_frames   ARRAY,
    outcome_summary  VARCHAR,
    source_url       VARCHAR,
    embedding        VECTOR(FLOAT, 1024),
    embedded_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Frame taxonomy (the 12 cultural frames). Static seed, MERGEd below.
CREATE TABLE IF NOT EXISTS app_data.frame_taxonomy (
    frame_name      VARCHAR PRIMARY KEY,
    description     VARCHAR,
    example_phrases ARRAY,
    hofstede_dim    VARCHAR
);

MERGE INTO app_data.frame_taxonomy t
USING (
    SELECT 'individualist' AS frame_name,
           'Emphasizes personal autonomy, individual rights, self-expression' AS description,
           ARRAY_CONSTRUCT('my choice','live your truth','be yourself') AS example_phrases,
           'individualism' AS hofstede_dim
    UNION ALL SELECT 'collectivist',
           'Emphasizes group harmony, family/community obligations, shared identity',
           ARRAY_CONSTRUCT('our community','for the family','together we'), 'individualism'
    UNION ALL SELECT 'nationalist',
           'Invokes national pride, in-group preference, cultural sovereignty',
           ARRAY_CONSTRUCT('our country','national pride','foreign interference'), 'in_group_loyalty'
    UNION ALL SELECT 'globalist',
           'Embraces cross-cultural exchange, international cooperation, cosmopolitanism',
           ARRAY_CONSTRUCT('global citizen','one world','cross-border'), 'in_group_loyalty'
    UNION ALL SELECT 'threat_framing',
           'Frames event as danger, loss, or vulnerability',
           ARRAY_CONSTRUCT('we must protect','at risk','under attack'), 'uncertainty_avoidance'
    UNION ALL SELECT 'opportunity_framing',
           'Frames event as benefit, growth, or possibility',
           ARRAY_CONSTRUCT('great opportunity','chance to grow','exciting future'), 'uncertainty_avoidance'
    UNION ALL SELECT 'historical_grievance',
           'Invokes past wrongs, colonial memory, ethnic or political grievance',
           ARRAY_CONSTRUCT('never forget','they always','since history'), 'long_term_orientation'
    UNION ALL SELECT 'status_quo',
           'Supports preservation of current order, tradition, established norms',
           ARRAY_CONSTRUCT('the way things should be','traditional values','dont change'), 'long_term_orientation'
    UNION ALL SELECT 'reform_seeking',
           'Calls for change, progress, structural improvement',
           ARRAY_CONSTRUCT('we need to change','time for reform','better future'), 'long_term_orientation'
    UNION ALL SELECT 'spiritual_ethical',
           'Frames event in moral, religious, or ethical terms',
           ARRAY_CONSTRUCT('its wrong','moral obligation','spiritual meaning'), 'indulgence'
    UNION ALL SELECT 'pragmatic',
           'Focuses on practical outcomes, efficiency, results',
           ARRAY_CONSTRUCT('lets get it done','whatever works','show me results'), 'indulgence'
    UNION ALL SELECT 'ambiguous',
           'No clear frame detectable; mixed or unclear signaling',
           ARRAY_CONSTRUCT(), NULL
) s
ON t.frame_name = s.frame_name
WHEN NOT MATCHED THEN
    INSERT (frame_name, description, example_phrases, hofstede_dim)
    VALUES (s.frame_name, s.description, s.example_phrases, s.hofstede_dim);

-- Grant read+write on data to admins, read-only to users.
GRANT SELECT ON ALL TABLES IN SCHEMA app_data TO APPLICATION ROLE app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_data TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Compute UDF: cosine distance between two 1024-dim vectors. Used by the
-- find_analogs / PLCS cosine fallbacks (and the Phase-2 CDS recompute). Ported
-- from snowpark/deploy.py. VECTOR_AVG (UDAF) is deferred to Phase 2 with the
-- enrichment pipeline — it isn't exercised by the bundled-data read path.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app_instance.cosine_distance(a VECTOR(FLOAT, 1024), b VECTOR(FLOAT, 1024))
RETURNS FLOAT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'cosine_distance'
AS $$
def cosine_distance(a, b):
    if a is None or b is None or len(a) == 0 or len(b) == 0:
        return None
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return None
    cs = dot / ((na ** 0.5) * (nb ** 0.5))
    cs = max(-1.0, min(1.0, cs))
    return 1.0 - cs
$$;
GRANT USAGE ON FUNCTION app_instance.cosine_distance(VECTOR(FLOAT, 1024), VECTOR(FLOAT, 1024))
    TO APPLICATION ROLE app_user;
GRANT USAGE ON FUNCTION app_instance.cosine_distance(VECTOR(FLOAT, 1024), VECTOR(FLOAT, 1024))
    TO APPLICATION ROLE app_admin;

-- ===========================================================================
-- Cortex stored procedures (the 4 hero features). Ported inline from
-- snowpark/deploy_*.py, re-targeted NUANCE_DB.* -> app_data.* / app_instance.*.
-- All run EXECUTE AS OWNER (required for native-app procedures); they call
-- SNOWFLAKE.CORTEX.* at runtime, so the consumer must grant the application
-- access to Cortex first (see README / provision_app below).
-- The two Cortex Search service names are built per-consumer from
-- CURRENT_DATABASE() (the installed app's database name varies).
-- ===========================================================================

-- --- Pre-Launch Cultural Risk Score (PLCS) ---------------------------------
CREATE OR REPLACE PROCEDURE app_instance.score_content(
    draft_content STRING, source_language STRING, target_market STRING, requested_by STRING
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'score_content'
EXECUTE AS OWNER
AS $$
import json
import uuid
from collections import Counter

def score_content(session, draft_content, source_language, target_market, requested_by=None):
    PROMPT_VERSION = "plcs-v1"

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM app_data.config"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")
    embedding_model = cfg.get("embedding_model", "snowflake-arctic-embed-l-v2.0")

    truncated = (draft_content or "")[:8000]

    db = session.sql("SELECT CURRENT_DATABASE() AS DB").collect()[0]["DB"]
    post_search = f"{db}.APP_DATA.COMPRENDA_POST_SEARCH"

    # Cortex Search over the enriched corpus filtered by target-market language.
    # Falls back to UDF cosine with a server-side embed if the service is absent.
    neighbors = []
    try:
        search_query = {
            "query": truncated[:1000],
            "columns": [
                "post_id", "post_text", "cultural_frame",
                "emotional_tone", "sentiment_score", "frame_confidence",
                "detected_language",
            ],
            "filter": {"@eq": {"detected_language": target_market}},
            "limit": 15,
        }
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(?, ?) AS r",
            params=[post_search, json.dumps(search_query)],
        ).collect()
        raw = result[0]["R"] if result else None
        parsed = json.loads(raw) if isinstance(raw, str) else (raw or {})
        neighbors = parsed.get("results", []) if isinstance(parsed, dict) else []
    except Exception:
        # CRITICAL: do NOT bind a Python list as a VECTOR param. Inline the
        # EMBED_TEXT_1024(?, ?) so the VECTOR is constructed server-side.
        rows = session.sql(
            "SELECT cf.post_id, cf.cultural_frame, cf.sentiment_score, "
            "       cf.emotional_tone, cf.frame_confidence, "
            "       app_instance.COSINE_DISTANCE("
            "           pe.embedding, "
            "           SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?)"
            "       ) AS dist "
            "FROM app_data.post_embeddings pe "
            "JOIN app_data.cultural_frames cf USING (post_id) "
            "WHERE cf.detected_language = ? "
            "ORDER BY dist ASC LIMIT 15",
            params=[embedding_model, truncated, target_market],
        ).collect()
        neighbors = [
            {
                "post_id": r["POST_ID"],
                "cultural_frame": r["CULTURAL_FRAME"],
                "sentiment_score": r["SENTIMENT_SCORE"],
                "emotional_tone": r["EMOTIONAL_TONE"],
                "frame_confidence": r["FRAME_CONFIDENCE"],
                "dist": r["DIST"],
            }
            for r in rows
        ]

    if not neighbors:
        plcs_score = 50
        plcs_confidence = 0.1
        top_frames = ["ambiguous"]
        nearest_post_ids = []
        risk_narrative = (
            "Insufficient historical data in target market to score with confidence. "
            "Recommend manual review by a market-native reviewer."
        )
    else:
        frame_counts = Counter(
            (n.get("cultural_frame") or "ambiguous") for n in neighbors
        )
        top_frames = [f for f, _ in frame_counts.most_common(3)]
        nearest_post_ids = [n.get("post_id") for n in neighbors if n.get("post_id")]

        def _safe_float(x, default=0.0):
            try:
                return float(x) if x is not None else default
            except (TypeError, ValueError):
                return default
        neg = sum(
            1 for n in neighbors
            if _safe_float(n.get("sentiment_score"), 0.0) < -0.2
        )
        pct_neg = round(100.0 * neg / len(neighbors))

        synth_prompt = (
            "You are a cultural intelligence analyst evaluating cultural risk of a "
            f"marketing draft for the target market with language code \"{target_market}\".\n\n"
            f"DRAFT CONTENT (source language {source_language}):\n"
            f"\"\"\"\n{draft_content[:1500]}\n\"\"\"\n\n"
            f"HISTORICAL ANALOG DATA (top frames in {target_market} similar content): "
            f"{', '.join(top_frames)}.\n"
            f"Proportion of similar historical content with negative sentiment: {pct_neg}%.\n\n"
            "Score cultural risk on a 0-100 scale (higher = more risk). Consider:\n"
            "- Frame mismatch between draft intent and dominant frames in target market\n"
            "- Historical sentiment of similar content\n"
            "- Common cultural pitfalls (religion, history, in-group/out-group cues)\n\n"
            "Return JSON ONLY with no other text:\n"
            "{\"plcs\":<integer_0_100>,\"confidence\":<float_0_1>,"
            "\"narrative\":\"<one paragraph under 150 words explaining the score "
            "and citing which frames matter>\"}"
        )

        resp_rows = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
            params=[model_large, synth_prompt],
        ).collect()
        raw = resp_rows[0]["R"] if resp_rows else ""

        plcs_score = 50
        plcs_confidence = 0.5
        risk_narrative = raw
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
            plcs_score = int(parsed.get("plcs", 50))
            plcs_confidence = float(parsed.get("confidence", 0.5))
            risk_narrative = str(parsed.get("narrative", raw))
        except Exception:
            import re
            m = re.search(r'"plcs"\s*:\s*(\d+)', raw)
            if m:
                plcs_score = int(m.group(1))
            m = re.search(r'"confidence"\s*:\s*([0-9.]+)', raw)
            if m:
                plcs_confidence = float(m.group(1))

        plcs_score = max(0, min(100, plcs_score))
        plcs_confidence = max(0.0, min(1.0, plcs_confidence))

    plcs_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO app_data.pre_launch_risk_scores ("
        "  plcs_id, requested_by, draft_content, source_language, target_market,"
        "  plcs_score, plcs_confidence, top_frames, nearest_analogs,"
        "  risk_narrative, model_used, prompt_version, inputs_json"
        ") SELECT ?,?,?,?,?,?,?, PARSE_JSON(?), PARSE_JSON(?),?,?,?, PARSE_JSON(?)",
        params=[
            plcs_id, requested_by, draft_content, source_language, target_market,
            plcs_score, plcs_confidence,
            json.dumps(top_frames),
            json.dumps(nearest_post_ids),
            risk_narrative, model_large, PROMPT_VERSION,
            json.dumps({"source_language": source_language,
                        "target_market": target_market,
                        "n_neighbors": len(neighbors)}),
        ],
    ).collect()

    return {
        "plcs_id": plcs_id,
        "plcs_score": plcs_score,
        "confidence": plcs_confidence,
        "top_frames": top_frames,
        "nearest_analogs": nearest_post_ids,
        "risk_narrative": risk_narrative,
        "target_market": target_market,
        "model": model_large,
    }
$$;

-- --- Cultural Translator ----------------------------------------------------
CREATE OR REPLACE PROCEDURE app_instance.translate_culture(
    source_content STRING, source_language STRING, target_market STRING,
    target_frame_hint STRING, requested_by STRING
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'translate_culture'
EXECUTE AS OWNER
AS $$
import json
import uuid

def translate_culture(session, source_content, source_language, target_market,
                      target_frame_hint=None, requested_by=None):
    PROMPT_VERSION = "translator-v1"

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM app_data.config"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")

    if not target_frame_hint:
        row = session.sql(
            "SELECT cultural_frame, COUNT(*) AS n "
            "FROM app_data.cultural_frames "
            "WHERE detected_language = ? "
            "  AND cultural_frame != 'ambiguous' "
            "GROUP BY cultural_frame ORDER BY n DESC LIMIT 1",
            params=[target_market],
        ).collect()
        target_frame_hint = row[0]["CULTURAL_FRAME"] if row else "pragmatic"

    prompt = (
        "You are a cross-cultural content adaptation specialist. Given source "
        "marketing content, produce 3 culturally-adapted variants for the target "
        "market that preserve INTENT but shift the cultural FRAME appropriately.\n\n"
        f"SOURCE LANGUAGE: {source_language}\n"
        f"TARGET MARKET LANGUAGE: {target_market}\n"
        f"TARGET DOMINANT FRAME: {target_frame_hint}\n\n"
        "SOURCE CONTENT:\n"
        f"\"\"\"\n{source_content[:2000]}\n\"\"\"\n\n"
        "Produce 3 variants. Each should be WRITTEN IN THE TARGET MARKET LANGUAGE, "
        "be the same approximate length as the source, and preserve the underlying "
        "marketing intent. Vary the frame approach across the 3 variants.\n\n"
        "Return JSON ONLY with no other text:\n"
        "{\"variants\":["
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"},"
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"},"
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"}"
        "]}"
    )

    raw_rows = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
        params=[model_large, prompt],
    ).collect()
    raw = raw_rows[0]["R"] if raw_rows else ""

    variants = []
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0]
        parsed = json.loads(cleaned)
        variants = parsed.get("variants", []) if isinstance(parsed, dict) else []
    except Exception:
        variants = [{
            "text": raw,
            "frame_shift": target_frame_hint or "unknown",
            "rationale": "Auto-fallback: model output did not parse as JSON.",
        }]

    run_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO app_data.cultural_translator_runs ("
        "  run_id, requested_by, source_content, source_language, target_market,"
        "  target_frame_hint, adapted_variants, model_used, prompt_version"
        ") SELECT ?,?,?,?,?,?,PARSE_JSON(?),?,?",
        params=[
            run_id, requested_by, source_content, source_language, target_market,
            target_frame_hint, json.dumps(variants), model_large, PROMPT_VERSION,
        ],
    ).collect()

    return {
        "run_id": run_id,
        "source_content": source_content,
        "target_market": target_market,
        "target_frame_hint": target_frame_hint,
        "variants": variants,
        "model": model_large,
    }
$$;

-- --- AI Cultural Brief Generator -------------------------------------------
CREATE OR REPLACE PROCEDURE app_instance.generate_brief(
    event_tag STRING, target_languages VARIANT, requested_by STRING
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'generate_brief'
EXECUTE AS OWNER
AS $$
import json
import uuid

def generate_brief(session, event_tag, target_languages, requested_by=None):
    BRIEF_PROMPT_VERSION = "ai-brief-v3"

    # target_languages may arrive as a Python list (VARIANT) or a JSON string.
    if isinstance(target_languages, str):
        try:
            target_languages = json.loads(target_languages)
        except Exception:
            target_languages = [target_languages]
    if not isinstance(target_languages, list):
        target_languages = list(target_languages or [])

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM app_data.config"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")

    if not target_languages:
        rows = session.sql(
            "SELECT detected_language FROM app_data.cultural_frames "
            "WHERE event_tag = ? "
            "GROUP BY detected_language HAVING COUNT(*) >= 10",
            params=[event_tag],
        ).collect()
        target_languages = [r["DETECTED_LANGUAGE"] for r in rows]

    if not target_languages:
        raise ValueError(f"No language has >=10 posts for event_tag={event_tag}")

    cds_rows = session.sql(
        "SELECT language_a, language_b, frame_divergence, sentiment_divergence, "
        "       topical_overlap, situation_label, cds_confidence "
        "FROM app_data.cultural_divergence_scores "
        "WHERE event_tag = ? AND frame_divergence IS NOT NULL "
        "  AND (language_a IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "       OR language_b IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?))))) "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY language_a, language_b "
        "                           ORDER BY computed_at DESC) = 1 "
        "ORDER BY frame_divergence DESC",
        params=[event_tag, json.dumps(target_languages), json.dumps(target_languages)],
    ).collect()
    cds_summary = [
        {
            "lang_a": r["LANGUAGE_A"], "lang_b": r["LANGUAGE_B"],
            "situation": r["SITUATION_LABEL"],
            "frame_divergence": round(float(r["FRAME_DIVERGENCE"]), 3),
            "sentiment_divergence": round(float(r["SENTIMENT_DIVERGENCE"]), 3),
            "topical_overlap": round(float(r["TOPICAL_OVERLAP"]), 3),
            "sample_sufficiency": round(float(r["CDS_CONFIDENCE"]), 2),
        }
        for r in cds_rows[:15]
    ]

    frame_rows = session.sql(
        "SELECT detected_language, cultural_frame, COUNT(*) AS n "
        "FROM app_data.cultural_frames "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "GROUP BY detected_language, cultural_frame "
        "ORDER BY detected_language, n DESC",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()
    frames_by_lang = {}
    for r in frame_rows:
        frames_by_lang.setdefault(r["DETECTED_LANGUAGE"], []).append({
            "frame": r["CULTURAL_FRAME"], "count": int(r["N"])
        })

    sent_rows = session.sql(
        "SELECT detected_language, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
        "FROM app_data.cultural_frames "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "GROUP BY detected_language",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()
    sentiment_by_lang = {
        r["DETECTED_LANGUAGE"]: {
            "avg_sentiment": round(float(r["AVG_SENT"]), 3),
            "n": int(r["N"]),
        }
        for r in sent_rows
    }

    sample_rows = session.sql(
        "SELECT post_id, detected_language FROM app_data.cultural_frames "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "  AND frame_confidence > 0.7 "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY detected_language ORDER BY frame_confidence DESC) <= 3",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()
    sample_post_ids = [r["POST_ID"] for r in sample_rows]

    summary_payload = json.dumps({
        "event_tag": event_tag,
        "target_languages": target_languages,
        "cds_top_pairs": cds_summary,
        "frames_by_language": frames_by_lang,
        "sentiment_by_language": sentiment_by_lang,
    }, indent=2).replace("'", "''")

    prompt = (
        "You are a senior cultural intelligence analyst writing a 2-page Cultural "
        "Intelligence Brief for a marketing executive. The data below summarizes how "
        f"the event \"{event_tag}\" was discussed across language communities.\n\n"
        f"DATA:\n{summary_payload}\n\n"
        "Divergence is measured on three axes per language pair: topical_overlap "
        "(how much they discuss the same thing — high across the board), "
        "frame_divergence (how differently they frame it — the headline signal), and "
        "sentiment_divergence (how differently they feel). 'situation' summarizes the "
        "pair: Aligned / Divergent / 'Shared lens, split mood' / "
        "'Same verdict, different reasons'. Each pair also carries sample_sufficiency in "
        "[0,1] — a normalized function of how many posts back that pair (data volume), "
        "NOT a statistical confidence measure. Treat it as how much data supports the "
        "reading; never describe it as statistical confidence or certainty.\n\n"
        "Write the brief in Markdown with exactly these sections:\n"
        "1. **Executive Summary** (2-3 sentences)\n"
        "2. **Key Cultural Divergences** (table: language pair, situation, frame "
        "divergence, sentiment divergence, interpretation). Topical overlap is high "
        "everywhere — focus on how framing and sentiment differ, not whether they "
        "discuss the same event.\n"
        "3. **Dominant Frames by Region** (one line per language)\n"
        "4. **Risk Flags** (3-5 bullet points of specific cultural risks)\n"
        "5. **Messaging Recommendations** (one paragraph per target language)\n"
        "6. **Data & Sample-Size Notes** (one short paragraph on how much data backs "
        "these findings — sample-size adequacy, not statistical confidence)\n\n"
        "Be specific. Quote concrete frame combinations. Do not hedge excessively."
    )

    raw_rows = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
        params=[model_large, prompt],
    ).collect()
    brief_md = raw_rows[0]["R"] if raw_rows else "(no content)"

    brief_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO app_data.ai_briefs ("
        "  brief_id, requested_by, event_tag, target_languages,"
        "  brief_markdown, source_post_ids, model_used, prompt_version"
        ") SELECT ?,?,?,PARSE_JSON(?),?,PARSE_JSON(?),?,?",
        params=[
            brief_id, requested_by, event_tag, json.dumps(target_languages),
            brief_md, json.dumps(sample_post_ids), model_large, BRIEF_PROMPT_VERSION,
        ],
    ).collect()

    return {
        "brief_id": brief_id,
        "event_tag": event_tag,
        "target_languages": target_languages,
        "brief_markdown": brief_md,
        "source_post_ids": sample_post_ids,
        "model": model_large,
    }
$$;

-- --- Analog Retrieval -------------------------------------------------------
CREATE OR REPLACE PROCEDURE app_instance.find_analogs(
    query_text STRING, target_market STRING, k INTEGER
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'find_analogs'
EXECUTE AS OWNER
AS $$
import json

def find_analogs(session, query_text, target_market=None, k=5):
    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM app_data.config"
        ).collect()
    }
    embedding_model = cfg.get("embedding_model", "snowflake-arctic-embed-l-v2.0")

    db = session.sql("SELECT CURRENT_DATABASE() AS DB").collect()[0]["DB"]
    analog_search = f"{db}.APP_DATA.COMPRENDA_ANALOG_SEARCH"

    analogs = []
    try:
        search_query = {
            "query": query_text[:1000],
            "columns": [
                "analog_id", "case_name", "company", "year",
                "description", "affected_markets", "failure_frames",
                "outcome_summary",
            ],
            "limit": k,
        }
        if target_market:
            search_query["filter"] = {
                "@contains": {"affected_markets": target_market}
            }
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(?, ?) AS r",
            params=[analog_search, json.dumps(search_query)],
        ).collect()
        parsed = json.loads(result[0]["R"]) if result else {}
        analogs = parsed.get("results", []) if isinstance(parsed, dict) else []
    except Exception:
        rows = session.sql(
            "WITH q AS (SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?) AS e) "
            "SELECT analog_id, case_name, company, year, description, "
            "       affected_markets, failure_frames, outcome_summary, "
            "       app_instance.COSINE_DISTANCE(embedding, (SELECT e FROM q)) AS dist "
            "FROM app_data.analog_corpus "
            "ORDER BY dist ASC LIMIT ?",
            params=[embedding_model, query_text[:8000], k],
        ).collect()
        analogs = [
            {
                "analog_id": r["ANALOG_ID"],
                "case_name": r["CASE_NAME"],
                "company": r["COMPANY"],
                "year": r["YEAR"],
                "description": r["DESCRIPTION"],
                "affected_markets": r["AFFECTED_MARKETS"],
                "failure_frames": r["FAILURE_FRAMES"],
                "outcome_summary": r["OUTCOME_SUMMARY"],
                "distance": float(r["DIST"]) if r["DIST"] is not None else None,
            }
            for r in rows
        ]

    return {
        "query": query_text,
        "target_market": target_market,
        "analogs": analogs,
        "count": len(analogs),
    }
$$;

GRANT USAGE ON PROCEDURE app_instance.score_content(STRING, STRING, STRING, STRING)
    TO APPLICATION ROLE app_user;
GRANT USAGE ON PROCEDURE app_instance.score_content(STRING, STRING, STRING, STRING)
    TO APPLICATION ROLE app_admin;
GRANT USAGE ON PROCEDURE app_instance.translate_culture(STRING, STRING, STRING, STRING, STRING)
    TO APPLICATION ROLE app_user;
GRANT USAGE ON PROCEDURE app_instance.translate_culture(STRING, STRING, STRING, STRING, STRING)
    TO APPLICATION ROLE app_admin;
GRANT USAGE ON PROCEDURE app_instance.generate_brief(STRING, VARIANT, STRING)
    TO APPLICATION ROLE app_user;
GRANT USAGE ON PROCEDURE app_instance.generate_brief(STRING, VARIANT, STRING)
    TO APPLICATION ROLE app_admin;
GRANT USAGE ON PROCEDURE app_instance.find_analogs(STRING, STRING, INTEGER)
    TO APPLICATION ROLE app_user;
GRANT USAGE ON PROCEDURE app_instance.find_analogs(STRING, STRING, INTEGER)
    TO APPLICATION ROLE app_admin;

-- ===========================================================================
-- Provisioning procedure (run ONCE by the consumer after install).
-- ---------------------------------------------------------------------------
-- A native-app setup script runs WITHOUT a warehouse, and both COPY INTO and
-- CREATE CORTEX SEARCH SERVICE require compute — so the bundled-data load and
-- the two Cortex Search services cannot run in the setup body. They live here,
-- in a procedure the consumer calls after granting the app a warehouse + Cortex
-- access (see native_app/README.md):
--     GRANT CREATE WAREHOUSE ON ACCOUNT TO APPLICATION <app>;
--     GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO APPLICATION <app>;
--     CALL <app>.app_instance.provision_app();
-- Idempotent: COPY INTO skips already-loaded files; the analog seed clears +
-- reseeds; the search services are CREATE OR REPLACE.
-- NOTE: a stored proc cannot run USE WAREHOUSE, so the COPY INTO / seed run on the
-- CALLER's active warehouse — set one (USE WAREHOUSE <wh>) before CALLing. The
-- Cortex Search services refresh on comprenda_wh via their WAREHOUSE = clause.
-- ===========================================================================
CREATE OR REPLACE PROCEDURE app_instance.provision_app()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
BEGIN
    -- 1. Dedicated XS warehouse the Cortex Search services refresh on (referenced
    --    by their WAREHOUSE = clause below; that needs no USE statement). A stored
    --    procedure cannot run USE WAREHOUSE, so the COPY INTO / seed steps run on
    --    the CALLER's active warehouse — the consumer sets one before CALLing this.
    CREATE WAREHOUSE IF NOT EXISTS comprenda_wh
        WAREHOUSE_SIZE = 'XSMALL'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
        INITIALLY_SUSPENDED = TRUE;

    -- 2. Load the bundled synthetic corpus from the application package
    --    (runs on the caller's warehouse).
    COPY INTO app_data.social_posts
        FROM '/data/social_posts.parquet'
        FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
    COPY INTO app_data.cultural_frames
        FROM '/data/cultural_frames.parquet'
        FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
    COPY INTO app_data.cultural_divergence_scores
        FROM '/data/cultural_divergence_scores.parquet'
        FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

    -- 3. Seed the static analog library (39 curated cases; no embeddings — the
    --    analog Cortex Search service indexes `description`). Inlined from
    --    native_app/scripts/seed_analog_corpus.sql (source of truth:
    --    data/seed_analog_library.py; regenerate with scripts/_gen_analog_seed.py).
    --    Inlined rather than EXECUTE IMMEDIATE FROM '/scripts/...' because
    --    `snow app validate` statically resolves file refs inside proc bodies.
    DELETE FROM app_data.analog_corpus;
    INSERT INTO app_data.analog_corpus
        (analog_id, case_name, company, year, description,
         affected_markets, failure_frames, outcome_summary, source_url)
    SELECT column1, column2, column3, column4, column5,
           PARSE_JSON(column6), PARSE_JSON(column7), column8, column9
    FROM VALUES
        ('analog_001', 'HSBC Assume Nothing → Do Nothing', 'HSBC', 2009, 'HSBC''s global ''Assume Nothing'' campaign translated into multiple markets as ''Do Nothing,'' implying inaction. The brand spent $10M rebranding to ''The world''s local bank'' to repair the damage.', '["zh", "ja", "ko", "es", "pt", "ar"]', '["pragmatic", "ambiguous"]', '$10M global rebrand; brand-trust impact in non-English markets for 18+ months.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_002', 'Mercedes Bensi → ''Rush to Die''', 'Mercedes-Benz', 1990, 'Mercedes-Benz entered China as ''Bensi,'' which read homophonically as ''rush to die.'' The brand quickly switched to ''Benchi'' (meaning ''dashing speed''). Early sales were materially affected.', '["zh"]', '["nationalist", "spiritual_ethical", "status_quo"]', 'Localized name change; Chinese launch delayed and re-budgeted.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_003', 'Pepsi ''Come Alive'' → ''Bring Ancestors Back''', 'Pepsi', 1960, 'Pepsi''s ''Come alive with the Pepsi Generation'' translated in Chinese as ''Pepsi brings your ancestors back from the dead.'' Spiritual-frame violation in market with strong ancestor veneration.', '["zh"]', '["spiritual_ethical", "historical_grievance"]', 'Campaign pulled in market; case-study staple for 60+ years.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_004', 'Parker Pen ''Embarrass'' Translation', 'Parker Pen', 1994, 'Parker''s ''It won''t leak in your pocket and embarrass you'' translated into Spanish using ''embarazar,'' which means ''to impregnate.'' The ad ran as ''It won''t leak in your pocket and impregnate you.''', '["es"]', '["pragmatic", "ambiguous"]', 'Brand mockery in Spanish-speaking markets for years.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_005', 'Coors ''Turn It Loose'' → ''Suffer from Diarrhea''', 'Coors', 1980, 'Coors'' ''Turn it loose'' slogan, when translated to Spanish, read as ''suffer from diarrhea.'' Material brand reputation damage.', '["es"]', '["pragmatic"]', 'Spanish-market entry delayed; campaign re-shot.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_006', 'KFC ''Finger-Lickin'' Good'' → ''Eat Your Fingers Off''', 'KFC', 1987, 'KFC''s signature slogan translated in Chinese as ''Eat your fingers off.'' Threat-framing violation in market that prizes pragmatism.', '["zh"]', '["threat_framing", "ambiguous"]', 'Slogan dropped in market; alternative wording used.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_007', 'Ford Pinto Name in Brazil', 'Ford', 1971, 'Ford launched the Pinto in Brazil; ''pinto'' is Brazilian-Portuguese slang for small male genitals. Sales were a fraction of forecast.', '["pt"]', '["pragmatic", "ambiguous"]', 'Renamed to ''Corcel'' in Brazil; sales recovered.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_008', 'Electrolux ''Nothing Sucks Like an Electrolux''', 'Electrolux', 1960, 'Swedish brand''s English campaign ''Nothing sucks like an Electrolux'' succeeded in UK but became meme-fodder in US English markets.', '["en"]', '["pragmatic", "ambiguous"]', 'Brand survived; campaign quietly retired in US.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_009', 'American Airlines ''Fly in Leather'' → ''Fly Naked''', 'American Airlines', 1990, 'AA''s ''Fly in leather'' translated to Mexican Spanish as ''Fly naked'' (''Vuela en cuero'' is colloquial for nudity). Premium-cabin positioning undermined in entire Mexican market.', '["es"]', '["pragmatic"]', 'Premium ad budget rewritten for Mexican market.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_010', 'Got Milk? in Mexico', 'California Milk Processor Board', 1993, '''Got Milk?'' translated literally into Spanish as ''¿Tienes leche?'' which read in Mexico as ''Are you lactating?'' Maternal-frame collision with brand intent.', '["es"]', '["spiritual_ethical", "pragmatic"]', 'Replaced with ''Familia, Amor y Leche'' in Mexican market.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_011', 'Dolce & Gabbana China Chopsticks Ad', 'Dolce & Gabbana', 2018, 'D&G aired a campaign showing Chinese model awkwardly eating pizza with chopsticks. Read in Chinese market as nationalist insult; leaked DMs from designer compounded historical-grievance frame.', '["zh"]', '["nationalist", "historical_grievance"]', 'Shanghai show canceled; estimated $500M+ China revenue impact over 2 years.', 'https://www.bbc.com/news/world-asia-china-46307889'),
        ('analog_012', 'Tropicana Redesign 2009', 'Tropicana', 2009, 'Tropicana''s $35M packaging redesign abandoned the iconic orange-with-straw imagery. Sales fell 20% in 2 months. Status-quo frame violation.', '["en"]', '["status_quo", "threat_framing"]', 'Reverted within 60 days; $35M+ lost.', 'https://en.wikipedia.org/wiki/Tropicana_Products'),
        ('analog_013', 'Gap Logo Redesign 2010', 'Gap', 2010, 'Gap replaced its iconic blue-box logo with a flat sans-serif. Twitter and design press revolt. Pulled within 6 days.', '["en"]', '["status_quo", "individualist"]', 'Reverted in 6 days; estimated $100M brand-equity hit.', 'https://en.wikipedia.org/wiki/Gap_Inc.'),
        ('analog_014', 'Pepsi Kendall Jenner Protest Ad', 'Pepsi', 2017, 'Pepsi ad showed Kendall Jenner ending a protest by handing a police officer a Pepsi. Read as trivializing Black Lives Matter — historical-grievance and threat-framing simultaneously.', '["en"]', '["historical_grievance", "threat_framing"]', 'Pulled in 24 hours; CEO public apology.', 'https://en.wikipedia.org/wiki/Kendall_Jenner_Pepsi_advertisement'),
        ('analog_015', 'Burger King Vietnam Chopstick Ad', 'Burger King', 2019, 'BK New Zealand ad showed customers eating Whoppers with oversized chopsticks. Nationalist-frame violation in East Asian markets; circulated globally.', '["zh", "ja", "ko", "vi"]', '["nationalist", "historical_grievance"]', 'Pulled; BK NZ public apology.', 'https://www.bbc.com/news/world-asia-47832890'),
        ('analog_016', 'Heineken ''Sometimes Lighter Is Better''', 'Heineken', 2018, 'Heineken Light ad showed bartender sliding a beer past darker-skinned patrons to a lighter-skinned one with the tagline ''Sometimes lighter is better.'' Historical-grievance frame collision in US.', '["en"]', '["historical_grievance", "threat_framing"]', 'Pulled within 48 hours; public apology.', 'https://www.nytimes.com/2018/03/26/business/heineken-ad.html'),
        ('analog_017', 'Dove ''Real Beauty'' Soap Bar Ad', 'Dove', 2017, 'Dove Facebook ad showed Black woman removing brown shirt to reveal white woman, intended as ''all skin types'' message. Read as historical-grievance violation.', '["en"]', '["historical_grievance"]', 'Pulled; public apology.', 'https://www.theguardian.com/world/2017/oct/08/dove-pulls-ad-showing-black-woman-turning-into-white-one'),
        ('analog_018', 'H&M ''Coolest Monkey'' Hoodie', 'H&M', 2018, 'H&M product page featured Black child model wearing hoodie labeled ''Coolest monkey in the jungle.'' Historical-grievance violation.', '["en", "sv"]', '["historical_grievance"]', 'Product pulled; CEO public apology.', 'https://www.bbc.com/news/world-africa-42634194'),
        ('analog_019', 'Bud Light Dylan Mulvaney Partnership', 'Anheuser-Busch', 2023, 'Bud Light''s trans-influencer partnership triggered a multi-month boycott in US conservative markets. Status-quo and historical-grievance frames collided with brand''s pragmatic identity.', '["en"]', '["status_quo", "historical_grievance"]', '~$400M sales decline; market-share loss to Modelo.', 'https://en.wikipedia.org/wiki/Bud_Light_and_Dylan_Mulvaney'),
        ('analog_020', 'Balenciaga Holiday 2022 Campaign', 'Balenciaga', 2022, 'Balenciaga campaign featured children with BDSM-themed teddy bears and adjacent court-document props. Spiritual-ethical violation in every market simultaneously.', '["en", "ja", "zh", "de", "es", "fr"]', '["spiritual_ethical", "threat_framing"]', 'Campaign pulled; lawsuits filed; ~30% sales decline that quarter.', 'https://en.wikipedia.org/wiki/Balenciaga'),
        ('analog_021', 'Coca-Cola ''New Coke'' 1985', 'Coca-Cola', 1985, 'Coca-Cola replaced classic formula with ''New Coke.'' Status-quo violation triggered consumer revolt. Reformulated within 79 days.', '["en"]', '["status_quo"]', 'Reverted within 79 days; brand-trust narrative shifted for decade.', 'https://en.wikipedia.org/wiki/New_Coke'),
        ('analog_022', 'Toyota Prius Japan vs US Marketing Split', 'Toyota', 2010, 'Toyota''s Prius marketing emphasized collectivist ''family'' values in Japan, individualist ''eco-savvy choice'' in US. Same product, opposite frame. Successful divergent execution — exemplar case study.', '["en", "ja"]', '["individualist", "collectivist"]', 'Top-selling hybrid for 15 years; case study in deliberate cultural framing.', 'https://hbr.org/case-study/toyota'),
        ('analog_023', 'IKEA Furniture Naming in Thailand', 'IKEA', 2012, 'IKEA product names sounded similar to vulgar terms in Thai. Thai team rewrote naming for local market entry — pragmatic localization success.', '["th"]', '["pragmatic"]', 'Smooth market entry due to proactive linguistic vetting.', 'https://www.wsj.com/articles/SB10001424052702304470504577483254039762870'),
        ('analog_024', 'P&G ''Stork Delivering Babies'' in Japan', 'Procter & Gamble', 1985, 'P&G''s diaper ad showed a stork delivering babies. In Japan, stork mythology is about peach-borne babies. Cultural-narrative mismatch made ad confusing rather than offensive — sales muted.', '["ja"]', '["ambiguous", "spiritual_ethical"]', 'Ad replaced with Japanese-mythology-aligned imagery; sales recovered.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_025', 'Nike ''Air'' Logo Resembling ''Allah''', 'Nike', 1997, 'Nike Air-Bakin shoe ''Air'' flame-script logo resembled the Arabic word for ''Allah.'' Spiritual-ethical violation in MENA market.', '["ar"]', '["spiritual_ethical"]', '38,000 shoes recalled; logo redesigned.', 'https://www.washingtonpost.com/archive/sports/1997/06/25/nike-recalling-shoes-after-muslim-protest/'),
        ('analog_026', 'Burger King ''Texican'' Ad Spain', 'Burger King', 2009, 'BK Spanish ad showed tall American cowboy alongside short Mexican wrestler wearing US flag cape. Nationalist-frame and historical-grievance violations in Mexico simultaneously.', '["es"]', '["nationalist", "historical_grievance"]', 'Ad pulled; Mexican ambassador filed complaint.', 'https://www.theguardian.com/business/2009/may/18/burger-king-texican'),
        ('analog_027', 'Audi ''Vorsprung durch Technik'' Translation', 'Audi', 1990, 'Audi kept German tagline ''Vorsprung durch Technik'' in English markets rather than translating. Counterintuitively succeeded — pragmatic German identity reinforced brand. Case study in ''don''t translate.''', '["en"]', '["pragmatic", "nationalist"]', 'Tagline still in use 30+ years; brand-equity case study.', 'https://en.wikipedia.org/wiki/Vorsprung_durch_Technik'),
        ('analog_028', 'Levi''s 501 in India', 'Levi''s', 1995, 'Levi''s launched 501 with US individualist ''rebel'' messaging in India. Collectivist Indian market preferred family-celebration framing. Sales muted until campaign rewritten.', '["hi"]', '["individualist", "collectivist"]', 'Re-shot for family-frame in India; sales recovered.', 'https://hbr.org/2011/04/levis-tries-on-india'),
        ('analog_029', 'McDonald''s Hindu Beef Tallow Fries', 'McDonald''s', 2001, 'McDonald''s revealed its US fries were cooked in beef tallow despite vegetarian claims. Spiritual-ethical violation in Hindu Indian diaspora led to $10M lawsuit settlement.', '["hi", "en"]', '["spiritual_ethical"]', '$10M settlement; vegetarian-only India menu post-launch.', 'https://www.bbc.co.uk/news/world-south-asia-13473296'),
        ('analog_030', 'Walmart Germany Exit', 'Walmart', 2006, 'Walmart''s friendliness training (smiling at strangers, in-store chants) violated German cultural norms around workplace formality and personal space. Exited Germany after $1B loss.', '["de"]', '["pragmatic", "status_quo"]', '$1B loss; exit after 9 years; Harvard case study.', 'https://hbr.org/2006/12/why-walmart-failed-in-germany'),
        ('analog_031', 'Mattel Barbie in Saudi Arabia', 'Mattel', 2003, 'Saudi religious police banned Barbie dolls, calling them ''a threat to morality'' due to Western individualist femininity. Spiritual-ethical frame collision.', '["ar"]', '["spiritual_ethical", "status_quo"]', 'Banned 2003; Fulla doll dominated regional market.', 'https://www.cbsnews.com/news/saudi-arabia-bans-barbie-as-a-threat/'),
        ('analog_032', 'Disney Mulan 2020 Boycott China & US', 'Disney', 2020, 'Disney''s Mulan was boycotted in US for actress''s pro-HK-government comments and in China for being filmed near Xinjiang. Historical-grievance frame fired in opposite directions in two markets.', '["en", "zh"]', '["historical_grievance", "nationalist"]', '$200M production grossed $70M; one of Disney''s biggest losses of the decade.', 'https://en.wikipedia.org/wiki/Mulan_(2020_film)#Controversies'),
        ('analog_033', 'Nestlé Infant Formula Africa 1970s', 'Nestlé', 1977, 'Nestlé marketed infant formula in African markets with insufficient clean-water access, contributing to infant deaths. Spiritual-ethical violation triggered 7-year global boycott.', '["en", "fr", "ar", "sw"]', '["spiritual_ethical", "threat_framing"]', '7-year boycott; WHO marketing code (1981) directly attributable to case.', 'https://en.wikipedia.org/wiki/Nestl%C3%A9_boycott'),
        ('analog_034', 'Snapchat Chinese New Year Filter', 'Snap Inc.', 2016, 'Snapchat Chinese New Year filter narrowed eyes and made face yellow. Historical-grievance frame triggered in Chinese-American and Chinese markets simultaneously.', '["en", "zh"]', '["historical_grievance", "threat_framing"]', 'Filter pulled within 24 hours; public apology.', 'https://www.theguardian.com/technology/2016/aug/10/snapchat-anime-filter-yellowface'),
        ('analog_035', 'Renault Kangoo Naming in Spain', 'Renault', 1997, 'Renault Kangoo sold well in most markets but in Spain, ''Kangoo'' sounded similar to slang for awkward person. Sales soft until Spanish-specific positioning was added.', '["es"]', '["pragmatic"]', 'Spain-specific campaign launched; sales recovered.', 'https://www.gelato.com/blog/international-marketing-failures'),
        ('analog_036', 'Procter & Gamble ''Whisper'' Naming', 'Procter & Gamble', 1990, 'P&G launched feminine-hygiene brand ''Whisper'' globally but ''Always'' in collectivist markets like Italy and Spain where ''whisper'' framing felt isolating rather than supportive. Successful frame split.', '["it", "es"]', '["individualist", "collectivist"]', 'Both brand names continue; deliberate cultural-frame split.', 'https://www.pg.com/news/'),
        ('analog_037', 'Apple iPhone ''No Sim'' Launch China', 'Apple', 2009, 'Apple launched iPhone in China without an official carrier deal, leaving grey-market phones dominant. Pragmatic-frame misjudgment; consumer trust in Apple suffered for 18 months.', '["zh"]', '["pragmatic", "ambiguous"]', 'China Unicom deal 2010; market-share takeoff began 2011.', 'https://en.wikipedia.org/wiki/IPhone_in_China'),
        ('analog_038', 'Twitter Rebrand to X 2023', 'X Corp.', 2023, 'Twitter rebranded to X overnight in 2023. Status-quo frame violation across all 240M+ users simultaneously. Brand equity ($24B in 2018) largely destroyed in days.', '["en", "ja", "es", "pt", "de", "fr"]', '["status_quo", "ambiguous"]', '~$20B brand-equity loss; advertiser exodus.', 'https://en.wikipedia.org/wiki/X_(social_network)'),
        ('analog_039', 'WeWork ''Live the We Life'' Global Campaign', 'WeWork', 2018, 'WeWork''s collectivist-Western ''community'' framing failed in individualist markets like Germany and pragmatist markets like Japan. Vacancy rates 2-3x higher in those markets.', '["de", "ja"]', '["collectivist", "individualist", "pragmatic"]', 'Market exits; $39B → $9B valuation collapse partly attributable to GTM mismatch.', 'https://en.wikipedia.org/wiki/WeWork');

    -- 4. Cortex Search services. They re-index from text (post_text /
    --    description), so the bundled data needs no vectors. The post service
    --    joins social_posts for post_timestamp (cultural_frames has none).
    CREATE OR REPLACE CORTEX SEARCH SERVICE app_data.comprenda_post_search
        ON post_text
        ATTRIBUTES detected_language, cultural_frame, emotional_tone,
                   event_tag, post_timestamp, sentiment_score, frame_confidence
        WAREHOUSE = comprenda_wh
        TARGET_LAG = '1 hour'
        AS (
            SELECT cf.post_id, cf.post_text, cf.detected_language,
                   cf.cultural_frame, cf.emotional_tone, cf.event_tag,
                   sp.post_timestamp, cf.sentiment_score, cf.frame_confidence
            FROM app_data.cultural_frames cf
            JOIN app_data.social_posts sp ON cf.post_id = sp.post_id
        );

    CREATE OR REPLACE CORTEX SEARCH SERVICE app_data.comprenda_analog_search
        ON description
        ATTRIBUTES company, year, affected_markets, failure_frames
        WAREHOUSE = comprenda_wh
        TARGET_LAG = '24 hours'
        AS (
            SELECT analog_id, case_name, description, company, year,
                   affected_markets, failure_frames, outcome_summary
            FROM app_data.analog_corpus
        );

    -- 5. Narrative Search calls SEARCH_PREVIEW directly as app_user; let it
    --    (and admins) use the services. The procs query them as owner.
    GRANT USAGE ON CORTEX SEARCH SERVICE app_data.comprenda_post_search
        TO APPLICATION ROLE app_user;
    GRANT USAGE ON CORTEX SEARCH SERVICE app_data.comprenda_analog_search
        TO APPLICATION ROLE app_user;
    GRANT USAGE ON CORTEX SEARCH SERVICE app_data.comprenda_post_search
        TO APPLICATION ROLE app_admin;
    GRANT USAGE ON CORTEX SEARCH SERVICE app_data.comprenda_analog_search
        TO APPLICATION ROLE app_admin;

    RETURN 'Comprenda provisioned: corpus loaded + Cortex Search services built.';
END;
$$;

GRANT USAGE ON PROCEDURE app_instance.provision_app() TO APPLICATION ROLE app_admin;

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

GRANT USAGE ON PROCEDURE app_instance.register_consumer_raw_data(STRING, STRING, STRING)
    TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- Streamlit
-- ---------------------------------------------------------------------------
-- Object name = comprenda_app to match manifest `default_streamlit` (customer-
-- facing). MAIN_FILE is the real post-redesign entry (comprenda_app.py + views/,
-- NOT the old nuance_app.py + pages/). Internal nuance_db plumbing is untouched.
CREATE STREAMLIT IF NOT EXISTS app_instance.comprenda_app
    FROM '/streamlit'
    MAIN_FILE = 'comprenda_app.py';

GRANT USAGE ON STREAMLIT app_instance.comprenda_app TO APPLICATION ROLE app_user;
GRANT USAGE ON STREAMLIT app_instance.comprenda_app TO APPLICATION ROLE app_admin;

-- ---------------------------------------------------------------------------
-- The four hero procedures (PLCS, Cultural Translator, AI Brief, Find Analogs)
-- are defined inline above as app_instance.* (ported from snowpark/deploy_*.py).
-- The bundled-data load + Cortex Search services live in app_instance.provision_app(),
-- which the consumer runs once after install (see native_app/README.md) — a
-- native-app setup script has no warehouse, so that compute can't run here.
-- ---------------------------------------------------------------------------
