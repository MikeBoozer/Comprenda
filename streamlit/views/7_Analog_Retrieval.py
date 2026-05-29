"""Analog Retrieval — find historical campaign-launch divergence patterns
similar to your current content or event.

Consistency pass (no artboard): PLCS-style input zone + editorial analog cards
(case name, outcome callout, failure-frame / market pills), results persisted
across reruns. Query logic (call_find_analogs) is unchanged.
"""
import json

import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import call_find_analogs, list_languages
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, section_head, pill, frame_label,
)


def _as_list(v):
    """FIND_ANALOGS returns failure_frames / affected_markets as JSON-encoded
    strings on the live app (real lists in the harness). Coerce to a list so the
    pills render per item, not per character."""
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else [v]
        except (ValueError, TypeError):
            return [v]
    return v or []


inject_css()
session = get_active_session()

page_header(
    "Pattern intelligence · historical analogs",
    "What happened last time.",
    "Find historical divergence patterns that resemble your current event or content. "
    "Nameable precedents your stakeholders can act on.",
)

SAMPLE_Q = ("Launching a US-designed luxury electric sedan in Japan, "
            "emphasizing speed and personal freedom.")


def _use_sample_q():
    # Widget-keyed mutation must happen in a callback (Streamlit constraint).
    st.session_state["analog_query"] = SAMPLE_Q


st.session_state.setdefault("analog_query", "")

# ---------------------------------------------------------------------------
# Input zone
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1], gap="large")
with left:
    st.markdown("<div class='nu-kicker'>Describe your event or draft</div>",
                unsafe_allow_html=True)
    query = st.text_area(
        "Query", key="analog_query", height=140, max_chars=2000,
        label_visibility="collapsed",
        placeholder="Example: 'Launching a US-designed luxury electric sedan in "
                    "Japan, emphasizing speed and personal freedom.'")
    meta_l, meta_r = st.columns([3, 1])
    meta_l.markdown(
        f"<span style='font-family:var(--mono); font-size:11px; color:var(--ink-faint);'>"
        f"{len(query)} / 2,000</span>", unsafe_allow_html=True)
    meta_r.button("Try an example →", use_container_width=True, on_click=_use_sample_q)

with right:
    languages = list_languages(session)
    st.markdown("<div class='nu-kicker'>Target market</div>", unsafe_allow_html=True)
    target_market = st.selectbox(
        "Target market", options=["(any)"] + languages, index=0,
        label_visibility="collapsed")
    st.markdown("<div class='nu-kicker' style='margin-top:8px;'>How many</div>",
                unsafe_allow_html=True)
    k = st.slider("Number of analogs", 3, 10, 5, label_visibility="collapsed")

st.divider()
find = st.button("Find analogs", type="primary", use_container_width=True,
                 disabled=(not query.strip()))

if find:
    with st.spinner("Searching analog library…"):
        try:
            r = call_find_analogs(
                session, query.strip(),
                target_market if target_market != "(any)" else None, k)
        except Exception as exc:
            st.error(f"Failed: {exc}")
            r = None
    if r is not None:
        st.session_state["analog_results"] = {"r": r, "query": query.strip()}


# ===========================================================================
# RESULTS
# ===========================================================================
def render_analogs(state):
    r = state["r"]
    analogs = r.get("analogs", []) if r else []
    if not analogs:
        st.info("No analogs found in the corpus for this description. "
                "Try a broader description, or drop the target-market filter.")
        return
    st.divider()
    section_head(
        f"Precedent · {len(analogs)} analog{'s' if len(analogs) != 1 else ''}",
        "What history shows.",
        "Historical launches whose divergence pattern resembles your "
        "description, closest first.")

    for a in analogs:
        dist = a.get("distance")
        dist_s = f"gap {dist:.3f}" if isinstance(dist, (int, float)) else ""
        desc_html = (f"<p style='font:400 15px/1.6 var(--serif); color:var(--ink); "
                     f"margin:0;'>{a['description']}</p>" if a.get("description") else "")
        outcome_html = (
            "<div style='border-left:3px solid var(--rule-strong); padding:4px 0 4px 12px;'>"
            "<span style='font:600 10px/1.4 var(--sans); text-transform:uppercase; "
            "letter-spacing:0.08em; color:var(--ink-muted);'>Outcome</span>"
            f"<div style='font:400 14px/1.5 var(--serif); color:var(--ink);'>"
            f"{a['outcome_summary']}</div></div>" if a.get("outcome_summary") else "")
        fail = "".join(pill(frame_label(f), tone="warn")
                       for f in _as_list(a.get("failure_frames")))
        mkts = "".join(pill(m) for m in _as_list(a.get("affected_markets")))
        fail_html = (
            "<div style='display:flex; flex-wrap:wrap; gap:4px; align-items:center;'>"
            "<span style='font:400 11px/1 var(--mono); color:var(--ink-faint); "
            f"margin-right:4px;'>Failure frames</span>{fail}</div>" if fail else "")
        mkts_html = (
            "<div style='display:flex; flex-wrap:wrap; gap:4px; align-items:center;'>"
            "<span style='font:400 11px/1 var(--mono); color:var(--ink-faint); "
            f"margin-right:4px;'>Affected markets</span>{mkts}</div>" if mkts else "")
        st.markdown(
            "<div class='nu-card' style='display:flex; flex-direction:column; gap:12px; "
            "margin-bottom:10px;'>"
            "<div style='display:flex; justify-content:space-between; align-items:baseline; "
            "gap:12px;'>"
            "<div>"
            f"<div class='nu-kicker'>{a.get('company', '—')} · {a.get('year', '—')}</div>"
            f"<div style='font:italic 400 21px/1.25 var(--serif); "
            f"color:var(--ink-strong);'>{a.get('case_name', '(unknown)')}</div>"
            "</div>"
            f"<span style='font:400 11px/1 var(--mono); color:var(--ink-muted); "
            f"white-space:nowrap;'>{dist_s}</span>"
            "</div>"
            f"{desc_html}{outcome_html}{fail_html}{mkts_html}"
            "</div>", unsafe_allow_html=True)


if "analog_results" in st.session_state:
    render_analogs(st.session_state["analog_results"])
else:
    st.markdown(
        "<div class='nu-card' style='margin-top:8px;'>"
        "<div class='nu-kicker'>How it reads</div>"
        "<div style='font:400 15px/1.55 var(--serif); color:var(--ink-muted); "
        "margin-top:8px;'>Describe a launch, campaign, or draft. Comprenda returns "
        "the closest historical analogs from the corpus — each with the company, "
        "year, what went wrong, and how it resolved. Pattern matching is the "
        "narrative device no incumbent offers.</div></div>", unsafe_allow_html=True)
