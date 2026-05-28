"""AI Cultural Brief Generator — one-click 2-page Markdown brief."""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import list_event_tags, list_languages, call_generate_brief

st.set_page_config(page_title="AI Brief — Nuance", page_icon="📄", layout="wide")
session = get_active_session()

st.title("📄 AI Cultural Intelligence Brief")
st.caption(
    "One-click 2-page brief: executive summary, key divergences, dominant frames, "
    "risk flags, and messaging recommendations. Source-cited and exportable."
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first (see docs/03_runbook.md).")
    st.stop()

languages = list_languages(session)

c1, c2 = st.columns([1, 2])

event_tag = c1.selectbox("Event", options=events)
target_langs = c2.multiselect(
    "Target languages",
    options=languages,
    default=[l for l in ["en", "ja", "zh", "de", "es"] if l in languages][:5],
)

if st.button("Generate brief", type="primary", use_container_width=True,
             disabled=(not target_langs)):
    with st.spinner("Synthesizing brief (claude-4-sonnet)…"):
        try:
            r = call_generate_brief(
                session, event_tag, target_langs,
                requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"),
            )
        except Exception as exc:
            st.error(f"Failed: {exc}")
            r = None

    if r:
        st.markdown(r.get("brief_markdown", "(empty)"))

        st.divider()
        with st.expander("Sources cited (post_ids)"):
            st.json(r.get("source_post_ids", []))

        st.download_button(
            label="Download as Markdown",
            data=r.get("brief_markdown", "").encode("utf-8"),
            file_name=f"nuance_brief_{event_tag}.md",
            mime="text/markdown",
        )
