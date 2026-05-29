"""Event Explorer — overview map and summary stats for a selected event_tag.

Consistency pass (no artboard): the body is restyled into the editorial design
language — KPI strip, section heads, frame pills — reusing comprenda_components.
Query logic (list_event_tags / get_event_summary) is unchanged.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt

from lib.comprenda_queries import list_event_tags, get_event_summary
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, section_head, kpi, pill, frame_label,
)

inject_css()
session = get_active_session()

page_header(
    "Event intelligence · corpus overview",
    "See how each market reacted.",
    "Pick an event. Sentiment, dominant frame, and post volume — by language community.",
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first (see `docs/03_runbook.md`).")
    st.stop()

st.markdown("<div class='nu-kicker'>Event</div>", unsafe_allow_html=True)
_evcol, _ = st.columns([1, 2])
event_tag = _evcol.selectbox("Event", options=events, label_visibility="collapsed")

summary = get_event_summary(session, event_tag)
if summary.empty:
    st.info(f"No enriched data for event `{event_tag}` yet. Did frame classification run?")
    st.stop()

# ---------------------------------------------------------------------------
# KPI strip — honest aggregations of the per-market summary (no invented data).
# ---------------------------------------------------------------------------
n_markets = len(summary)
total_posts = int(summary["N_POSTS"].sum())
weighted_sent = (float((summary["N_POSTS"] * summary["AVG_SENTIMENT"]).sum() / total_posts)
                 if total_posts else 0.0)
spread = float(summary["AVG_SENTIMENT"].max() - summary["AVG_SENTIMENT"].min())

st.divider()
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("Markets", n_markets)
with k2:
    kpi("Posts", f"{total_posts:,}")
with k3:
    kpi("Avg sentiment", f"{weighted_sent:+.2f}")
with k4:
    kpi("Sentiment spread", f"{spread:.2f}")

st.divider()

# ---------------------------------------------------------------------------
# Sentiment by market
# ---------------------------------------------------------------------------
section_head("Sentiment · by market", "Where the mood splits.",
             "Average sentiment per language community, on a −1 to +1 scale.")
chart = (
    alt.Chart(summary)
    .mark_bar()
    .encode(
        x=alt.X("DETECTED_LANGUAGE:N", title="Market", sort="-y"),
        y=alt.Y("AVG_SENTIMENT:Q", title="Avg sentiment",
                scale=alt.Scale(domain=[-1, 1])),
        color=alt.Color(
            "AVG_SENTIMENT:Q",
            scale=alt.Scale(scheme="redyellowgreen", domain=[-1, 1]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("DETECTED_LANGUAGE:N", title="Market"),
            alt.Tooltip("AVG_SENTIMENT:Q", title="Avg sentiment", format=".3f"),
            alt.Tooltip("N_POSTS:Q", title="Posts"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Dominant frame by market
# ---------------------------------------------------------------------------
section_head("Dominant frame · by market", "The lens each community used.")
rows_html = ""
for _, r in summary.iterrows():
    rows_html += (
        "<div style='display:flex; align-items:center; gap:14px; padding:11px 0; "
        "border-bottom:1px solid var(--rule);'>"
        f"<span style='font:600 14px/1 var(--sans); color:var(--ink-strong); "
        f"min-width:44px;'>{r['DETECTED_LANGUAGE']}</span>"
        f"{pill(frame_label(r['DOMINANT_FRAME']))}"
        f"<span style='margin-left:auto; font:400 11px/1 var(--mono); "
        f"color:var(--ink-muted);'>{int(r['N_POSTS']):,} posts</span>"
        "</div>")
st.markdown(rows_html, unsafe_allow_html=True)

with st.expander("Full summary table", expanded=False):
    st.dataframe(summary, use_container_width=True, hide_index=True)
