"""Cultural Translator — produces frame-preserving content adaptations per market."""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import call_translator, list_languages

st.set_page_config(page_title="Cultural Translator — Nuance", page_icon="🌍", layout="wide")
session = get_active_session()

st.title("🌍 Cultural Translator")
st.caption(
    "Beyond translation. Produces culturally-adapted variants that preserve "
    "intent but shift cultural frame — ready to drop into your marketing workflow."
)

# Pre-fill from PLCS page if available
prefill = st.session_state.get("translator_prefill", "")
prefill_markets = st.session_state.get("translator_target_markets", [])

left, right = st.columns([2, 1])

with left:
    source_content = st.text_area("Source content", value=prefill, height=160, max_chars=2000)

with right:
    languages = list_languages(session)
    source_language = st.selectbox(
        "Source language", options=languages,
        index=languages.index("en") if "en" in languages else 0,
    )
    target_market = st.selectbox(
        "Target market",
        options=languages,
        index=languages.index(prefill_markets[0]) if prefill_markets and prefill_markets[0] in languages else 0,
    )

    frame_override = st.selectbox(
        "Target frame (optional override)",
        options=["(auto-detect dominant)", "individualist", "collectivist",
                 "nationalist", "globalist", "threat_framing", "opportunity_framing",
                 "historical_grievance", "status_quo", "reform_seeking",
                 "spiritual_ethical", "pragmatic"],
        index=0,
    )

st.divider()

if st.button("Generate adapted variants", type="primary",
             disabled=(not source_content.strip())):
    with st.spinner("Generating culturally-adapted variants…"):
        try:
            r = call_translator(
                session, source_content.strip(), source_language, target_market,
                target_frame_hint=None if frame_override.startswith("(") else frame_override,
                requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"),
            )
        except Exception as exc:
            st.error(f"Failed: {exc}")
            r = None

    if r:
        st.subheader(f"Adapted variants for {target_market}")
        st.caption(f"Target frame: **{r.get('target_frame_hint')}**")
        for i, v in enumerate(r.get("variants", []), start=1):
            with st.container(border=True):
                st.markdown(f"**Variant {i}** — *{v.get('frame_shift', '?')}*")
                st.code(v.get("text", "(no text)"), language=None)
                st.caption(v.get("rationale", ""))
