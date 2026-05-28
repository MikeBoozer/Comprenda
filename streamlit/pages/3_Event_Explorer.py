"""Event Explorer — overview map and summary stats for a selected event_tag."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt

from lib.comprenda_queries import list_event_tags, get_event_summary

st.set_page_config(page_title="Event Explorer — Nuance", page_icon="🗺️", layout="wide")
session = get_active_session()

st.title("🗺️ Event Explorer")
st.caption(
    "Pick an event. See how each language community reacted — sentiment, "
    "dominant frame, post volume."
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first (see docs/03_runbook.md).")
    st.stop()

event_tag = st.selectbox("Event", options=events)

summary = get_event_summary(session, event_tag)

if summary.empty:
    st.info(f"No enriched data for event `{event_tag}` yet. Did frame classification run?")
    st.stop()

left, right = st.columns(2)

with left:
    st.subheader("By language")
    st.dataframe(summary, use_container_width=True, hide_index=True)

with right:
    st.subheader("Sentiment distribution")
    chart = (
        alt.Chart(summary)
        .mark_bar()
        .encode(
            x=alt.X("DETECTED_LANGUAGE:N", title="Language", sort="-y"),
            y=alt.Y("AVG_SENTIMENT:Q", title="Avg sentiment",
                    scale=alt.Scale(domain=[-1, 1])),
            color=alt.Color(
                "AVG_SENTIMENT:Q",
                scale=alt.Scale(scheme="redyellowgreen", domain=[-1, 1]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("DETECTED_LANGUAGE:N", title="Language"),
                alt.Tooltip("AVG_SENTIMENT:Q", title="Avg sentiment", format=".3f"),
                alt.Tooltip("N_POSTS:Q", title="Posts"),
            ],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)

st.divider()

# Dominant frame breakdown
st.subheader("Dominant cultural frame per language")
st.dataframe(
    summary[["DETECTED_LANGUAGE", "DOMINANT_FRAME", "N_POSTS"]],
    use_container_width=True, hide_index=True,
)
