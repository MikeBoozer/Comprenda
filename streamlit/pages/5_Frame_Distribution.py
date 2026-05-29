"""Frame Distribution — side-by-side cultural frame breakdown per language."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt

from lib.comprenda_queries import list_event_tags, get_frame_distribution
from lib.comprenda_theme import inject_css
from lib.comprenda_components import sidebar_brand, page_header

st.set_page_config(page_title="Frame Distribution — Comprenda", page_icon="🎯", layout="wide")
inject_css()
sidebar_brand()
session = get_active_session()

page_header(
    "Frame analysis · taxonomy breakdown",
    "Who's framing it, and how.",
    "Side-by-side % distribution across the 12-category cultural frame taxonomy. "
    "The single fastest way to see ideological fault lines.",
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first.")
    st.stop()

event_tag = st.selectbox("Event", options=events)
df = get_frame_distribution(session, event_tag)

if df.empty:
    st.info(f"No frames yet for `{event_tag}`. Run snowflake/06_frame_classification.sql.")
    st.stop()

# Compute % within each language
totals = df.groupby("DETECTED_LANGUAGE")["N"].transform("sum")
df["PCT"] = (df["N"] / totals * 100).round(1)

chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("CULTURAL_FRAME:N", title="Frame", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("PCT:Q", title="% of posts"),
        color=alt.Color("CULTURAL_FRAME:N", legend=None),
        tooltip=[
            alt.Tooltip("DETECTED_LANGUAGE:N", title="Language"),
            alt.Tooltip("CULTURAL_FRAME:N", title="Frame"),
            alt.Tooltip("PCT:Q", title="% of posts"),
            alt.Tooltip("N:Q", title="Count"),
        ],
    )
    .properties(width=180, height=180)
    .facet(facet=alt.Facet("DETECTED_LANGUAGE:N", title=None), columns=3)
)
st.altair_chart(chart, use_container_width=True)

st.divider()
st.subheader("Raw counts")
st.dataframe(df, use_container_width=True, hide_index=True)
