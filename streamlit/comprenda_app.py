"""
Nuance — Cultural Intelligence Platform
Main entry / home dashboard.

Streamlit-in-Snowflake app. Run via Snowflake → Projects → Streamlit.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

from lib.comprenda_queries import (
    get_recent_drift_events,
    get_recent_plcs_scores,
    get_kpi_summary,
)

st.set_page_config(
    page_title="Nuance — Cultural Intelligence",
    page_icon="🌐",
    layout="wide",
)

session = get_active_session()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("# 🌐")
with col_title:
    st.title("Nuance")
    st.caption("Cultural intelligence for the AI era. Don't translate — understand.")

st.divider()

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
kpis = get_kpi_summary(session)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Events tracked", kpis["events"])
k2.metric("Languages analyzed", kpis["languages"])
k3.metric("Posts in corpus", f"{kpis['posts']:,}")
k4.metric("Drift events (24h)", kpis["drift_24h"])

st.divider()

# ---------------------------------------------------------------------------
# Recent activity
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("🔔 Recent drift alerts")
    drift = get_recent_drift_events(session, limit=8)
    if drift.empty:
        st.info("No drift events yet. Subscribe an entity in the **Drift Alerts** page.")
    else:
        st.dataframe(drift, use_container_width=True, hide_index=True)

with right:
    st.subheader("⚠️ Recent Pre-Launch Risk scores")
    plcs = get_recent_plcs_scores(session, limit=8)
    if plcs.empty:
        st.info("No PLCS runs yet. Try one in the **Pre-Launch Risk** page.")
    else:
        st.dataframe(plcs, use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Navigation hint
# ---------------------------------------------------------------------------
st.markdown(
    "### Where to go next\n"
    "- **Pre-Launch Risk** — score a draft tagline or ad copy before launch.\n"
    "- **Event Explorer** — explore a launched event across language communities.\n"
    "- **Cultural Translator** — adapt content for a target market.\n"
    "- **Divergence Matrix** — see the heatmap of cultural divergence.\n"
    "- **AI Brief** — one-click 2-page cultural intelligence report.\n"
    "- **Drift Alerts** — subscribe to ongoing monitoring."
)
