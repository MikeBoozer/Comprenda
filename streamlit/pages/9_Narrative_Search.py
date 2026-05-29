"""Narrative Search — Cortex Search-powered hybrid search over the corpus."""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import narrative_search, list_languages
from lib.comprenda_theme import inject_css
from lib.comprenda_components import sidebar_brand, page_header

FRAMES = [
    "individualist", "collectivist", "nationalist", "globalist",
    "threat_framing", "opportunity_framing", "historical_grievance",
    "status_quo", "reform_seeking", "spiritual_ethical", "pragmatic", "ambiguous",
]

st.set_page_config(page_title="Narrative Search — Comprenda", page_icon="🔍", layout="wide")
inject_css()
sidebar_brand()
session = get_active_session()

page_header(
    "Corpus intelligence · narrative search",
    "Find what communities actually said.",
    "Hybrid search across enriched content. Filter by language and cultural frame — "
    "the fast path when a stakeholder asks 'show me everything X users said about Y with a threat frame'.",
)

q = st.text_input("Search query", placeholder="e.g. 'product launch reaction'")

c1, c2, c3 = st.columns(3)
langs = c1.multiselect("Languages", options=list_languages(session))
frames = c2.multiselect("Frames", options=FRAMES)
limit = c3.slider("Max results", 5, 100, 25)

if st.button("Search", type="primary", disabled=(not q.strip())):
    with st.spinner("Searching…"):
        df = narrative_search(session, q.strip(), langs, frames, limit)
    if df.empty:
        st.info("No matches.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
