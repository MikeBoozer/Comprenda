"""Narrative Search — Cortex Search-powered hybrid search over the corpus.

Consistency pass (no artboard): editorial result cards (post text + language /
frame / tone pills + sentiment) with the full table in an expander. Query logic
(narrative_search) is unchanged. Cortex SEARCH_PREVIEW returns lowercase column
names (built from JSON, not Snowpark), so columns are normalized to lowercase.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import narrative_search, list_languages
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, section_head, pill, frame_label,
)

FRAMES = [
    "individualist", "collectivist", "nationalist", "globalist",
    "threat_framing", "opportunity_framing", "historical_grievance",
    "status_quo", "reform_seeking", "spiritual_ethical", "pragmatic", "ambiguous",
]

inject_css()
session = get_active_session()

page_header(
    "Corpus intelligence · narrative search",
    "Find what communities actually said.",
    "Hybrid search across enriched content. Filter by language and cultural frame — "
    "the fast path when a stakeholder asks 'show me everything X users said about Y with a threat frame'.",
)

# ---------------------------------------------------------------------------
# Query + filters
# ---------------------------------------------------------------------------
# One st.form so (a) pressing Enter in the query box submits the search, and
# (b) the query + all filters are captured ATOMICALLY on submit — clearing a
# filter and re-submitting always re-queries with the current selection, rather
# than leaving stale results from a previous run.
st.session_state.setdefault("nsearch_q", "")
with st.form("nsearch_form", border=False):
    st.markdown("<div class='nu-kicker'>Search</div>", unsafe_allow_html=True)
    _qcol, _bcol = st.columns([3, 1], vertical_alignment="bottom")
    q = _qcol.text_input("Search query", key="nsearch_q", label_visibility="collapsed",
                         placeholder="e.g. 'product launch reaction' — press Enter or Search")
    submitted = _bcol.form_submit_button("Search", type="primary", use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='nu-kicker'>Languages</div>", unsafe_allow_html=True)
        langs = st.multiselect("Languages", options=list_languages(session),
                               label_visibility="collapsed")
    with c2:
        st.markdown("<div class='nu-kicker'>Frames</div>", unsafe_allow_html=True)
        frames = st.multiselect("Frames", options=FRAMES, format_func=frame_label,
                                label_visibility="collapsed")
    with c3:
        st.markdown("<div class='nu-kicker'>Max results</div>", unsafe_allow_html=True)
        limit = st.slider("Max results", 5, 100, 25, label_visibility="collapsed")

st.divider()

if submitted:
    if not q.strip():
        st.warning("Enter a search query.")
    else:
        with st.spinner("Searching…"):
            try:
                df = narrative_search(session, q.strip(), langs, frames, limit)
            except Exception as exc:
                st.error(f"Failed: {exc}")
                df = None
        if df is not None:
            # Always overwrite, so a new query or cleared filters replace prior results.
            st.session_state["nsearch_results"] = {"df": df, "q": q.strip()}


# ===========================================================================
# RESULTS
# ===========================================================================
def render_results(state):
    df = state["df"]
    if df is None or df.empty:
        st.info("No matches. Try broadening the query or removing filters.")
        return
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]  # normalize (real returns lower)
    n = len(df)

    st.divider()
    section_head(f"Results · {n} match{'es' if n != 1 else ''}", "What surfaced.",
                 f"Hybrid-search hits for “{state['q']}”, most relevant first.")

    for _, r in df.iterrows():
        sent = r.get("sentiment_score")
        sent_s = f"{sent:+.2f}" if isinstance(sent, (int, float)) else "—"
        chips = pill(r.get("detected_language", "?"))
        if r.get("cultural_frame"):
            chips += pill(frame_label(r["cultural_frame"]))
        if r.get("emotional_tone"):
            chips += pill(str(r["emotional_tone"]).capitalize())
        st.markdown(
            "<div class='nu-card' style='display:flex; flex-direction:column; gap:8px; "
            "margin-bottom:8px;'>"
            "<blockquote style='font:400 16px/1.55 var(--serif); color:var(--ink); "
            f"margin:0; padding:0; border:0;'>“{r.get('post_text', '')}”</blockquote>"
            "<div style='display:flex; flex-wrap:wrap; gap:4px; align-items:center;'>"
            f"{chips}"
            "<span style='margin-left:auto; font:400 11px/1 var(--mono); "
            f"color:var(--ink-muted);'>{r.get('post_id', '')} · sentiment {sent_s}</span>"
            "</div></div>", unsafe_allow_html=True)

    with st.expander("Full results table", expanded=False):
        st.dataframe(state["df"], use_container_width=True, hide_index=True)


if "nsearch_results" in st.session_state:
    render_results(st.session_state["nsearch_results"])
