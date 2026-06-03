"""Mock data + fakes for the local preview harness.

Fixture shapes are grounded in the real contracts:
  - PLCS  : snowpark/deploy_plcs.py return dict
  - Brief : snowpark/deploy_ai_brief.py return dict
  - queries: lib/comprenda_queries.py SQL column names (Snowpark .to_pandas()
             upper-cases unquoted identifiers, so DataFrame columns are UPPER)

Nothing here ships to Snowflake — it is only imported by sitecustomize.py when
the harness PYTHONPATH is active. Production keeps the real session + queries.
"""
from __future__ import annotations

import os
import types
import pandas as pd

# Set HARNESS_EMPTY=1 before launching to preview first-run / empty states.
EMPTY = bool(os.environ.get("HARNESS_EMPTY"))

# ---------------------------------------------------------------------------
# Scalar / list fixtures
# ---------------------------------------------------------------------------
LANGUAGES = ["de", "en", "es", "fr", "ja", "ko", "pt", "zh"]
EVENT_TAGS = [
    "ev_automotive_ev_launch",
    "ev_luxury_rebrand",
    "ev_streaming_price_hike",
    "ev_athleisure_campaign",
]

KPI = {"events": 142, "languages": 38, "posts": 48213, "drift_24h": 2}

# market -> (score, confidence, top_frames, risk_narrative)
_PLCS = {
    "ja": (82, 0.86, ["status_quo", "craft_reverence", "national_pride"],
           "The draft's individualist, speed-forward framing collides with a market "
           "that codes premium automotive around craft reverence and quiet status. "
           "Across 1,204 in-market posts the dominant frame is status quo; an "
           "assertive \"puts you first\" register reads as status loss, not aspiration."),
    "ko": (71, 0.78, ["status_loss", "individualist", "price_anxiety"],
           "The line lands near a status-loss frame that has historically depressed "
           "launch sentiment in this market. Topical overlap is high, but the emotional "
           "register is misaligned."),
    "zh": (58, 0.74, ["price_anxiety", "individualist", "status_loss"],
           "Price-anxiety framing is ascendant in the corpus, and the draft addresses "
           "only freedom, never value. That partial mismatch is worth adapting before "
           "launch."),
    "es": (47, 0.69, ["individualist", "national_pride", "other"],
           "The individualist frame is broadly compatible here, so the residual risk is "
           "tonal rather than structural. Light lexical tuning is enough."),
    "fr": (41, 0.72, ["craft", "reform_seeking", "premium_affirmation"],
           "Craft and premium-affirmation frames dominate, and the draft sits adjacent "
           "to them. Only minor lexical tuning is needed to align it."),
    "de": (34, 0.81, ["craft", "premium_affirmation", "reform_seeking"],
           "The engineering-craft frame that governs this market absorbs the draft's "
           "performance claim without friction, so no adaptation is needed."),
}


def _plcs_for(market):
    score, conf, frames, narrative = _PLCS.get(
        market, (50, 0.50, ["other"], "Insufficient in-market history to score with "
                                       "confidence; treat as provisional."))
    return {
        "plcs_id": f"mock-{market}",
        "plcs_score": score,
        "confidence": conf,
        "top_frames": frames,
        "nearest_analogs": [f"post_{market}_{i}" for i in range(3)],
        "risk_narrative": narrative,
        "target_market": market,
        "model": "claude-4-sonnet (mock)",
    }


_ANALOGS = [
    {"case_name": "Open Road, Open Wallet", "company": "Velar Motors", "year": 2019,
     "description": "Launch tagline foregrounding personal freedom in a craft-coded market.",
     "outcome_summary": "Sentiment fell 14 pts in 6 weeks; line withdrawn and re-cut around heritage.",
     "failure_frames": ["status_loss", "individualist"],
     "affected_markets": ["ja", "ko"], "distance": 0.118, "similarity": 0.88},
    {"case_name": "Drive It Like You Stole It", "company": "Northwind EV", "year": 2021,
     "description": "Speed-forward performance claim in markets prioritising restraint.",
     "outcome_summary": "Localized variants recovered most of the gap within a quarter.",
     "failure_frames": ["status_loss"], "affected_markets": ["ja"],
     "distance": 0.156, "similarity": 0.81},
    {"case_name": "Yours, Faster", "company": "Atria Auto", "year": 2018,
     "description": "Possessive, ego-first register against a collectivist frame.",
     "outcome_summary": "Muted launch; no recall but underperformed forecast by 22%.",
     "failure_frames": ["individualist", "status_loss"], "affected_markets": ["zh", "ko"],
     "distance": 0.171, "similarity": 0.77},
]


_BRIEF_MD = """## Executive summary

Across eight language communities the electric-sports-car launch reads as one
event but lands as four different stories. Topical overlap is uniformly high —
everyone is talking about the same car — yet the frame through which each market
absorbs it diverges sharply. Japanese- and Korean-language discourse codes the
category around craft and quiet status; the draft's freedom-and-speed register
is heard as status loss. German discourse, by contrast, reads the same line as a
straightforward engineering-performance claim and absorbs it without friction.

The single largest fault line is JA↔EN frame divergence (0.61). The watch-out:
sentiment is *not* the warning sign here — it is broadly neutral — the signal is
in the frame, which sentiment-only monitoring would miss.

## Where the markets disagree

| Pair | Situation | Frame div. | Sentiment div. |
|------|-----------|-----------:|---------------:|
| JA ↔ EN | Lens-split | 0.61 | 0.12 |
| KO ↔ EN | Lens-split | 0.49 | 0.18 |
| ZH ↔ EN | Partial    | 0.31 | 0.22 |
| DE ↔ EN | Aligned    | 0.09 | 0.07 |

## Dominant frames

- **EN** — individualist, freedom
- **JA** — craft reverence, status quo
- **KO** — status loss, individualist
- **DE** — craft, premium affirmation
- **ZH** — price anxiety, individualist

## Risk flags

1. The phrase "puts you first" maps onto a status-loss frame in JA/KO.
2. Value is never addressed; ZH price-anxiety framing is left unanswered.
3. Frame divergence, not sentiment, carries the risk — monitor accordingly.

## Recommendations

1. **Japan / Korea** — recut around heritage and craft; drop the possessive register.
2. **China** — add an explicit value proof point.
3. **Germany** — ship as drafted.

## Sources cited

Synthesized from 3,180 posts across 8 languages; representative post_ids listed below.
"""


def _brief_for(event_tag, target_languages):
    return {
        "brief_id": "mock-brief",
        "event_tag": event_tag,
        "target_languages": list(target_languages),
        "brief_markdown": _BRIEF_MD,
        "source_post_ids": [f"post_{i:05d}" for i in range(1, 13)],
        "model": "claude-4-sonnet (mock)",
    }


_TRANSLATOR = {
    "target_frame_hint": "craft_reverence",
    "variants": [
        {"frame_shift": "individualist → craft reverence",
         "text": "Engineered to be lived with. The new electric sports car, made to last.",
         "rationale": "Recenters the claim on craft and longevity, the dominant in-market frame."},
        {"frame_shift": "freedom → quiet status",
         "text": "Quietly quick. A sports car that lets the road speak first.",
         "rationale": "Trades the assertive register for restraint, aligning with status-quo coding."},
    ],
}


# ---------------------------------------------------------------------------
# DataFrame fixtures (UPPER-case columns, mirroring Snowpark .to_pandas())
# ---------------------------------------------------------------------------
def drift_events_df(limit=10):
    rows = [
        ("Velar Motors", "ja", "en", 0.402, 0.61, 0.208, "2026-05-28 06:12:00"),
        ("Northwind EV", "ko", "en", 0.351, 0.49, 0.139, "2026-05-28 02:48:00"),
    ]
    df = pd.DataFrame(rows, columns=[
        "ENTITY_NAME", "LANGUAGE_A", "LANGUAGE_B",
        "PREV_CDS", "NEW_CDS", "DELTA_CDS", "DETECTED_AT"])
    return df.head(limit)


def plcs_scores_df(limit=10):
    rows = [
        ("ja", 82, 0.86, "Live Free, Drive Fast — the new electric sports car th…", "2026-05-28 08:55:00"),
        ("ko", 71, 0.78, "Live Free, Drive Fast — the new electric sports car th…", "2026-05-28 08:55:00"),
        ("de", 34, 0.81, "Live Free, Drive Fast — the new electric sports car th…", "2026-05-28 08:55:00"),
    ]
    df = pd.DataFrame(rows, columns=[
        "TARGET_MARKET", "PLCS_SCORE", "CONFIDENCE", "DRAFT_PREVIEW", "INFERENCE_TIMESTAMP"])
    return df.head(limit)


def event_summary_df(event_tag):
    rows = [
        ("en", 1812, 0.21, "individualist"),
        ("ja", 1204, -0.08, "status_quo"),
        ("de", 964, 0.16, "craft"),
        ("ko", 712, -0.11, "status_loss"),
        ("zh", 688, 0.04, "price_anxiety"),
    ]
    return pd.DataFrame(rows, columns=[
        "DETECTED_LANGUAGE", "N_POSTS", "AVG_SENTIMENT", "DOMINANT_FRAME"])


def frame_distribution_df(event_tag):
    data = {
        "en": {"individualist": 920, "status_quo": 410, "craft": 300, "other": 182},
        "ja": {"status_quo": 560, "craft_reverence": 380, "national_pride": 160, "other": 104},
        "de": {"craft": 520, "premium_affirmation": 300, "reform_seeking": 100, "other": 44},
        "ko": {"status_loss": 360, "individualist": 220, "price_anxiety": 92, "other": 40},
        "zh": {"price_anxiety": 360, "individualist": 200, "status_loss": 88, "other": 40},
    }
    rows = [(lang, frame, n) for lang, fr in data.items() for frame, n in fr.items()]
    return pd.DataFrame(rows, columns=["DETECTED_LANGUAGE", "CULTURAL_FRAME", "N"])


def cds_matrix_df(event_tag=None):
    """Pairwise cultural divergence. UPPER-case columns, mirroring Snowpark."""
    rows = [
        ("ja", "en", 0.61, 0.61, 0.12, 0.91, "Lens-split", 0.86),
        ("ko", "en", 0.49, 0.49, 0.18, 0.88, "Lens-split", 0.80),
        ("zh", "en", 0.31, 0.31, 0.22, 0.84, "Same verdict, diff. reasons", 0.74),
        ("ja", "de", 0.44, 0.44, 0.15, 0.86, "Lens-split", 0.79),
        ("ko", "ja", 0.22, 0.22, 0.09, 0.90, "Aligned", 0.77),
        ("de", "en", 0.09, 0.09, 0.07, 0.93, "Aligned", 0.82),
        ("zh", "ja", 0.27, 0.27, 0.31, 0.81, "Mood-split", 0.71),
        ("es", "en", 0.14, 0.14, 0.10, 0.92, "Aligned", 0.75),
    ]
    return pd.DataFrame(rows, columns=[
        "LANGUAGE_A", "LANGUAGE_B", "HEADLINE_SCORE", "FRAME_DIVERGENCE",
        "SENTIMENT_DIVERGENCE", "TOPICAL_OVERLAP", "SITUATION_LABEL", "CDS_CONFIDENCE"])


def tracked_entities_df():
    rows = [
        ("e1", "Velar Motors", "brand", "cmo@velar.example", 0.15, 0.55, True, "2026-05-20 10:00:00"),
        ("e2", "Northwind EV", "brand", "brand@northwind.example", 0.15, 0.55, True, "2026-05-22 14:30:00"),
    ]
    return pd.DataFrame(rows, columns=[
        "ENTITY_ID", "ENTITY_NAME", "ENTITY_TYPE", "OWNER_EMAIL",
        "CDS_THRESHOLD_DELTA", "CDS_THRESHOLD_ABS", "ACTIVE", "CREATED_AT"])


def narrative_search_df(query, languages=None, frames=None, limit=25):
    rows = [
        {"post_id": "post_00012", "post_text": "This car forgets what driving is for.",
         "detected_language": "ja", "cultural_frame": "craft_reverence",
         "emotional_tone": "wistful", "event_tag": "ev_automotive_ev_launch",
         "sentiment_score": -0.12},
        {"post_id": "post_00031", "post_text": "Finally something that puts the driver first.",
         "detected_language": "en", "cultural_frame": "individualist",
         "emotional_tone": "enthusiastic", "event_tag": "ev_automotive_ev_launch",
         "sentiment_score": 0.44},
        {"post_id": "post_00077", "post_text": "Schöne Technik, ehrliche Leistung.",
         "detected_language": "de", "cultural_frame": "craft",
         "emotional_tone": "approving", "event_tag": "ev_automotive_ev_launch",
         "sentiment_score": 0.31},
    ]
    return pd.DataFrame(rows[:limit])


# ---------------------------------------------------------------------------
# Fake Snowpark session — covers inline session.sql() (page 4 CDS query).
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
            return _Result(df=cds_matrix_df())
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
    m.list_event_tags = lambda session: list(EVENT_TAGS)
    m.list_languages = lambda session: list(LANGUAGES)
    m.get_session_context = lambda session: {
        "Role": "NUANCE_APP_ROLE (mock)", "Warehouse": "NUANCE_DEV_WH",
        "Database": "NUANCE_DB", "Schema": "OUTPUTS", "Region": "AWS_US_WEST_2 (mock)",
        "Snowflake": "8.x (mock)", "Session ID": "mock-session-0001",
        "Last query ID": "01b-mock-query-id",
    }
    m.get_corpus_freshness = lambda session: "2026-05-28 06:12:00"
    m.get_event_summary = lambda session, event_tag: event_summary_df(event_tag)
    m.get_cds_matrix = lambda session, event_tag: cds_matrix_df(event_tag)
    m.get_frame_distribution = lambda session, event_tag: frame_distribution_df(event_tag)
    m.call_plcs = lambda session, draft_content, source_language, target_market, requested_by=None: _plcs_for(target_market)
    m.call_translator = lambda session, *a, **k: dict(_TRANSLATOR)
    m.list_tracked_entities = lambda session: tracked_entities_df()
    m.add_tracked_entity = lambda session, *a, **k: None
    m.find_matching_events = lambda session, entity_name: list(EVENT_TAGS[:2])
    m.call_find_analogs = lambda session, query_text, target_market=None, k=5: {"analogs": _ANALOGS[:k]}
    m.call_generate_brief = lambda session, event_tag, target_languages, requested_by=None: _brief_for(event_tag, target_languages)
    m.narrative_search = lambda session, query, languages=None, frames=None, limit=25: narrative_search_df(query, languages, frames, limit)
    # _sql: the Native-App object-name resolver wrapper (lib.comprenda_queries).
    # 4_Divergence_Matrix.py imports it for its inlined CDS query. In the demo there
    # is no retargeting, so it just delegates to the (fake) session — FakeSession.sql
    # returns the CDS matrix fixture for that query.
    m._sql = lambda session, text, params=None: session.sql(text, params=params)

    # Safety net (PEP 562 module __getattr__): any OTHER private helper a view might
    # import directly from lib.comprenda_queries — which this fixture fully replaces —
    # resolves to a session.sql pass-through. So adding such an import to a view can
    # never again ImportError the public demo; the worst case is a fixture-less query
    # routed through FakeSession. Public (non-underscore) names must still be defined
    # explicitly above, so a genuinely missing helper surfaces loudly.
    def _missing(name):
        # Single-underscore private helpers only. NOT dunders (__path__, __all__,
        # __spec__, …) — intercepting those breaks Python's import machinery.
        if name.startswith("_") and not name.startswith("__"):
            return lambda session, text, params=None: session.sql(text, params=params)
        raise AttributeError(
            f"module 'lib.comprenda_queries' (demo fixture) has no attribute {name!r}")
    m.__getattr__ = _missing
    return m
