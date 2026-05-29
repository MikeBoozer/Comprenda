"""Cultural Translator — produces frame-preserving content adaptations per market.

Redesign blueprint: the ScreenTranslator artboard in design/screens.jsx (the
index.html "translator" section). Query logic and the TRANSLATE_CONTENT /
SCORE_CONTENT proc signatures are preserved.

Real-data note: call_translator returns text / frame_shift / rationale per
variant — no risk score. The artboard's risk comparison is realized truthfully
by re-scoring each variant through the existing call_plcs proc, gated behind an
opt-in button so the default generate doesn't spend trial credits. See
design/IMPLEMENTATION_NOTES.md §3 (item F).
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import call_translator, call_plcs, list_languages
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, pill, badge, band_of, frame_label, risk_band,
)

inject_css()

session = get_active_session()

SAMPLE = "Live Free, Drive Fast — the new electric sports car that puts you first."
MARKET_NAMES = {
    "en": "English", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "de": "German", "es": "Spanish", "fr": "French", "pt": "Portuguese",
    "it": "Italian", "ar": "Arabic", "ru": "Russian", "hi": "Hindi",
}
FRAME_OPTIONS = ["(auto-detect dominant)", "individualist", "collectivist",
                 "nationalist", "globalist", "threat_framing", "opportunity_framing",
                 "historical_grievance", "status_quo", "reform_seeking",
                 "spiritual_ethical", "pragmatic"]
_WORDS = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}


def market_name(code):
    return MARKET_NAMES.get(code, code.upper())


def _word(n):
    return _WORDS.get(n, str(n))


def _section_head(kicker, headline, dek=None):
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:680px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


def _use_sample():
    # Mutating a widget-keyed session_state value is only allowed from a
    # callback (runs before the next rerun re-instantiates the widget).
    st.session_state["translator_source"] = SAMPLE


def _variant_card(n, frame_shift, text, rationale, score=None, conf=None):
    """One editorial variant card. score/conf shown only after re-scoring."""
    if score is not None:
        band = band_of(score)
        score_html = (
            f"<div style='display:flex; align-items:baseline; gap:6px; margin-top:2px;'>"
            f"<span class='nu-score-n nu-score-n--{band}' style='font-size:40px;'>{score}</span>"
            f"<span class='nu-score-denom'>/100</span>"
            f"<span style='margin-left:auto;'>{badge(score)}</span></div>")
        conf_html = (
            f"<div style='font-family:var(--mono); font-size:11px; color:var(--ink-muted);'>"
            f"{conf*100:.0f}% confidence on re-scored risk</div>" if conf is not None else "")
    else:
        score_html = conf_html = ""
    st.markdown(f"""
      <div class='nu-card' style='display:flex; flex-direction:column; gap:12px;
                                  min-height:240px;'>
        <div style='display:flex; justify-content:space-between; align-items:center; gap:8px;'>
          <div class='nu-kicker'>Variant {n}</div>
          {pill(frame_label(frame_shift))}
        </div>
        {score_html}
        <blockquote style='font:400 17px/1.5 var(--serif); color:var(--ink);
                           margin:0; padding:0; border:0;'>"{text}"</blockquote>
        <div style='font:400 13px/1.55 var(--sans); color:var(--ink-muted);
                    margin-top:auto;'>{rationale}</div>
        {conf_html}
      </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Prefill handoff from the PLCS page ("Open Translator with this draft").
# ---------------------------------------------------------------------------
if "translator_prefill" in st.session_state:
    st.session_state["translator_source"] = st.session_state.pop("translator_prefill")
st.session_state.setdefault("translator_source", "")
prefill_markets = st.session_state.pop("translator_target_markets", [])

source_now = st.session_state["translator_source"]
is_empty = not source_now.strip()
has_results = "translator_results" in st.session_state

# ---------------------------------------------------------------------------
# Header (state-dependent, mirroring the empty vs populated artboards).
# ---------------------------------------------------------------------------
if has_results:
    tm = st.session_state["translator_results"]["target_market"]
    page_header(
        f"Cultural translation · adapting for {market_name(tm)}",
        "Same intent, different frame.",
        "Culturally-adapted variants of the source draft, each shifting the "
        "cultural frame to match in-market discourse. Re-score any variant to "
        "compare its risk before shipping.")
else:
    page_header(
        "Cultural translation · content adaptation",
        "Adapt without losing the point.",
        "Frame-preserving variants that shift cultural register without distorting "
        "intent — written in the target market's language, ready for your workflow.")

# ---------------------------------------------------------------------------
# Input zone
# ---------------------------------------------------------------------------
languages = list_languages(session)
if not languages:
    st.warning(
        "No languages found in the corpus yet, so there are no markets to "
        "translate between. Load demo data first (see `docs/03_runbook.md`), "
        "then reload this page.")
    st.stop()

left, right = st.columns([2, 1], gap="large")

with left:
    st.markdown("<div class='nu-kicker'>Source draft</div>", unsafe_allow_html=True)
    source_content = st.text_area(
        "Source content", key="translator_source", height=160, max_chars=2000,
        label_visibility="collapsed",
        placeholder="Paste a tagline, headline, product name, or campaign line. "
                    "Up to 2,000 characters.")
    meta_l, meta_r = st.columns([3, 1])
    meta_l.markdown(
        f"<span style='font-family:var(--mono); font-size:11px; color:var(--ink-faint);'>"
        f"{len(source_content)} / 2,000</span>", unsafe_allow_html=True)
    meta_r.button("Try a sample →", use_container_width=True, on_click=_use_sample)

with right:
    st.markdown("<div class='nu-kicker'>Target market</div>", unsafe_allow_html=True)
    target_market = st.selectbox(
        "Target market", options=languages, label_visibility="collapsed",
        index=(languages.index(prefill_markets[0])
               if prefill_markets and prefill_markets[0] in languages else 0),
        format_func=lambda c: f"{c} · {market_name(c)}")
    st.markdown("<div class='nu-kicker' style='margin-top:8px;'>Source language</div>",
                unsafe_allow_html=True)
    source_language = st.selectbox(
        "Source language", options=languages, label_visibility="collapsed",
        index=languages.index("en") if "en" in languages else 0,
        format_func=lambda c: f"{c} · {market_name(c)}")
    st.markdown("<div class='nu-kicker' style='margin-top:8px;'>Frame override</div>",
                unsafe_allow_html=True)
    frame_override = st.selectbox(
        "Target frame (optional override)", options=FRAME_OPTIONS,
        label_visibility="collapsed", index=0)
    st.caption("Adapts to the target market's dominant frames. Override to force one.")

st.divider()

generate = st.button("Generate adapted variants", type="primary",
                     use_container_width=True, disabled=is_empty)

# ---------------------------------------------------------------------------
# Generate → persist results so they survive the re-score rerun.
# ---------------------------------------------------------------------------
if generate:
    with st.spinner("Generating culturally-adapted variants…"):
        try:
            r = call_translator(
                session, source_content.strip(), source_language, target_market,
                target_frame_hint=None if frame_override.startswith("(") else frame_override,
                requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"))
        except Exception as exc:
            st.error(f"Failed: {exc}")
            r = None
    if r:
        st.session_state["translator_results"] = {
            "draft": source_content.strip(), "source_language": source_language,
            "target_market": target_market, "result": r,
        }
        st.session_state.pop("translator_rescored", None)  # clear stale scores


# ===========================================================================
# RESULTS
# ===========================================================================
def render_results(state):
    r = state["result"]
    variants = r.get("variants", []) or []
    if not variants:
        st.info("The model returned no variants for this draft. Try rephrasing the source.")
        return
    target = state["target_market"]
    n_var = len(variants)
    target_frame = r.get("target_frame_hint", "")
    rescored = st.session_state.get("translator_rescored")

    st.divider()
    _section_head(
        f"Result · {_word(n_var).lower()} variant{'s' if n_var != 1 else ''} · "
        f"target frame {frame_label(target_frame)}" if target_frame
        else f"Result · {_word(n_var).lower()} variants",
        f"{_word(n_var)} ways this could land in {market_name(target)}.",
        "Each variant takes a different cultural frame while preserving the "
        "marketing intent. Written in the target market's language.")

    # --- Variant cards -----------------------------------------------------
    cols = st.columns(n_var, gap="medium")
    var_scores = (rescored or {}).get("variants", [])
    for i, (col, v) in enumerate(zip(cols, variants)):
        sc = var_scores[i] if i < len(var_scores) else {}
        with col:
            _variant_card(
                i + 1, v.get("frame_shift", "?"), v.get("text", "(no text)"),
                v.get("rationale", ""),
                score=sc.get("score"), conf=sc.get("conf"))

    st.divider()

    # --- Risk comparison (opt-in: composes the existing call_plcs proc) ----
    if rescored:
        orig = rescored["original"]
        _section_head(
            "Risk comparison · original vs. adapted",
            "The gap the translator closed.",
            f"Original draft scored {orig}/100 in {market_name(target)}. "
            "Each adapted variant is positioned on the same scale below.")
        markers = [("Original", orig, band_of(orig))]
        for i, sc in enumerate(var_scores, start=1):
            s = sc.get("score")
            if s is not None:
                markers.append((f"Variant {i}", s, band_of(s)))
        risk_band(markers)
    else:
        _section_head(
            "Compare before shipping",
            "Re-score these variants for cultural risk.",
            "Scores the original draft and each variant through the same "
            "Pre-Launch Risk model so you can compare on one scale. Runs a few "
            "Cortex inferences — only when you ask.")
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button(f"Re-score {_word(n_var).lower()} variant"
                     f"{'s' if n_var != 1 else ''} for risk →", type="primary"):
            scored = {"variants": []}
            prog = st.progress(0, text="Re-scoring…")
            steps = n_var + 1
            try:
                # Original draft: source language → target market (as PLCS scored it).
                o = call_plcs(session, state["draft"], state["source_language"], target,
                              requested_by="translator")
                scored["original"] = int(o.get("plcs_score", 0))
                prog.progress(1 / steps, text="Re-scoring… (original)")
                # Each variant is written in the target language → score in-market.
                for i, v in enumerate(variants, start=1):
                    res = call_plcs(session, v.get("text", ""), target, target,
                                    requested_by="translator")
                    scored["variants"].append({
                        "score": int(res.get("plcs_score", 0)),
                        "conf": float(res.get("confidence", 0))})
                    prog.progress((i + 1) / steps, text=f"Re-scoring… ({i}/{n_var})")
            except Exception as exc:
                st.error(f"Re-scoring failed: {exc}")
                scored = None
            prog.empty()
            if scored and "original" in scored:
                st.session_state["translator_rescored"] = scored
                st.rerun()

    st.divider()

    # --- Copy + provenance -------------------------------------------------
    with st.expander("Copy variants as text", expanded=False):
        for i, v in enumerate(variants, start=1):
            st.markdown(f"**Variant {i}** · {frame_label(v.get('frame_shift', '?'))}")
            st.code(v.get("text", ""), language=None)
    with st.expander("About this run", expanded=False):
        st.markdown(f"- Target market · {market_name(target)} (`{target}`)")
        st.markdown(f"- Source language · {market_name(state['source_language'])} "
                    f"(`{state['source_language']}`)")
        st.markdown(f"- Target frame · {frame_label(target_frame)}"
                    if target_frame else "- Target frame · (auto-detect)")
        st.markdown(f"- Variants generated · {n_var}")
        st.markdown(f"- Run id · `{r.get('run_id', '—')}`")
        st.markdown(f"- Model · `{r.get('model', '—')}`")


# ===========================================================================
# EMPTY / FIRST-RUN BODY
# ===========================================================================
def render_empty_body():
    st.divider()
    ex_l, ex_r = st.columns([3, 2], gap="large")
    with ex_l:
        _section_head("What the translator does",
                      "Three frames, one intent, your language.")
        for n, h, p in [
            ("a.", "Frame-preserving variants.",
             "Three adaptations of your draft, each shifting the cultural frame to "
             "match how the target market actually talks — not a literal translation."),
            ("b.", "A rationale for each.",
             "One sentence on why the frame shift works in-market, so you can defend "
             "the choice to a stakeholder."),
            ("c.", "Re-score on demand.",
             "Run any variant back through Pre-Launch Risk to compare its cultural "
             "risk against the original on one scale, before you ship."),
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
            <div class='nu-kicker'>A draft worth adapting</div>
            <div style='font:400 17px/1.5 var(--serif); color:var(--ink); margin:10px 0 8px;'>
              "{SAMPLE}"
            </div>
            <div style='font:400 13px/1.55 var(--sans); color:var(--ink-muted);'>
              An assertive, individualist automotive line. See how it reframes for a
              market that codes restraint as status.
            </div>
          </div>
        """, unsafe_allow_html=True)
        st.button("Use this sample →", type="primary", use_container_width=True,
                  on_click=_use_sample)


# ---------------------------------------------------------------------------
# Dispatch — include `generate` so results render on the same run that produced
# them (has_results is computed at top-of-script, before the generate block).
# ---------------------------------------------------------------------------
if (generate or has_results) and "translator_results" in st.session_state:
    render_results(st.session_state["translator_results"])
elif is_empty:
    render_empty_body()
