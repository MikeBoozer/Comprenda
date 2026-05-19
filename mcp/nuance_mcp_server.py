"""
Nuance MCP Server — exposes Nuance's cultural-intelligence capabilities to
any MCP-compatible AI agent (Claude Desktop, Claude Code, Cursor, ChatGPT
desktop, enterprise agents).

This is the strategic 2026 positioning: Nuance becomes the *cultural context
substrate* that every enterprise AI agent can call. Brand-tier feature.

Tools exposed:
  - nuance.score_content          (Pre-Launch Cultural Risk Score)
  - nuance.translate_culture      (Cultural Translator)
  - nuance.get_divergence         (CDS lookup)
  - nuance.find_analogs           (Analog Retrieval)
  - nuance.generate_brief         (AI Brief generator)
  - nuance.list_events            (Available events)
  - nuance.list_tracked_entities  (Active drift subscriptions)

Auth: per-customer Snowflake credentials via env vars or ~/.snowflake/config.toml.
Each tool call runs SQL against the customer's own Snowflake — data never
leaves their boundary.

Run locally:
    pip install -r mcp/requirements.txt
    python mcp/nuance_mcp_server.py

Hosted: see mcp/README.md for Fly.io / Cloud Run / Render deployment.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "ERROR: install MCP SDK: pip install 'mcp[cli]>=1.2'",
        file=sys.stderr,
    )
    sys.exit(1)

from snowflake.snowpark import Session


# ---------------------------------------------------------------------------
# Snowflake connection (lazy, cached, auto-reconnecting)
# ---------------------------------------------------------------------------
_session: Optional[Session] = None


def _build_session() -> Session:
    """Create a brand-new Snowflake session from config file or environment variables."""
    if os.path.exists(os.path.expanduser("~/.snowflake/config.toml")):
        return Session.builder.config(
            "connection_name",
            os.environ.get("SNOWFLAKE_CONNECTION", "default"),
        ).create()
    cfg = {
        "account":          os.environ["SNOWFLAKE_ACCOUNT"],
        "user":             os.environ["SNOWFLAKE_USER"],
        "password":         os.environ.get("SNOWFLAKE_PASSWORD"),
        "private_key_path": os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"),
        "role":             os.environ.get("SNOWFLAKE_ROLE", "NUANCE_APP_ROLE"),
        "warehouse":        os.environ.get("SNOWFLAKE_WAREHOUSE", "NUANCE_DEV_WH"),
        "database":         os.environ.get("SNOWFLAKE_DATABASE", "NUANCE_DB"),
        "schema":           os.environ.get("SNOWFLAKE_SCHEMA", "OUTPUTS"),
    }
    return Session.builder.configs(
        {k: v for k, v in cfg.items() if v is not None}
    ).create()


def get_session() -> Session:
    """Return a live Snowflake session, reconnecting automatically if the connection dropped."""
    global _session
    if _session is not None:
        try:
            _session.sql("SELECT 1").collect()  # lightweight ping to test the connection
            return _session
        except Exception:
            _session = None  # connection is stale — discard it and rebuild below
    _session = _build_session()
    return _session


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("nuance")


_MAX_CONTENT_CHARS = 2_000  # ~400 words — generous for marketing copy, blocks runaway agents


def _check_length(text: str, field: str) -> None:
    """Raise ValueError if text exceeds the per-call character limit."""
    if len(text) > _MAX_CONTENT_CHARS:
        raise ValueError(
            f"'{field}' is {len(text):,} characters — the limit is "
            f"{_MAX_CONTENT_CHARS:,}. Please shorten the input."
        )


def _parse_variant(raw):
    """Snowflake returns CALL results as VARIANT; sometimes string, sometimes dict."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}
    return raw


@mcp.tool()
def score_content(
    draft_content: str,
    source_language: str = "en",
    target_market: str = "ja",
    requested_by: Optional[str] = None,
) -> dict:
    """
    Pre-Launch Cultural Risk Score (PLCS).

    Score how culturally risky a piece of marketing draft content is for a
    target market, on a 0-100 scale. Returns the score, confidence, top
    cultural frames the content activates, nearest historical analogs, and
    an LLM-synthesized risk narrative.

    Args:
        draft_content: The marketing copy to evaluate (tagline, ad headline,
                       product name, hero copy, social post).
        source_language: ISO 639-1 code of the source text (default "en").
        target_market:   ISO 639-1 code of the target market.
        requested_by:    Optional user identifier for audit.

    Returns:
        {plcs_score, confidence, top_frames, nearest_analogs, risk_narrative,
         target_market, model}
    """
    _check_length(draft_content, "draft_content")
    s = get_session()
    row = s.sql(
        "CALL NUANCE_DB.OUTPUTS.SCORE_CONTENT(?,?,?,?)",
        params=[draft_content, source_language, target_market, requested_by],
    ).collect()
    return _parse_variant(row[0][0]) if row else {"error": "no result"}


@mcp.tool()
def translate_culture(
    source_content: str,
    target_market: str,
    source_language: str = "en",
    target_frame_hint: Optional[str] = None,
    requested_by: Optional[str] = None,
) -> dict:
    """
    Cultural Translator — adapt content to preserve intent while shifting
    cultural frame appropriately for the target market.

    This is NOT translation. Produces 2-3 variants in the target language
    that re-frame the content (e.g., individualist → collectivist).

    Args:
        source_content: The content to adapt.
        target_market:  ISO 639-1 code of the target market.
        source_language: Source language code (default "en").
        target_frame_hint: Optional frame override (e.g. "collectivist",
                           "spiritual_ethical", "pragmatic"). If None, the
                           dominant frame in the target market's enriched
                           corpus is auto-selected.
        requested_by:   Optional user identifier.

    Returns:
        {run_id, variants: [{text, frame_shift, rationale}, ...],
         target_frame_hint, model}
    """
    _check_length(source_content, "source_content")
    s = get_session()
    row = s.sql(
        "CALL NUANCE_DB.OUTPUTS.TRANSLATE_CULTURE(?,?,?,?,?)",
        params=[source_content, source_language, target_market,
                target_frame_hint, requested_by],
    ).collect()
    return _parse_variant(row[0][0]) if row else {"error": "no result"}


@mcp.tool()
def get_divergence(
    event_tag: str,
    language_a: Optional[str] = None,
    language_b: Optional[str] = None,
) -> dict:
    """
    Look up the Cultural Divergence Score (CDS) for an event_tag.

    If language_a and language_b are provided, returns the single pair.
    Otherwise returns all language pairs sorted by CDS descending.

    Args:
        event_tag: The event identifier (e.g., "iPhone_17_launch").
        language_a: Optional ISO 639-1 code.
        language_b: Optional ISO 639-1 code.

    Returns:
        {event_tag, pairs: [{language_a, language_b, cds_score, confidence}, ...]}
    """
    s = get_session()
    where = ["event_tag = ?"]
    params = [event_tag]
    if language_a and language_b:
        # Canonicalize order (table stores language_a < language_b)
        la, lb = sorted([language_a, language_b])
        where.append("language_a = ? AND language_b = ?")
        params += [la, lb]
    sql = (
        "SELECT language_a, language_b, "
        "       ROUND(cds_score,3) AS cds_score, "
        "       ROUND(cds_confidence,2) AS confidence "
        "FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY cds_score DESC LIMIT 50"
    )
    rows = s.sql(sql, params=params).collect()
    return {
        "event_tag": event_tag,
        "pairs": [
            {
                "language_a": r["LANGUAGE_A"],
                "language_b": r["LANGUAGE_B"],
                "cds_score": float(r["CDS_SCORE"]),
                "confidence": float(r["CONFIDENCE"]) if r["CONFIDENCE"] is not None else None,
            }
            for r in rows
        ],
    }


@mcp.tool()
def find_analogs(
    query_text: str,
    target_market: Optional[str] = None,
    k: int = 5,
) -> dict:
    """
    Find the k most similar historical campaign-launch divergence patterns
    (HSBC, Mercedes, Pepsi, etc.) for a given query.

    Args:
        query_text: Description of current event or draft content.
        target_market: Optional ISO 639-1 code to filter analogs by affected market.
        k: Number of analogs (default 5, max 20).

    Returns:
        {query, analogs: [{case_name, company, year, description,
                           affected_markets, failure_frames, outcome_summary,
                           distance}, ...]}
    """
    _check_length(query_text, "query_text")
    s = get_session()
    k = max(1, min(20, k))
    row = s.sql(
        "CALL NUANCE_DB.OUTPUTS.FIND_ANALOGS(?,?,?)",
        params=[query_text, target_market, k],
    ).collect()
    return _parse_variant(row[0][0]) if row else {"error": "no result"}


@mcp.tool()
def generate_brief(
    event_tag: str,
    target_languages: list[str],
    requested_by: Optional[str] = None,
) -> dict:
    """
    Generate a 2-page AI Cultural Intelligence Brief for an event.

    Args:
        event_tag: The event identifier.
        target_languages: List of ISO 639-1 codes to include.
        requested_by: Optional user identifier.

    Returns:
        {brief_id, brief_markdown, event_tag, target_languages, source_post_ids,
         model}
    """
    s = get_session()
    row = s.sql(
        "CALL NUANCE_DB.OUTPUTS.GENERATE_BRIEF(?, PARSE_JSON(?), ?)",
        params=[event_tag, json.dumps(target_languages), requested_by],
    ).collect()
    return _parse_variant(row[0][0]) if row else {"error": "no result"}


@mcp.tool()
def list_events() -> dict:
    """List all event tags with post counts and language coverage."""
    s = get_session()
    rows = s.sql(
        "SELECT event_tag, COUNT(*) AS n_posts, "
        "       COUNT(DISTINCT detected_language) AS n_langs "
        "FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS "
        "WHERE event_tag IS NOT NULL "
        "GROUP BY event_tag ORDER BY n_posts DESC"
    ).collect()
    return {
        "events": [
            {
                "event_tag": r["EVENT_TAG"],
                "n_posts": int(r["N_POSTS"]),
                "n_languages": int(r["N_LANGS"]),
            }
            for r in rows
        ]
    }


@mcp.tool()
def list_tracked_entities() -> dict:
    """List entities currently subscribed to Cultural Drift Alerts."""
    s = get_session()
    rows = s.sql(
        "SELECT entity_name, entity_type, owner_email, "
        "       cds_threshold_delta, cds_threshold_abs, active, created_at "
        "FROM NUANCE_DB.LIBRARY.TRACKED_ENTITIES "
        "ORDER BY created_at DESC"
    ).collect()
    return {
        "entities": [
            {
                "entity_name": r["ENTITY_NAME"],
                "entity_type": r["ENTITY_TYPE"],
                "owner_email": r["OWNER_EMAIL"],
                "threshold_delta": float(r["CDS_THRESHOLD_DELTA"]),
                "threshold_abs": float(r["CDS_THRESHOLD_ABS"]),
                "active": bool(r["ACTIVE"]),
                "created_at": str(r["CREATED_AT"]),
            }
            for r in rows
        ]
    }


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Default transport is stdio (good for Claude Desktop, Cursor).
    # For HTTP hosting (Fly.io, Cloud Run), set NUANCE_MCP_TRANSPORT=http.
    transport = os.environ.get("NUANCE_MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
