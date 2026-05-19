"""Analog Retrieval — find historical campaign-launch divergence patterns
similar to your current content or event."""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.nuance_queries import call_find_analogs, list_languages

st.set_page_config(page_title="Analog Retrieval — Nuance", page_icon="🧭", layout="wide")
session = get_active_session()

st.title("🧭 Analog Retrieval")
st.caption(
    "Find historical campaign and product-launch divergence patterns that "
    "resemble your current event or content. Pattern matching is a uniquely "
    "powerful narrative device — and one no incumbent offers."
)

query = st.text_area(
    "Describe your current event or paste your draft content",
    height=120,
    max_chars=2000,
    placeholder=(
        "Example: 'Launching a US-designed luxury electric sedan in Japan, "
        "emphasizing speed and personal freedom.'"
    ),
)

languages = list_languages(session)
target_market = st.selectbox(
    "Target market (optional)",
    options=["(any)"] + languages,
    index=0,
)

k = st.slider("Number of analogs", 3, 10, 5)

if st.button("Find analogs", type="primary", disabled=(not query.strip())):
    with st.spinner("Searching analog library…"):
        try:
            r = call_find_analogs(
                session, query.strip(),
                target_market if target_market != "(any)" else None,
                k,
            )
        except Exception as exc:
            st.error(f"Failed: {exc}")
            r = None

    if r and r.get("analogs"):
        for a in r["analogs"]:
            with st.container(border=True):
                cols = st.columns([3, 1])
                cols[0].markdown(f"### {a.get('case_name', '(unknown)')}")
                cols[0].caption(f"{a.get('company', '?')} · {a.get('year', '?')}")
                if a.get("description"):
                    cols[0].markdown(a["description"])
                if a.get("outcome_summary"):
                    cols[0].markdown(f"**Outcome:** {a['outcome_summary']}")
                if a.get("failure_frames"):
                    cols[0].markdown(
                        f"**Failure frames:** {', '.join(a['failure_frames'])}"
                    )
                if a.get("affected_markets"):
                    cols[1].markdown(
                        f"**Markets:** {', '.join(a['affected_markets'])}"
                    )
                if a.get("distance") is not None:
                    cols[1].caption(f"Distance: {a['distance']:.3f}")
    elif r:
        st.info("No analogs found.")
