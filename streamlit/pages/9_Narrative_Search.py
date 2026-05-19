"""Narrative Search — Cortex Search-powered hybrid search over the corpus."""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.nuance_queries import narrative_search, list_languages

FRAMES = [
    "individualist", "collectivist", "nationalist", "globalist",
    "threat_framing", "opportunity_framing", "historical_grievance",
    "status_quo", "reform_seeking", "spiritual_ethical", "pragmatic", "ambiguous",
]

st.set_page_config(page_title="Narrative Search — Nuance", page_icon="🔍", layout="wide")
session = get_active_session()

st.title("🔍 Narrative Search")
st.caption(
    "Search across all enriched content. Filters: language, cultural frame. "
    "Useful for ad-hoc investigation when a stakeholder asks "
    "'show me everything Japanese users said about X with a threat frame'."
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
