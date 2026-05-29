"""Query helpers for Nuance Streamlit pages."""
from __future__ import annotations

import json
import pandas as pd
from snowflake.snowpark import Session


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def get_kpi_summary(session: Session) -> dict:
    row = session.sql(
        "SELECT "
        "  (SELECT COUNT(DISTINCT event_tag) FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS) AS events, "
        "  (SELECT COUNT(DISTINCT detected_language) FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS) AS languages, "
        "  (SELECT COUNT(*) FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS) AS posts, "
        "  (SELECT COUNT(*) FROM NUANCE_DB.INTERNAL.DRIFT_EVENTS "
        "   WHERE detected_at > DATEADD('hour', -24, CURRENT_TIMESTAMP())) AS drift_24h"
    ).collect()[0]
    return {
        "events": int(row["EVENTS"] or 0),
        "languages": int(row["LANGUAGES"] or 0),
        "posts": int(row["POSTS"] or 0),
        "drift_24h": int(row["DRIFT_24H"] or 0),
    }


def get_recent_drift_events(session: Session, limit: int = 10) -> pd.DataFrame:
    df = session.sql(
        "SELECT entity_name, language_a, language_b, "
        "       ROUND(prev_cds, 3) AS prev_cds, "
        "       ROUND(new_cds, 3) AS new_cds, "
        "       ROUND(delta_cds, 3) AS delta_cds, "
        "       detected_at "
        "FROM NUANCE_DB.INTERNAL.DRIFT_EVENTS "
        "ORDER BY detected_at DESC LIMIT ?",
        params=[limit],
    ).to_pandas()
    return df


def get_recent_plcs_scores(session: Session, limit: int = 10) -> pd.DataFrame:
    df = session.sql(
        "SELECT target_market, plcs_score, "
        "       ROUND(plcs_confidence, 2) AS confidence, "
        "       SUBSTR(draft_content, 1, 60) || '…' AS draft_preview, "
        "       inference_timestamp "
        "FROM NUANCE_DB.OUTPUTS.PRE_LAUNCH_RISK_SCORES "
        "ORDER BY inference_timestamp DESC LIMIT ?",
        params=[limit],
    ).to_pandas()
    return df


# ---------------------------------------------------------------------------
# Event Explorer
# ---------------------------------------------------------------------------
def list_event_tags(session: Session) -> list[str]:
    rows = session.sql(
        "SELECT DISTINCT event_tag FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS "
        "WHERE event_tag IS NOT NULL ORDER BY event_tag"
    ).collect()
    return [r["EVENT_TAG"] for r in rows]


def list_languages(session: Session) -> list[str]:
    rows = session.sql(
        "SELECT DISTINCT detected_language FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS "
        "WHERE detected_language IS NOT NULL ORDER BY detected_language"
    ).collect()
    return [r["DETECTED_LANGUAGE"] for r in rows]


def get_session_context(session: Session) -> dict:
    """Read-only Snowflake session context for the diagnostics footer.

    Only the user's own, non-sensitive operational context — no CURRENT_USER /
    CURRENT_ACCOUNT. One metadata query; nothing cross-tenant or secret.
    """
    rows = session.sql(
        "SELECT CURRENT_ROLE() AS role, CURRENT_WAREHOUSE() AS wh, "
        "CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS sch, "
        "CURRENT_REGION() AS region, CURRENT_VERSION() AS sfver, "
        "CURRENT_SESSION() AS sess, LAST_QUERY_ID() AS lastq"
    ).collect()
    if not rows:
        return {}
    r = rows[0]
    return {
        "Role": r["ROLE"], "Warehouse": r["WH"], "Database": r["DB"],
        "Schema": r["SCH"], "Region": r["REGION"], "Snowflake": r["SFVER"],
        "Session ID": r["SESS"], "Last query ID": r["LASTQ"],
    }


def get_corpus_freshness(session: Session):
    """Most recent corpus ingestion timestamp (None if the corpus is empty)."""
    rows = session.sql(
        "SELECT MAX(ingested_at) AS latest FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS"
    ).collect()
    return rows[0]["LATEST"] if rows else None


def get_event_summary(session: Session, event_tag: str) -> pd.DataFrame:
    df = session.sql(
        "SELECT detected_language, "
        "       COUNT(*) AS n_posts, "
        "       ROUND(AVG(sentiment_score), 3) AS avg_sentiment, "
        "       MODE(cultural_frame) AS dominant_frame "
        "FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
        "WHERE event_tag = ? "
        "GROUP BY detected_language ORDER BY n_posts DESC",
        params=[event_tag],
    ).to_pandas()
    return df


# ---------------------------------------------------------------------------
# Divergence Matrix
# ---------------------------------------------------------------------------
def get_cds_matrix(session: Session, event_tag: str) -> pd.DataFrame:
    # headline_score = frame_divergence (the primary axis). Select only the latest
    # computed batch per language pair, since the table appends a batch each run.
    df = session.sql(
        "SELECT language_a, language_b, headline_score, frame_divergence, "
        "       sentiment_divergence, topical_overlap, situation_label, cds_confidence "
        "FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES "
        "WHERE event_tag = ? AND frame_divergence IS NOT NULL "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY language_a, language_b "
        "                           ORDER BY computed_at DESC) = 1 "
        "ORDER BY headline_score DESC",
        params=[event_tag],
    ).to_pandas()
    return df


# ---------------------------------------------------------------------------
# Frame Distribution
# ---------------------------------------------------------------------------
def get_frame_distribution(session: Session, event_tag: str) -> pd.DataFrame:
    df = session.sql(
        "SELECT detected_language, cultural_frame, COUNT(*) AS n "
        "FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
        "WHERE event_tag = ? "
        "GROUP BY detected_language, cultural_frame "
        "ORDER BY detected_language, n DESC",
        params=[event_tag],
    ).to_pandas()
    return df


# ---------------------------------------------------------------------------
# Pre-Launch Risk
# ---------------------------------------------------------------------------
def call_plcs(
    session: Session,
    draft_content: str,
    source_language: str,
    target_market: str,
    requested_by: str = None,
) -> dict:
    row = session.sql(
        "CALL NUANCE_DB.OUTPUTS.SCORE_CONTENT(?,?,?,?)",
        params=[draft_content, source_language, target_market, requested_by],
    ).collect()
    # Snowflake returns the VARIANT as a string-serialized JSON
    raw = row[0][0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ---------------------------------------------------------------------------
# Cultural Translator
# ---------------------------------------------------------------------------
def call_translator(
    session: Session,
    source_content: str,
    source_language: str,
    target_market: str,
    target_frame_hint: str = None,
    requested_by: str = None,
) -> dict:
    row = session.sql(
        "CALL NUANCE_DB.OUTPUTS.TRANSLATE_CULTURE(?,?,?,?,?)",
        params=[source_content, source_language, target_market,
                target_frame_hint, requested_by],
    ).collect()
    raw = row[0][0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ---------------------------------------------------------------------------
# Drift Alerts
# ---------------------------------------------------------------------------
def list_tracked_entities(session: Session) -> pd.DataFrame:
    return session.sql(
        "SELECT entity_id, entity_name, entity_type, owner_email, "
        "       cds_threshold_delta, cds_threshold_abs, active, created_at "
        "FROM NUANCE_DB.LIBRARY.TRACKED_ENTITIES ORDER BY created_at DESC"
    ).to_pandas()


def add_tracked_entity(
    session: Session,
    entity_name: str,
    owner_email: str,
    languages: list[str],
    delta: float = 0.15,
    abs_threshold: float = 0.55,
) -> None:
    session.sql(
        "INSERT INTO NUANCE_DB.LIBRARY.TRACKED_ENTITIES "
        "(entity_name, owner_email, languages, cds_threshold_delta, cds_threshold_abs) "
        "SELECT ?, ?, PARSE_JSON(?), ?, ?",
        params=[entity_name, owner_email, json.dumps(languages), delta, abs_threshold],
    ).collect()


# ---------------------------------------------------------------------------
# Drift Alerts helpers
# ---------------------------------------------------------------------------
def find_matching_events(session: Session, entity_name: str) -> list[str]:
    """Return event_tags in the corpus that match the given entity name.

    Mirrors the ILIKE logic used by the drift-check task: matches on the
    raw name and on a space-to-underscore normalised version, both case-
    insensitive. Returns a list of matching event_tag strings (may be empty).
    """
    normalised = entity_name.replace(" ", "_")
    rows = session.sql(
        "SELECT DISTINCT event_tag "
        "FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS "
        "WHERE event_tag IS NOT NULL "
        "  AND (LOWER(event_tag) LIKE '%' || LOWER(?) || '%' "
        "    OR LOWER(event_tag) LIKE '%' || LOWER(?) || '%') "
        "ORDER BY event_tag",
        params=[entity_name, normalised],
    ).collect()
    return [r["EVENT_TAG"] for r in rows]


# ---------------------------------------------------------------------------
# Analog Retrieval
# ---------------------------------------------------------------------------
def call_find_analogs(
    session: Session, query_text: str, target_market: str = None, k: int = 5
) -> dict:
    row = session.sql(
        "CALL NUANCE_DB.OUTPUTS.FIND_ANALOGS(?,?,?)",
        params=[query_text, target_market, k],
    ).collect()
    raw = row[0][0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ---------------------------------------------------------------------------
# AI Brief
# ---------------------------------------------------------------------------
def call_generate_brief(
    session: Session, event_tag: str, target_languages: list[str], requested_by: str = None
) -> dict:
    row = session.sql(
        "CALL NUANCE_DB.OUTPUTS.GENERATE_BRIEF(?, PARSE_JSON(?), ?)",
        params=[event_tag, json.dumps(target_languages), requested_by],
    ).collect()
    raw = row[0][0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ---------------------------------------------------------------------------
# Narrative Search
# ---------------------------------------------------------------------------
def narrative_search(
    session: Session,
    query: str,
    languages: list[str] = None,
    frames: list[str] = None,
    limit: int = 25,
) -> pd.DataFrame:
    body = {"query": query, "limit": limit, "columns": [
        "post_id", "post_text", "detected_language", "cultural_frame",
        "emotional_tone", "event_tag", "sentiment_score",
    ]}
    if languages or frames:
        filt = {"@and": []}
        if languages:
            filt["@and"].append({"@or": [{"@eq": {"detected_language": l}} for l in languages]})
        if frames:
            filt["@and"].append({"@or": [{"@eq": {"cultural_frame": f}} for f in frames]})
        body["filter"] = filt
    row = session.sql(
        "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW("
        "'NUANCE_DB.ENRICHED.NUANCE_POST_SEARCH', ?) AS r",
        params=[json.dumps(body)],
    ).collect()
    raw = row[0]["R"] if row else "{}"
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return pd.DataFrame(parsed.get("results", []))
    except Exception:
        return pd.DataFrame()
