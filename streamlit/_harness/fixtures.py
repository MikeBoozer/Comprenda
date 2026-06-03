"""Fixture layer for the local preview harness and the public demo.

These fixtures are now backed by **real Cortex outputs** captured from the live
Snowflake account on 2026-06-03 (account REB37163), exported to
``_harness/real_exports/*.json`` before the trial lapsed. See
``real_exports/README.md`` for provenance. Earlier versions of this file used a
hand-invented "EV sports-car" scenario; the demo now shows genuine model output
for the real corpus (8 events × 12 languages × 1,440 posts — iPhone 17, Tesla
Robotaxi, Olympics 2026, …).

The contract is unchanged: ``build_query_module()`` returns a stand-in for
``lib.comprenda_queries`` with the same function names/signatures, so the views
and the public ``demo_app.py`` need no other changes. Nothing here ships to
Snowflake; production (Streamlit-in-Snowflake) keeps the real session + queries.

Snowpark ``.to_pandas()`` upper-cases unquoted identifiers, so the exported rows
(and the DataFrames built from them) use UPPER-case columns — except
``narrative_search``, which the live app builds from Cortex Search JSON and so
returns lower-case columns.
"""
from __future__ import annotations

import json
import os
import types
from pathlib import Path

import pandas as pd

# Set HARNESS_EMPTY=1 before launching to preview first-run / empty states.
EMPTY = bool(os.environ.get("HARNESS_EMPTY"))

_EXPORT_DIR = Path(__file__).resolve().parent / "real_exports"
_FILE_CACHE: dict = {}


def _load(name: str) -> list:
    """Load and cache one exported JSON file (a list of row dicts)."""
    if name not in _FILE_CACHE:
        path = _EXPORT_DIR / f"{name}.json"
        with open(path, encoding="utf-8") as fh:
            _FILE_CACHE[name] = json.load(fh)
    return _FILE_CACHE[name]


def _pj(value):
    """Parse a value that may be a JSON-encoded string.

    Snowpark ARRAY / VARIANT columns serialize as strings via
    ``snow sql --format json`` (e.g. TOP_FRAMES, ADAPTED_VARIANTS). Recurse so a
    parsed list of dicts also has its own string-encoded members parsed (analog
    ``affected_markets`` / ``failure_frames`` arrive double-encoded).
    """
    if isinstance(value, str):
        s = value.strip()
        if s[:1] in "[{":
            try:
                value = json.loads(s)
            except Exception:
                return value
    if isinstance(value, list):
        return [_pj(v) for v in value]
    if isinstance(value, dict):
        return {k: _pj(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# Scalars / lists
# ---------------------------------------------------------------------------
LANGUAGES = [r["DETECTED_LANGUAGE"] for r in _load("languages")]
EVENT_TAGS = [r["EVENT_TAG"] for r in _load("event_tags")]

_kpi_row = _load("kpi")[0]
KPI = {
    "events": int(_kpi_row["EVENTS"]),
    "languages": int(_kpi_row["LANGUAGES"]),
    "posts": int(_kpi_row["POSTS"]),
    "drift_24h": int(_kpi_row["DRIFT_24H"]),
}

_CORPUS_FRESHNESS = (_load("corpus_freshness") or [{}])[0].get("LATEST")

# A sensible default event for the rare case a view passes an unknown tag.
_DEFAULT_EVENT = "iPhone_17_launch" if "iPhone_17_launch" in EVENT_TAGS else (
    EVENT_TAGS[0] if EVENT_TAGS else None)


# ---------------------------------------------------------------------------
# Per-event DataFrames (grouped once; the views slice by event_tag)
# ---------------------------------------------------------------------------
def _grouped_df(name: str, cols: list) -> dict:
    groups: dict = {}
    for r in _load(name):
        groups.setdefault(r["EVENT_TAG"], []).append([r[c] for c in cols])
    return {ev: pd.DataFrame(rows, columns=cols) for ev, rows in groups.items()}


_EVENT_SUMMARY = _grouped_df(
    "event_summary",
    ["DETECTED_LANGUAGE", "N_POSTS", "AVG_SENTIMENT", "DOMINANT_FRAME"])
_CDS = _grouped_df(
    "cds_matrix",
    ["LANGUAGE_A", "LANGUAGE_B", "HEADLINE_SCORE", "FRAME_DIVERGENCE",
     "SENTIMENT_DIVERGENCE", "TOPICAL_OVERLAP", "SITUATION_LABEL", "CDS_CONFIDENCE"])
_FRAMES = _grouped_df(
    "frame_distribution",
    ["DETECTED_LANGUAGE", "CULTURAL_FRAME", "N"])


def _event_slice(groups: dict, event_tag, cols: list) -> pd.DataFrame:
    df = groups.get(event_tag)
    if df is None:
        df = groups.get(_DEFAULT_EVENT)
    return df.copy() if df is not None else pd.DataFrame(columns=cols)


def event_summary_df(event_tag):
    return _event_slice(_EVENT_SUMMARY, event_tag,
                        ["DETECTED_LANGUAGE", "N_POSTS", "AVG_SENTIMENT", "DOMINANT_FRAME"])


def cds_matrix_df(event_tag=None):
    return _event_slice(_CDS, event_tag,
                        ["LANGUAGE_A", "LANGUAGE_B", "HEADLINE_SCORE", "FRAME_DIVERGENCE",
                         "SENTIMENT_DIVERGENCE", "TOPICAL_OVERLAP", "SITUATION_LABEL",
                         "CDS_CONFIDENCE"])


def frame_distribution_df(event_tag):
    return _event_slice(_FRAMES, event_tag, ["DETECTED_LANGUAGE", "CULTURAL_FRAME", "N"])


# ---------------------------------------------------------------------------
# Dashboard tables
# ---------------------------------------------------------------------------
def drift_events_df(limit=10):
    cols = ["ENTITY_NAME", "LANGUAGE_A", "LANGUAGE_B",
            "PREV_CDS", "NEW_CDS", "DELTA_CDS", "DETECTED_AT"]
    rows = [[r[c] for c in cols] for r in _load("drift_events")]
    return pd.DataFrame(rows, columns=cols).head(limit)


def plcs_scores_df(limit=10):
    cols = ["TARGET_MARKET", "PLCS_SCORE", "CONFIDENCE", "DRAFT_PREVIEW", "INFERENCE_TIMESTAMP"]
    rows = [[r[c] for c in cols] for r in _load("recent_plcs_scores")]
    return pd.DataFrame(rows, columns=cols).head(limit)


def tracked_entities_df():
    cols = ["ENTITY_ID", "ENTITY_NAME", "ENTITY_TYPE", "OWNER_EMAIL",
            "CDS_THRESHOLD_DELTA", "CDS_THRESHOLD_ABS", "ACTIVE", "CREATED_AT"]
    rows = [[r[c] for c in cols] for r in _load("tracked_entities")]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# PLCS — keyed by target market (the Tesla Robotaxi individualist draft, scored
# across all 12 markets). Home market (en) is safe; collectivist markets elevated.
# ---------------------------------------------------------------------------
_PLCS_BY_MARKET = {r["TARGET_MARKET"]: r for r in _load("plcs_runs")}
PLCS_DRAFT = next(iter(_PLCS_BY_MARKET.values()), {}).get("DRAFT_CONTENT", "")


def _plcs_for(market):
    r = _PLCS_BY_MARKET.get(market)
    if r is None:
        return {
            "plcs_id": f"demo-{market}", "plcs_score": 50, "confidence": 0.5,
            "top_frames": ["ambiguous"], "nearest_analogs": [],
            "risk_narrative": ("Insufficient in-market history in this demo export to "
                               "score with confidence; treat as provisional."),
            "target_market": market, "model": "claude-4-sonnet",
        }
    return {
        "plcs_id": r["PLCS_ID"],
        "plcs_score": int(r["PLCS_SCORE"]),
        "confidence": float(r["PLCS_CONFIDENCE"]),
        "top_frames": _pj(r["TOP_FRAMES"]),
        "nearest_analogs": _pj(r["NEAREST_ANALOGS"]),
        "risk_narrative": r["RISK_NARRATIVE"],
        "target_market": market,
        "model": r["MODEL_USED"],
    }


# ---------------------------------------------------------------------------
# Analogs — merged from the two captured find_analogs result sets (deduped),
# canonical first (Levi's 501 in India, WeWork, P&G Whisper, Toyota Prius …).
# ---------------------------------------------------------------------------
def _analogs_from(name: str) -> list:
    raw = _load(name)[0]["FIND_ANALOGS"]
    parsed = _pj(raw)
    return parsed.get("analogs", []) if isinstance(parsed, dict) else []


def _build_analogs() -> list:
    seen, out = set(), []
    for name in ("analogs_canonical", "analogs_broad"):
        for a in _analogs_from(name):
            aid = a.get("analog_id")
            if aid in seen:
                continue
            seen.add(aid)
            out.append(a)
    return out


_ANALOGS = _build_analogs()


# ---------------------------------------------------------------------------
# Briefs — keyed by event (every event has a real generated brief).
# ---------------------------------------------------------------------------
_BRIEFS_BY_EVENT = {r["EVENT_TAG"]: r for r in _load("ai_briefs")}


def _brief_for(event_tag, target_languages):
    r = _BRIEFS_BY_EVENT.get(event_tag) or _BRIEFS_BY_EVENT.get(_DEFAULT_EVENT)
    if r is None:
        return {"brief_id": "demo", "event_tag": event_tag,
                "target_languages": list(target_languages), "brief_markdown": "",
                "source_post_ids": [], "model": "claude-4-sonnet"}
    return {
        "brief_id": r["BRIEF_ID"],
        "event_tag": event_tag,
        "target_languages": list(target_languages) or _pj(r["TARGET_LANGUAGES"]),
        "brief_markdown": r["BRIEF_MARKDOWN"],
        "source_post_ids": _pj(r["SOURCE_POST_IDS"]),
        "model": r["MODEL_USED"],
    }


# ---------------------------------------------------------------------------
# Translator — the captured en→ja run (threat-framing reframe of PLCS_DRAFT).
# ---------------------------------------------------------------------------
def _translator_result():
    r = _load("translator_runs")[0]
    return {
        "run_id": r["RUN_ID"],
        "source_content": r["SOURCE_CONTENT"],
        "target_market": r["TARGET_MARKET"],
        "target_frame_hint": r["TARGET_FRAME_HINT"],
        "variants": _pj(r["ADAPTED_VARIANTS"]),
        "model": r["MODEL_USED"],
    }


# ---------------------------------------------------------------------------
# Narrative search — a varied real sample of the corpus (one post per
# language×frame). Filters by language/frame and ranks by query token overlap so
# the page is genuinely interactive on real data.
# ---------------------------------------------------------------------------
_NARRATIVE_POOL = [
    {"post_id": r["POST_ID"], "post_text": r["POST_TEXT"],
     "detected_language": r["DETECTED_LANGUAGE"], "cultural_frame": r["CULTURAL_FRAME"],
     "emotional_tone": r["EMOTIONAL_TONE"], "event_tag": r["EVENT_TAG"],
     "sentiment_score": r["SENTIMENT_SCORE"]}
    for r in _load("narrative_pool")
]


def narrative_search_df(query, languages=None, frames=None, limit=25):
    rows = _NARRATIVE_POOL
    if languages:
        rows = [r for r in rows if r["detected_language"] in set(languages)]
    if frames:
        rows = [r for r in rows if r["cultural_frame"] in set(frames)]
    terms = [t for t in (query or "").lower().split() if len(t) > 1]
    if terms:
        def _score(r):
            text = r["post_text"].lower()
            return sum(t in text for t in terms)
        rows = sorted(rows, key=_score, reverse=True)
    return pd.DataFrame(rows[:limit])


# ---------------------------------------------------------------------------
# Fake Snowpark session — covers inline session.sql() (the Divergence Matrix
# page inlines its CDS query rather than calling lib.get_cds_matrix).
# ---------------------------------------------------------------------------
class _Result:
    def __init__(self, rows=None, df=None):
        self._rows = rows if rows is not None else []
        self._df = df

    def collect(self):
        return self._rows

    def to_pandas(self):
        return self._df if self._df is not None else pd.DataFrame()


class FakeSession:
    """Minimal stand-in for a Snowpark Session for inline queries."""

    def sql(self, query, params=None):
        q = (query or "").upper()
        if "CULTURAL_DIVERGENCE_SCORES" in q:
            # The Divergence Matrix inlines `... WHERE event_tag = ?` with
            # params=[chosen]; return that event's real matrix.
            event_tag = params[0] if params else None
            return _Result(df=cds_matrix_df(event_tag))
        # Unknown inline query → empty; query helpers are stubbed separately.
        return _Result(rows=[], df=pd.DataFrame())

    def __getattr__(self, name):  # be permissive about unused session methods
        def _noop(*a, **k):
            return _Result()
        return _noop


# ---------------------------------------------------------------------------
# Fake query module — mirrors lib.comprenda_queries, ignores the session arg.
# ---------------------------------------------------------------------------
def build_query_module():
    m = types.ModuleType("lib.comprenda_queries")

    _empty_kpi = {"events": 0, "languages": 0, "posts": 0, "drift_24h": 0}
    _empty_df = lambda cols: pd.DataFrame(columns=cols)

    m.get_kpi_summary = lambda session: (dict(_empty_kpi) if EMPTY else dict(KPI))
    m.get_recent_drift_events = lambda session, limit=10: (
        _empty_df(["ENTITY_NAME", "LANGUAGE_A", "LANGUAGE_B", "PREV_CDS",
                   "NEW_CDS", "DELTA_CDS", "DETECTED_AT"]) if EMPTY
        else drift_events_df(limit))
    m.get_recent_plcs_scores = lambda session, limit=10: (
        _empty_df(["TARGET_MARKET", "PLCS_SCORE", "CONFIDENCE", "DRAFT_PREVIEW",
                   "INFERENCE_TIMESTAMP"]) if EMPTY else plcs_scores_df(limit))
    m.list_event_tags = lambda session: ([] if EMPTY else list(EVENT_TAGS))
    m.list_languages = lambda session: ([] if EMPTY else list(LANGUAGES))
    m.get_session_context = lambda session: {
        "Role": "NUANCE_APP_ROLE (demo)", "Warehouse": "NUANCE_DEV_WH",
        "Database": "NUANCE_DB", "Schema": "OUTPUTS", "Region": "AWS_US_WEST_2 (demo)",
        "Snowflake": "10.x (demo)", "Session ID": "demo-session-0001",
        "Last query ID": "01b-demo-query-id",
    }
    m.get_corpus_freshness = lambda session: (None if EMPTY else _CORPUS_FRESHNESS)
    m.get_event_summary = lambda session, event_tag: event_summary_df(event_tag)
    m.get_cds_matrix = lambda session, event_tag: cds_matrix_df(event_tag)
    m.get_frame_distribution = lambda session, event_tag: frame_distribution_df(event_tag)
    m.call_plcs = lambda session, draft_content, source_language, target_market, requested_by=None: _plcs_for(target_market)
    m.call_translator = lambda session, *a, **k: _translator_result()
    m.list_tracked_entities = lambda session: (
        _empty_df(["ENTITY_ID", "ENTITY_NAME", "ENTITY_TYPE", "OWNER_EMAIL",
                   "CDS_THRESHOLD_DELTA", "CDS_THRESHOLD_ABS", "ACTIVE", "CREATED_AT"])
        if EMPTY else tracked_entities_df())
    m.add_tracked_entity = lambda session, *a, **k: None
    m.find_matching_events = lambda session, entity_name: _find_matching_events(entity_name)
    m.call_find_analogs = lambda session, query_text, target_market=None, k=5: {
        "query": query_text, "target_market": target_market,
        "analogs": _ANALOGS[:k], "count": min(k, len(_ANALOGS))}
    m.call_generate_brief = lambda session, event_tag, target_languages, requested_by=None: _brief_for(event_tag, target_languages)
    m.narrative_search = lambda session, query, languages=None, frames=None, limit=25: narrative_search_df(query, languages, frames, limit)
    # _sql: the Native-App object-name resolver wrapper. The Divergence Matrix
    # imports it for its inlined CDS query. In the demo there is no retargeting,
    # so it delegates to the (fake) session — FakeSession.sql returns the matching
    # event's CDS matrix for that query.
    m._sql = lambda session, text, params=None: session.sql(text, params=params)

    # Safety net (PEP 562 module __getattr__): any OTHER private helper a view
    # might import directly from lib.comprenda_queries — which this fixture fully
    # replaces — resolves to a session.sql pass-through, so adding such an import
    # to a view can never ImportError the public demo. Public (non-underscore)
    # names must still be defined explicitly above, so a genuinely missing helper
    # surfaces loudly.
    def _missing(name):
        if name.startswith("_") and not name.startswith("__"):
            return lambda session, text, params=None: session.sql(text, params=params)
        raise AttributeError(
            f"module 'lib.comprenda_queries' (demo fixture) has no attribute {name!r}")
    m.__getattr__ = _missing
    return m


def _find_matching_events(entity_name):
    """Mirror the live ILIKE match: an entity name matches event_tags that
    contain the raw or space-to-underscore-normalised name (case-insensitive)."""
    raw = (entity_name or "").lower()
    norm = raw.replace(" ", "_")
    return [e for e in EVENT_TAGS
            if raw and (raw in e.lower() or norm in e.lower())]
