"""Divergence Matrix — multi-axis cultural divergence across language pairs.

How differently each language community frames the same event. Color encodes a
chosen divergence axis (frame / sentiment / topical gap); an aside reads out the
selected pair. Redesign blueprint: Claude-Code-Handoff.md §6.3, chart per §5.7.

Query logic preserved (CDS query inlined on purpose — see note below).
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd

from lib.comprenda_queries import list_event_tags
from lib.comprenda_theme import inject_css
from lib.comprenda_components import sidebar_brand, page_header, pill

st.set_page_config(page_title="Divergence Matrix — Comprenda", layout="wide")
inject_css()
sidebar_brand()

session = get_active_session()

PLACEHOLDER = "— pick an event tag —"
_WORDS = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
          6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}

# Shared oxblood ramp (§5.7). Higher = more divergent across all three axes.
_RAMP = ["#ECE6D7", "#E9E6D7", "#E5D0B6", "#D9A887", "#BF6C4B", "#8B2A1F"]
_AXES = {
    "Frame": ("headline_score", [0, 0.15, 0.25, 0.34, 0.50, 0.65], "Frame divergence"),
    "Sentiment": ("sentiment_divergence", [0, 0.10, 0.20, 0.30, 0.40, 0.50], "Sentiment divergence"),
    "Topical": ("topical_gap", [0, 0.05, 0.10, 0.15, 0.25, 0.40], "Topical gap (1 − overlap)"),
}


def _word(n):
    return _WORDS.get(n, str(n))


def _choose_event(ev):
    # Mutating a widget-keyed session_state value is only allowed from a
    # callback (runs before the next rerun instantiates the widget).
    st.session_state["matrix_event"] = ev


def _section_head(kicker, headline, dek=None):
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:680px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


def cds_band(v):
    return "risk" if v >= 0.34 else "warn" if v >= 0.23 else "safe"


_BAND_LABEL = {"risk": "High divergence", "warn": "Elevated", "safe": "Aligned"}
_SITUATION_NOTE = {
    "Lens-split": "Same event, opposing lenses. Translation alone will not bridge a "
                  "frame gap this wide — the creative needs a frame.",
    "Mood-split": "Same frame, opposite feeling. Rare, and usually a sign the event "
                  "touched different nerves in each community.",
    "Aligned": "Same lens, same mood. This pair reads the event the same way.",
}


def _note_for(situation):
    return _SITUATION_NOTE.get(
        situation, "Look behind the agreement: similar sentiment can hide different "
                   "reasoning. Read the dominant frames for each side.")


def _aside_rows(row):
    items = [
        ("Situation", row["SITUATION_LABEL"]),
        ("Frame divergence", f"{row['HEADLINE_SCORE']:.2f}"),
        ("Sentiment divergence", f"{row['SENTIMENT_DIVERGENCE']:.2f}"),
        ("Topical overlap", f"{row['TOPICAL_OVERLAP']:.2f}"),
        ("Confidence", f"{row['CDS_CONFIDENCE']:.2f}"),
    ]
    return "".join(
        "<div style='display:flex; justify-content:space-between; padding:3px 0;'>"
        f"<span style='font:400 13px var(--sans); color:var(--ink-muted);'>{label}</span>"
        f"<span style='font-family:var(--mono); font-size:13px; color:var(--ink);'>{val}</span>"
        "</div>"
        for label, val in items)


def build_heatmap(chart_df, langs, axis):
    """Layered heatmap. A base grid renders EVERY language pair as a neutral
    'not computed' cell (so the grid is a full square and hover works
    everywhere); the real colored cells layer on top. Missing pairs are NOT
    colored as 0.00 — that would falsely read as 'perfectly aligned'."""
    field, domain, legend_title = _AXES[axis]
    xenc = alt.X("language_b:N", title=None, sort=langs,
                 axis=alt.Axis(orient="top", labelAngle=0, labelFontWeight="bold",
                               labelFont="ui-monospace, SF Mono, Menlo",
                               labelFontSize=12, labelColor="#1C1A17",
                               ticks=False, domain=False))
    yenc = alt.Y("language_a:N", title=None, sort=langs,
                 axis=alt.Axis(labelFontWeight="bold",
                               labelFont="ui-monospace, SF Mono, Menlo",
                               labelFontSize=12, labelColor="#1C1A17",
                               ticks=False, domain=False))

    # Base: a cell for every (a, b) combination, neutral + "not computed".
    combos = pd.DataFrame([(a, b) for a in langs for b in langs],
                          columns=["language_a", "language_b"])
    combos["status"] = "Not computed"
    base = (
        alt.Chart(combos)
        .mark_rect(fill="#F0EBDF", stroke="#F5F1E8", strokeWidth=2)
        .encode(x=xenc, y=yenc,
                tooltip=[alt.Tooltip("language_a:N", title="A"),
                         alt.Tooltip("language_b:N", title="B"),
                         alt.Tooltip("status:N", title="")]))

    # Data: the computed pairs (+ mirror + diagonal), colored.
    data = (
        alt.Chart(chart_df)
        .mark_rect(stroke="#F5F1E8", strokeWidth=2)
        .encode(
            x=xenc, y=yenc,
            color=alt.Color(
                f"{field}:Q",
                scale=alt.Scale(domain=domain, range=_RAMP),
                legend=alt.Legend(title=legend_title, titleFontSize=11, labelFontSize=11)),
            tooltip=[
                alt.Tooltip("language_a:N", title="A"),
                alt.Tooltip("language_b:N", title="B"),
                alt.Tooltip("situation_label:N", title="Situation"),
                alt.Tooltip("headline_score:Q", title="Frame div.", format=".2f"),
                alt.Tooltip("sentiment_divergence:Q", title="Sentiment div.", format=".2f"),
                alt.Tooltip("topical_overlap:Q", title="Topical overlap", format=".2f"),
            ]))

    return (
        alt.layer(base, data)
        .properties(height=520)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
    )


# ---------------------------------------------------------------------------
# Event selection
# ---------------------------------------------------------------------------
events = list_event_tags(session)

if not events:
    page_header("Cultural divergence matrix", "Pick an event. Read the room.",
                "The matrix shows how differently each language community frames the "
                "same event. Load the demo corpus to begin.")
    st.info("No events in the corpus yet. Load demo data (see docs/03_runbook.md).")
    st.stop()

options = [PLACEHOLDER] + events
ctrl = st.columns([2, 2, 3], gap="large")
with ctrl[0]:
    st.markdown("<div class='nu-kicker'>Event</div>", unsafe_allow_html=True)
    event_sel = st.selectbox("Event", options=options, key="matrix_event",
                             label_visibility="collapsed")
with ctrl[1]:
    st.markdown("<div class='nu-kicker'>Color axis</div>", unsafe_allow_html=True)
    axis = st.radio("Color axis", list(_AXES.keys()), horizontal=True,
                    label_visibility="collapsed")
with ctrl[2]:
    st.markdown("<div class='nu-kicker'>Scale</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='display:flex; align-items:center; gap:0; margin-top:4px;'>"
        + "".join(f"<span style='width:34px; height:14px; background:{c};'></span>" for c in _RAMP)
        + "<span style='font-family:var(--mono); font-size:11px; color:var(--ink-muted);"
          " margin-left:8px;'>0.00 &nbsp;·&nbsp; 0.34 risk → &nbsp;·&nbsp; high</span></div>",
        unsafe_allow_html=True)

chosen = None if event_sel == PLACEHOLDER else event_sel


# ===========================================================================
# EMPTY / FIRST-RUN STATE — "pick an event"
# ===========================================================================
def render_empty():
    st.divider()
    e_l, e_r = st.columns([3, 2], gap="large")
    with e_l:
        _section_head("Events worth opening first", "Pre-loaded into your corpus.")
        for ev in events[:3]:
            row = st.columns([4, 1])
            row[0].markdown(
                f"<div style='font:600 14px/1.3 var(--sans); color:var(--ink-strong);'>"
                f"<span style='font-family:var(--mono);'>{ev}</span></div>"
                f"<div style='font:400 13px/1.5 var(--sans); color:var(--ink-muted);'>"
                f"Open to see how language communities frame this event.</div>",
                unsafe_allow_html=True)
            row[1].button("Open →", key=f"open_{ev}", use_container_width=True,
                          on_click=_choose_event, args=(ev,))
            st.markdown("<div style='border-bottom:1px solid var(--rule); margin:8px 0;'></div>",
                        unsafe_allow_html=True)
    with e_r:
        st.markdown(f"""
          <div class='nu-card'>
            <div class='nu-kicker'>How to read it, in two sentences</div>
            <p style='font:400 15px/1.6 var(--serif); color:var(--ink); margin:10px 0 0;'>
              Color encodes frame divergence — how differently two communities frame
              the same event. Topical overlap is high across the board, so the signal
              you care about lives in <em>how</em>, not <em>whether</em>, they're talking.
            </p>
          </div>
        """, unsafe_allow_html=True)
        st.button(f"Open {events[0]} →", type="primary", use_container_width=True,
                  on_click=_choose_event, args=(events[0],))


if chosen is None:
    page_header("Cultural divergence matrix", "Pick an event. Read the room.",
                "How differently each language community frames the same event. Color "
                "encodes frame divergence — the lens-mismatch axis. Pick an event tag "
                "above, or start with one below.")
    render_empty()
    st.stop()


# ===========================================================================
# POPULATED STATE
# ===========================================================================
# NOTE: CDS query inlined (not via lib.get_cds_matrix) on purpose. SiS re-executes
# page files every run but caches imported lib modules on a warm container, so a lib
# change can stay stale after deploy until cold-start. Inlining keeps this page
# correct on the next rerun. (lib.get_cds_matrix holds the same query server-side.)
df = session.sql(
    "SELECT language_a, language_b, headline_score, frame_divergence, "
    "       sentiment_divergence, topical_overlap, situation_label, cds_confidence "
    "FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES "
    "WHERE event_tag = ? AND frame_divergence IS NOT NULL "
    "QUALIFY ROW_NUMBER() OVER (PARTITION BY language_a, language_b "
    "                           ORDER BY computed_at DESC) = 1 "
    "ORDER BY headline_score DESC",
    params=[chosen],
).to_pandas()

n_langs = len(set(df["LANGUAGE_A"]) | set(df["LANGUAGE_B"])) if not df.empty else 0
n_faults = int((df["HEADLINE_SCORE"] >= 0.34).sum()) if not df.empty else 0

page_header(
    f"Cultural divergence matrix · {chosen}",
    (f"{_word(n_langs)} languages, one event, "
     f"{_word(n_faults).lower() if n_faults == 0 else _word(n_faults)} "
     f"fault line{'s' if n_faults != 1 else ''}.") if not df.empty
    else "No divergence profile yet.",
    "How differently each language community frames this event. Color encodes the "
    "selected axis; topical overlap is high across the board, so the signal lives "
    "in how each community frames it." if not df.empty
    else f"No computed divergence for {chosen}. Run snowflake/07_cds_computation.sql.")

if df.empty:
    st.info(f"No divergence profile yet for `{chosen}`.")
    st.stop()

st.divider()

# Mirror (axes are symmetric) + zero diagonal so the grid is a full square.
mirror = df.rename(columns={"LANGUAGE_A": "LANGUAGE_B", "LANGUAGE_B": "LANGUAGE_A"})
langs = sorted(set(df["LANGUAGE_A"]) | set(df["LANGUAGE_B"]))
diag = pd.DataFrame({
    "LANGUAGE_A": langs, "LANGUAGE_B": langs,
    "HEADLINE_SCORE": 0.0, "FRAME_DIVERGENCE": 0.0, "SENTIMENT_DIVERGENCE": 0.0,
    "TOPICAL_OVERLAP": 1.0, "SITUATION_LABEL": "—", "CDS_CONFIDENCE": 1.0,
})
full = pd.concat([df, mirror, diag], ignore_index=True)
chart_df = full.rename(columns=str.lower)
chart_df["topical_gap"] = 1.0 - chart_df["topical_overlap"]

# --- Heatmap + aside -------------------------------------------------------
grid_col, aside_col = st.columns([5, 2], gap="large")

with grid_col:
    st.altair_chart(build_heatmap(chart_df, langs, axis), use_container_width=True)

with aside_col:
    # Pair selection (reliable across SiS Streamlit versions; replaces the
    # artboard's click-a-cell interaction — see IMPLEMENTATION_NOTES §4).
    pair_labels = [f"{r['LANGUAGE_A']} ⇄ {r['LANGUAGE_B']}" for _, r in df.iterrows()]
    sel_label = st.selectbox("Selected pair", options=pair_labels)
    sel_idx = pair_labels.index(sel_label)
    row = df.iloc[sel_idx]

    fd = float(row["HEADLINE_SCORE"])
    band = cds_band(fd)
    st.markdown(f"""
      <div class='nu-card' style='border-top:3px solid var(--{band});'>
        <div class='nu-kicker'>Selected · {row['LANGUAGE_A']} ⇄ {row['LANGUAGE_B']}</div>
        <div class='nu-score-n nu-score-n--{band}' style='font-size:56px;'>{fd:.2f}</div>
        <div>{pill(_BAND_LABEL[band], band)}</div>
        <div style='border-bottom:1px solid var(--rule); margin:12px 0;'></div>
        {_aside_rows(row)}
        <div style='border-bottom:1px solid var(--rule); margin:12px 0;'></div>
        <p style='font:400 14px/1.55 var(--serif); color:var(--ink);'>{_note_for(row['SITUATION_LABEL'])}</p>
      </div>
    """, unsafe_allow_html=True)
    if st.button("Open in event explorer →", type="primary", use_container_width=True):
        st.session_state["explorer_event"] = chosen
        st.switch_page("pages/3_Event_Explorer.py")

st.divider()

# --- Reading the matrix ----------------------------------------------------
_section_head("Reading the matrix", "Four ways a pair can land.")
read = st.columns(4, gap="medium")
for col, (h, p) in zip(read, [
    ("Aligned", "Same lens, same mood. Below 0.15."),
    ("Lens-split", "Same words, different frame."),
    ("Mood-split", "Same frame, opposite feeling. Rare."),
    ("Same verdict, different reasons", "Different framing, similar feeling. Look behind the agreement."),
]):
    col.markdown(
        f"<h3>{h}</h3><p style='font:400 13px/1.5 var(--sans); color:var(--ink-muted);'>{p}</p>",
        unsafe_allow_html=True)
