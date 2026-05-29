"""Pre-Launch Cultural Risk Score (PLCS) — the signature screen.

Marketer pastes draft content + target markets, gets a 0-100 cultural risk
score per market with a banded verdict, the model's narrative, nearest
historical analogs, and a recommended next move.

Redesign blueprint: Claude-Code-Handoff.md §6.2. Query logic and the
SCORE_CONTENT / FIND_ANALOGS proc signatures are preserved.
"""
import time

import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import call_plcs, list_languages, call_find_analogs
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, plcs_card, risk_band, analog, rec_band,
    pill, band_of, frame_label,
)

inject_css()

session = get_active_session()

SAMPLE = "Live Free, Drive Fast — the new electric sports car that puts you first."
MARKET_NAMES = {
    "en": "English", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "de": "German", "es": "Spanish", "fr": "French", "pt": "Portuguese",
    "it": "Italian", "ar": "Arabic", "ru": "Russian", "hi": "Hindi",
}
_WORDS = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
          6: "Six", 7: "Seven", 8: "Eight"}


def _word(n):
    return _WORDS.get(n, str(n))


def market_name(code):
    return MARKET_NAMES.get(code, code.upper())


def _use_sample():
    # Mutating a widget-keyed session_state value (plcs_draft) is only allowed
    # from a callback, which runs before the next rerun instantiates the widget.
    st.session_state["plcs_draft"] = SAMPLE


def _section_head(kicker, headline, dek=None):
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:680px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


def _first_sentence(text):
    if not text:
        return ""
    for sep in (". ", "! ", "? "):
        if sep in text:
            return text.split(sep)[0].strip() + "."
    return text.strip()


# ---------------------------------------------------------------------------
# Prefill handoff from the home page ("Score this draft").
# ---------------------------------------------------------------------------
if "plcs_prefill" in st.session_state:
    st.session_state["plcs_draft"] = st.session_state.pop("plcs_prefill")
st.session_state.setdefault("plcs_draft", "")

draft_now = st.session_state["plcs_draft"]
is_empty = not draft_now.strip()

# ---------------------------------------------------------------------------
# Header (state-dependent: matches the empty vs populated artboards).
# ---------------------------------------------------------------------------
if is_empty and "plcs_results" not in st.session_state:
    page_header(
        "Pre-launch cultural risk · PLCS",
        "Score a draft.",
        "One number per market, on a scale of 0–100. Each number is backed by a "
        "confidence interval, three historical analogs from your corpus, and a "
        "one-sentence read. Nothing is invented; everything is sourced.")
else:
    page_header(
        "Pre-launch cultural risk · PLCS",
        "Will this travel?",
        "Score a draft tagline, headline, or campaign line for cultural risk in "
        "any market in your corpus. The score is grounded in historical content — "
        "analogs are nameable.")

# ---------------------------------------------------------------------------
# Input zone
# ---------------------------------------------------------------------------
languages = list_languages(session)
if not languages:
    st.warning(
        "No languages found in the corpus yet, so there are no markets to score "
        "against. Load demo data first (see `docs/03_runbook.md`), then reload "
        "this page.")
    st.stop()

left, right = st.columns([2, 1], gap="large")

with left:
    st.markdown("<div class='nu-kicker'>Draft</div>", unsafe_allow_html=True)
    draft = st.text_area(
        "Draft content", key="plcs_draft", height=160, max_chars=2000,
        label_visibility="collapsed",
        placeholder="Paste a tagline, headline, product name, or campaign line. "
                    "Up to 2,000 characters.")
    meta_l, meta_r = st.columns([3, 1])
    meta_l.markdown(
        f"<span style='font-family:var(--mono); font-size:11px; color:var(--ink-faint);'>"
        f"{len(draft)} / 2,000 · ⌘↩ to score</span>", unsafe_allow_html=True)
    meta_r.button("Try a sample →", use_container_width=True, on_click=_use_sample)

with right:
    st.markdown("<div class='nu-kicker'>Target markets</div>", unsafe_allow_html=True)
    target_markets = st.multiselect(
        "Target markets", options=languages, label_visibility="collapsed",
        default=[l for l in ["ja", "ko", "de", "fr"] if l in languages][:4],
        format_func=lambda c: f"{c} · {market_name(c)}")
    st.markdown("<div class='nu-kicker' style='margin-top:8px;'>Source</div>",
                unsafe_allow_html=True)
    source_language = st.selectbox(
        "Source language", options=languages, label_visibility="collapsed",
        index=languages.index("en") if "en" in languages else 0,
        format_func=lambda c: f"{c} · {market_name(c)}")

st.divider()

run = st.button("Score cultural risk", type="primary", use_container_width=True,
                disabled=(is_empty or not target_markets))

# ---------------------------------------------------------------------------
# Score → persist results in session_state so they survive reruns.
# ---------------------------------------------------------------------------
if run:
    t0 = time.time()
    results = {}
    progress = st.progress(0, text="Scoring…")
    for i, market in enumerate(target_markets, start=1):
        with st.spinner(f"Scoring {market_name(market)}…"):
            try:
                results[market] = call_plcs(
                    session, draft.strip(), source_language, market,
                    requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"))
            except Exception as exc:
                st.error(f"Failed for {market_name(market)}: {exc}")
        progress.progress(i / len(target_markets),
                          text=f"Scoring… ({i}/{len(target_markets)})")
    progress.empty()

    worst = max(results, key=lambda m: results[m].get("plcs_score", 0)) if results else None
    analogs = []
    if worst is not None:
        try:
            analogs = call_find_analogs(session, draft.strip(), worst, k=3).get("analogs", [])
        except Exception:
            analogs = []

    st.session_state["plcs_results"] = {
        "results": results, "worst": worst, "analogs": analogs,
        "elapsed": time.time() - t0, "draft": draft.strip(),
    }


# ===========================================================================
# RESULTS
# ===========================================================================
def render_results(state):
    results = state["results"]
    if not results:
        return
    worst = state["worst"]
    scores = {m: int(r.get("plcs_score", 0)) for m, r in results.items()}
    max_score = scores[worst]
    n_markets = len(results)
    action = [m for m, s in scores.items() if s >= 55]   # warn or risk → adapt+
    caution = [m for m, s in scores.items() if 35 <= s < 55]

    st.divider()

    # --- Result header -----------------------------------------------------
    if action:
        verb = "is" if len(action) == 1 else "are"
        headline = (f"{_word(len(action))} of {n_markets} "
                    f"market{'s' if n_markets != 1 else ''} {verb} unsafe to ship as drafted.")
    elif caution:
        headline = f"Mostly fine. {market_name(worst)} is the one to watch."
    else:
        headline = "Cleared. No market scored above 35."
    worst_conf = results[worst].get("confidence", 0)
    dek = (f"{market_name(worst)} is the highest at {max_score}/100 "
           f"({worst_conf:.0%} confidence). Read the narrative below for why.")
    _section_head(
        f"Result · {n_markets} market{'s' if n_markets != 1 else ''} scored · "
        f"{state['elapsed']:.0f}s", headline, dek)

    # --- PLCS cards --------------------------------------------------------
    cols = st.columns(len(results), gap="medium")
    for col, (market, r) in zip(cols, results.items()):
        with col:
            plcs_card(
                market, market_name(market), int(r.get("plcs_score", 0)),
                float(r.get("confidence", 0)),
                _first_sentence(r.get("risk_narrative", "")),
                r.get("top_frames", []))

    st.divider()

    # --- Risk band (signature viz) ----------------------------------------
    # Markers are real; analog ticks are omitted because call_plcs returns
    # analog post_ids, not 0-100 positions (real-data gap, see handoff §10).
    _section_head("Risk spectrum · positioned on the 0–100 scale",
                  "Where this draft sits, market by market.")
    markers = [(m, scores[m], band_of(scores[m])) for m in results]
    risk_band(markers)

    st.divider()

    # --- Deep narrative for the worst market ------------------------------
    _section_head(f"Narrative · {market_name(worst)}", f"Why it scores {max_score}.")
    narr_l, narr_r = st.columns([3, 2], gap="large")
    with narr_l:
        frames_html = "".join(pill(frame_label(f)) for f in results[worst].get("top_frames", []))
        st.markdown(
            f"<p style='font:400 16px/1.6 var(--serif); color:var(--ink); max-width:640px;'>"
            f"{results[worst].get('risk_narrative', '(no narrative)')}</p>"
            f"<div style='margin-top:12px;'>{frames_html}</div>",
            unsafe_allow_html=True)
    with narr_r:
        st.markdown("<div class='nu-kicker'>Three historical analogs</div>",
                    unsafe_allow_html=True)
        if state["analogs"]:
            for a in state["analogs"]:
                gap = a.get("distance")
                analog(a.get("year", "—"), a.get("company", "—"),
                       a.get("case_name", "(unknown)"),
                       a.get("outcome_summary", ""),
                       f"{gap:.2f}" if isinstance(gap, (int, float)) else "—")
        else:
            st.caption("No close analogs found in the corpus for this draft.")

    # --- Progressive disclosure -------------------------------------------
    with st.expander("Confidence calculation", expanded=(max_score >= 60)):
        st.markdown(
            "Confidence reflects how densely the target market is represented in "
            "the corpus for content like this. Per market:")
        for m, r in results.items():
            st.markdown(f"- **{market_name(m)}** — {r.get('confidence', 0):.0%}")
    with st.expander("Sources cited", expanded=False):
        for m, r in results.items():
            ids = r.get("nearest_analogs", []) or []
            st.markdown(f"**{market_name(m)}** — {len(ids)} nearest posts")
            if ids:
                st.code(", ".join(map(str, ids)), language=None)
    with st.expander("About this run", expanded=False):
        st.markdown(f"- Duration · {state['elapsed']:.1f}s")
        for m, r in results.items():
            st.markdown(
                f"- {market_name(m)} · id `{r.get('plcs_id', '—')}` · "
                f"model `{r.get('model', '—')}`")

    st.divider()

    # --- Recommendation band ----------------------------------------------
    def _open_translator():
        st.session_state["translator_prefill"] = state["draft"]
        st.session_state["translator_target_markets"] = action or [worst]
        st.switch_page("views/2_Cultural_Translator.py")

    if action:
        names = ", ".join(market_name(m) for m in action)
        rec_head = f"Adapt for {names} before ship."
        rec_body = ("Cultural Translator can produce frame-preserving variants for "
                    "each flagged market, with a rationale and an updated risk score.")
    elif caution:
        rec_head = f"Review {market_name(worst)} before ship."
        rec_body = ("One market is in the watch band. Consider a frame-preserving "
                    "variant before committing the line.")
    else:
        rec_head = "Ship as drafted."
        rec_body = ("No market crossed the watch threshold. If you want regional "
                    "polish, the Translator is one click away.")
    rec_band("Recommended next move", rec_head, rec_body,
             "Open Translator with this draft →", _open_translator)


# ===========================================================================
# EMPTY / FIRST-RUN BODY — "what you'll see" + sample
# ===========================================================================
def render_empty_body():
    st.divider()
    ex_l, ex_r = st.columns([3, 2], gap="large")
    with ex_l:
        _section_head("What you'll see, in plain English",
                      "A score, a band, a story, a next move.")
        for n, h, p in [
            ("a.", "A number, banded.",
             "0–35 ship · 35–55 watch · 55–75 adapt · 75–100 do not ship. Bands "
             "derived from outcomes of historical launches in your corpus."),
            ("b.", "A confidence interval.",
             "How sure the model is, given corpus density for that market. Shown "
             "by default; the calculation expands on click."),
            ("c.", "Three nameable analogs.",
             "Historical lines that scored similarly, with what happened next — "
             "the defensibility your stakeholders need."),
            ("d.", "A recommended next move.",
             "Ship, adapt, or do not ship. If adapt: a one-click handoff to "
             "Cultural Translator with the draft pre-filled."),
        ]:
            st.markdown(f"""
              <div style='display:flex; gap:16px; padding:14px 0;
                          border-bottom:1px solid var(--rule);'>
                <div style='font:400 22px/1 var(--serif); color:var(--ink-faint);
                            min-width:32px;'>{n}</div>
                <div>
                  <div style='font:600 15px/1.3 var(--sans); color:var(--ink-strong);'>{h}</div>
                  <div style='font:400 13px/1.55 var(--sans); color:var(--ink-muted);
                              margin-top:2px;'>{p}</div>
                </div>
              </div>
            """, unsafe_allow_html=True)
    with ex_r:
        st.markdown(f"""
          <div class='nu-card'>
            <div class='nu-kicker'>A draft worth seeing</div>
            <div style='font:400 17px/1.5 var(--serif); color:var(--ink); margin:10px 0 8px;'>
              "{SAMPLE}"
            </div>
            <div style='font:400 13px/1.55 var(--sans); color:var(--ink-muted);'>
              Real automotive launch line, scored against ja, ko, de, fr. Spoiler:
              one market is the one to watch. Worth seeing why.
            </div>
          </div>
        """, unsafe_allow_html=True)
        st.button("Use this sample →", type="primary", use_container_width=True,
                  on_click=_use_sample)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if run or "plcs_results" in st.session_state:
    render_results(st.session_state["plcs_results"])
elif is_empty:
    render_empty_body()
