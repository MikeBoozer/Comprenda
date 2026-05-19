"""Divergence Matrix — CDS heatmap across language pairs for an event."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import plotly.express as px
import pandas as pd

from lib.nuance_queries import list_event_tags, get_cds_matrix

st.set_page_config(page_title="Divergence Matrix — Nuance", page_icon="🔥", layout="wide")
session = get_active_session()

st.title("🔥 Cultural Divergence Matrix")
st.caption(
    "Heatmap of Cultural Divergence Score (CDS) between language communities "
    "for a selected event. Darker red = more culturally divergent."
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first.")
    st.stop()

event_tag = st.selectbox("Event", options=events)
df = get_cds_matrix(session, event_tag)

if df.empty:
    st.info(f"No CDS yet for `{event_tag}`. Run snowflake/07_cds_computation.sql.")
    st.stop()

# Mirror the matrix (CDS is symmetric)
mirror = df.rename(columns={"LANGUAGE_A": "LANGUAGE_B", "LANGUAGE_B": "LANGUAGE_A"})
full = pd.concat([df, mirror], ignore_index=True)

# Pivot into a square matrix
pivot = full.pivot_table(
    index="LANGUAGE_A", columns="LANGUAGE_B",
    values="CDS_SCORE", aggfunc="mean",
).fillna(0)

fig = px.imshow(
    pivot, color_continuous_scale="Reds", aspect="equal",
    labels={"x": "Language B", "y": "Language A", "color": "CDS"},
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top divergences (sorted)")
st.dataframe(
    df.sort_values("CDS_SCORE", ascending=False).head(20),
    use_container_width=True, hide_index=True,
)

# Confidence note
st.caption(
    "💡 CDS values >0.55 are significant cultural risk signals. "
    "Values 0.35-0.55 indicate meaningful divergence worth investigating. "
    "Below 0.35 = communities are interpreting the event similarly."
)
