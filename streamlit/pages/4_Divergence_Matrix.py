"""Divergence Matrix — multi-axis cultural divergence across language pairs for an event."""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd

from lib.nuance_queries import list_event_tags

st.set_page_config(page_title="Divergence Matrix — Nuance", page_icon="🔥", layout="wide")
session = get_active_session()

st.title("🔥 Cultural Divergence Matrix")
st.caption(
    "How differently language communities **frame** the same event. Color = frame "
    "divergence (the headline signal); the table breaks each pair into three axes — "
    "topical overlap, frame divergence, and sentiment divergence."
)

events = list_event_tags(session)
if not events:
    st.warning("No events found. Load demo data first.")
    st.stop()

event_tag = st.selectbox("Event", options=events)

# NOTE: query inlined here (not via lib.get_cds_matrix) on purpose. Streamlit-in-
# Snowflake re-executes page files every run but caches imported lib modules on a
# warm container, so a lib change can stay stale after a deploy until the container
# cold-starts. Inlining keeps this page correct on the next rerun. (lib.get_cds_matrix
# holds the same query for non-SiS / server-side use.)
df = session.sql(
    "SELECT language_a, language_b, headline_score, frame_divergence, "
    "       sentiment_divergence, topical_overlap, situation_label, cds_confidence "
    "FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES "
    "WHERE event_tag = ? AND frame_divergence IS NOT NULL "
    "QUALIFY ROW_NUMBER() OVER (PARTITION BY language_a, language_b "
    "                           ORDER BY computed_at DESC) = 1 "
    "ORDER BY headline_score DESC",
    params=[event_tag],
).to_pandas()

if df.empty:
    st.info(f"No divergence profile yet for `{event_tag}`. Run snowflake/07_cds_computation.sql.")
    st.stop()

# Mirror (all axes are symmetric) and add a zero diagonal so the grid is a full square.
mirror = df.rename(columns={"LANGUAGE_A": "LANGUAGE_B", "LANGUAGE_B": "LANGUAGE_A"})
langs = sorted(set(df["LANGUAGE_A"]) | set(df["LANGUAGE_B"]))
diag = pd.DataFrame({
    "LANGUAGE_A": langs, "LANGUAGE_B": langs,
    "HEADLINE_SCORE": 0.0, "FRAME_DIVERGENCE": 0.0,
    "SENTIMENT_DIVERGENCE": 0.0, "TOPICAL_OVERLAP": 1.0,
    "SITUATION_LABEL": "—",
})
full = pd.concat([df, mirror, diag], ignore_index=True)

heatmap = (
    alt.Chart(full)
    .mark_rect()
    .encode(
        x=alt.X("LANGUAGE_B:N", title="Language B"),
        y=alt.Y("LANGUAGE_A:N", title="Language A"),
        color=alt.Color("HEADLINE_SCORE:Q", scale=alt.Scale(scheme="reds"),
                        title="Frame divergence"),
        tooltip=[
            alt.Tooltip("LANGUAGE_A:N", title="Language A"),
            alt.Tooltip("LANGUAGE_B:N", title="Language B"),
            alt.Tooltip("SITUATION_LABEL:N", title="Situation"),
            alt.Tooltip("FRAME_DIVERGENCE:Q", title="Frame divergence", format=".3f"),
            alt.Tooltip("SENTIMENT_DIVERGENCE:Q", title="Sentiment divergence", format=".3f"),
            alt.Tooltip("TOPICAL_OVERLAP:Q", title="Topical overlap", format=".3f"),
        ],
    )
    .properties(height=600)
)
st.altair_chart(heatmap, use_container_width=True)

st.subheader("Divergence profile by language pair")
table = df.rename(columns={
    "LANGUAGE_A": "Lang A", "LANGUAGE_B": "Lang B",
    "FRAME_DIVERGENCE": "Frame div", "SENTIMENT_DIVERGENCE": "Sentiment div",
    "TOPICAL_OVERLAP": "Topical overlap", "SITUATION_LABEL": "Situation",
})[["Lang A", "Lang B", "Situation", "Frame div", "Sentiment div", "Topical overlap"]]
st.dataframe(
    table.sort_values("Frame div", ascending=False).head(25),
    use_container_width=True, hide_index=True,
)

st.caption(
    "**Reading it:** topical overlap is high across the board — every community is "
    "discussing the same event, so the cultural signal lives in the other two axes. "
    "**Frame divergence ≥ 0.23** = meaningfully different framing; **≥ 0.34** = cultural "
    "risk. **Situations:** *Aligned* (same lens, same mood) · *Divergent* (different lens "
    "and mood) · *Shared lens, split mood* (same framing, opposite feeling) · "
    "*Same verdict, different reasons* (different framing, similar feeling)."
)
