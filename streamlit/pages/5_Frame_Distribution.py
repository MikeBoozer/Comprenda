"""Frame Distribution — side-by-side cultural frame breakdown per language."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import plotly.express as px

from lib.nuance_queries import list_event_tags, get_frame_distribution

st.set_page_config(page_title="Frame Distribution — Nuance", page_icon="🎯", layout="wide")
session = get_active_session()

st.title("🎯 Cultural Frame Distribution")
st.caption(
    "How does each language community frame this event? The bar charts below "
    "show the % distribution across the 12-category cultural frame taxonomy."
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

fig = px.bar(
    df, x="CULTURAL_FRAME", y="PCT",
    color="CULTURAL_FRAME",
    facet_col="DETECTED_LANGUAGE",
    facet_col_wrap=3,
    labels={"PCT": "% of posts", "CULTURAL_FRAME": "Frame"},
)
fig.update_layout(height=200 * (df["DETECTED_LANGUAGE"].nunique() // 3 + 1),
                  showlegend=False)
fig.update_xaxes(tickangle=45)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Raw counts")
st.dataframe(df, use_container_width=True, hide_index=True)
