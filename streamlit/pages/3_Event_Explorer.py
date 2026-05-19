"""Event Explorer — overview map and summary stats for a selected event_tag."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import plotly.express as px

from lib.nuance_queries import list_event_tags, get_event_summary

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
    fig = px.bar(
        summary,
        x="DETECTED_LANGUAGE", y="AVG_SENTIMENT",
        color="AVG_SENTIMENT",
        color_continuous_scale="RdYlGn", range_color=[-1, 1],
        labels={"DETECTED_LANGUAGE": "Language", "AVG_SENTIMENT": "Avg sentiment"},
    )
    fig.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Dominant frame breakdown
st.subheader("Dominant cultural frame per language")
st.dataframe(
    summary[["DETECTED_LANGUAGE", "DOMINANT_FRAME", "N_POSTS"]],
    use_container_width=True, hide_index=True,
)
