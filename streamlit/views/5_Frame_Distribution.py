"""Frame Distribution — side-by-side cultural frame breakdown per language.

Consistency pass (no artboard): leads with the editorial frame_share_bar
component (one stacked bar per market) instead of a bare facet chart; the
original chart and raw counts move into expanders. Query logic unchanged.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt

from lib.comprenda_queries import list_event_tags, get_frame_distribution
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, section_head, frame_share_bar,
)

inject_css()
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

st.markdown("<div class='nu-kicker'>Event</div>", unsafe_allow_html=True)
_evcol, _ = st.columns([1, 2])
event_tag = _evcol.selectbox("Event", options=events, label_visibility="collapsed")
df = get_frame_distribution(session, event_tag)

if df.empty:
    st.info(f"No frames yet for `{event_tag}`. Run snowflake/06_frame_classification.sql.")
    st.stop()

# Compute % within each language
totals = df.groupby("DETECTED_LANGUAGE")["N"].transform("sum")
df["PCT"] = (df["N"] / totals * 100).round(1)

st.divider()

# ---------------------------------------------------------------------------
# Frame mix per market — the editorial stacked bars (markets ordered by volume).
# ---------------------------------------------------------------------------
section_head(
    "Frame mix · by market", "How the story splits, community by community.",
    "Each bar is one market's distribution across the cultural-frame taxonomy. "
    "A long leading segment means one frame dominates; an even bar means a "
    "contested narrative.")

order = (df.groupby("DETECTED_LANGUAGE")["N"].sum()
         .sort_values(ascending=False).index)
for lang in order:
    sub = df[df["DETECTED_LANGUAGE"] == lang].sort_values("N", ascending=False)
    tot = sub["N"].sum()
    shares = {row["CULTURAL_FRAME"]: (row["N"] / tot) for _, row in sub.iterrows()}
    frame_share_bar(lang, shares)

st.divider()

# ---------------------------------------------------------------------------
# Detail — the per-frame facet chart and raw counts, on demand.
# ---------------------------------------------------------------------------
with st.expander("Per-frame detail (chart)", expanded=False):
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

with st.expander("Raw counts", expanded=False):
    st.dataframe(df, use_container_width=True, hide_index=True)
