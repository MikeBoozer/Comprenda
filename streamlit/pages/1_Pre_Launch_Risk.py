"""Pre-Launch Cultural Risk Score (PLCS) page.

The killer feature. Marketer pastes draft content + target markets, gets a
0-100 cultural risk score per market with risk narrative + nearest analogs.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.nuance_queries import call_plcs, list_languages, call_find_analogs

st.set_page_config(page_title="Pre-Launch Risk — Nuance", page_icon="⚠️", layout="wide")
session = get_active_session()

st.title("⚠️ Pre-Launch Cultural Risk Score")
st.caption(
    "Paste a draft tagline, ad headline, product name, or marketing copy. "
    "We score it 0-100 for cultural risk in each target market, grounded in "
    "historical content from your corpus."
)

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    draft = st.text_area(
        "Draft content",
        height=160,
        max_chars=2000,
        placeholder=(
            "Example: \"Live Free, Drive Fast — the new electric sports car that "
            "puts you first.\""
        ),
    )

with right:
    languages = list_languages(session)
    target_markets = st.multiselect(
        "Target markets (language codes)",
        options=languages,
        default=[l for l in ["ja", "zh", "de", "es", "fr", "ko"] if l in languages][:4],
    )
    source_language = st.selectbox(
        "Source language",
        options=languages,
        index=languages.index("en") if "en" in languages else 0,
    )

st.divider()

# ---------------------------------------------------------------------------
# Score button
# ---------------------------------------------------------------------------
if st.button("Score cultural risk", type="primary", use_container_width=True,
             disabled=(not draft.strip() or not target_markets)):
    results_by_market = {}
    progress = st.progress(0, text="Scoring…")
    for i, market in enumerate(target_markets, start=1):
        with st.spinner(f"Scoring {market}…"):
            try:
                r = call_plcs(
                    session, draft.strip(), source_language, market,
                    requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"),
                )
                results_by_market[market] = r
            except Exception as exc:
                st.error(f"Failed for {market}: {exc}")
        progress.progress(i / len(target_markets), text=f"Scoring… ({i}/{len(target_markets)})")
    progress.empty()

    # ---------------------------------------------------------------------------
    # Render results
    # ---------------------------------------------------------------------------
    if results_by_market:
        st.subheader("Results")
        cols = st.columns(len(results_by_market))
        for col, (market, r) in zip(cols, results_by_market.items()):
            score = r.get("plcs_score", 0)
            conf = r.get("confidence", 0)
            color = ("🟢" if score < 40 else "🟡" if score < 60
                     else "🟠" if score < 80 else "🔴")
            col.metric(
                label=f"{color} {market}",
                value=f"{score} / 100",
                delta=f"confidence {conf:.0%}",
                delta_color="off",
            )

        # Narratives
        for market, r in results_by_market.items():
            with st.expander(f"📋 {market} — risk narrative", expanded=(r.get("plcs_score", 0) >= 60)):
                st.markdown(f"**Top frames:** {', '.join(r.get('top_frames', []))}")
                st.markdown(r.get("risk_narrative", "(no narrative)"))

                # Pull analog suggestions
                with st.spinner(f"Finding historical analogs for {market}…"):
                    try:
                        analogs = call_find_analogs(session, draft.strip(), market, k=3)
                        if analogs.get("analogs"):
                            st.markdown("**Most similar historical cases:**")
                            for a in analogs["analogs"]:
                                st.markdown(
                                    f"- **{a.get('case_name')}** "
                                    f"({a.get('company')}, {a.get('year')}) — "
                                    f"{a.get('outcome_summary', '')}"
                                )
                    except Exception:
                        pass

        # Translator suggestion
        high_risk = [(m, r) for m, r in results_by_market.items()
                     if r.get("plcs_score", 0) >= 60]
        if high_risk:
            st.divider()
            st.warning(
                f"⚠️ {len(high_risk)} target market(s) scored ≥60. "
                "Consider running the **Cultural Translator** to produce adapted variants."
            )
            if st.button("Open Cultural Translator with this draft →"):
                st.session_state["translator_prefill"] = draft.strip()
                st.session_state["translator_target_markets"] = [m for m, _ in high_risk]
                st.switch_page("pages/2_Cultural_Translator.py")
