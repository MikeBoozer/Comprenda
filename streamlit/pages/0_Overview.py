"""Overview — the morning read (home page).

Was the entry script; under the st.navigation router (comprenda_app.py) the home
content lives here as the default page. No st.set_page_config / sidebar here —
the router owns global config and the sidebar. Redesign blueprint: §6.1.
"""
import datetime

import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import (
    get_recent_drift_events,
    get_recent_plcs_scores,
    get_kpi_summary,
)
from lib.comprenda_theme import inject_css
from lib.comprenda_components import (
    page_header, kpi, badge, pill, band_of,
)

inject_css()

session = get_active_session()

# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------
_WORDS = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
          6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}


def _word(n):
    return _WORDS.get(n, str(n))


def _section_head(kicker, headline, dek=None):
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:640px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


def _cds_tone(new_cds):
    return "risk" if new_cds >= 0.55 else "warn" if new_cds >= 0.35 else "neutral"


_CDS_VERDICT = {"risk": "Past tolerance", "warn": "Watch", "neutral": "Within tolerance"}


def _onward_card(num, title, body):
    st.markdown(f"""
      <div class='nu-card' style='min-height:150px;'>
        <div style='font:400 22px/1 var(--serif); color:var(--ink-faint);'>{num}</div>
        <div style='font:600 16px/1.3 var(--sans); color:var(--ink-strong); margin:8px 0 6px;'>{title}</div>
        <div style='font:400 13px/1.5 var(--sans); color:var(--ink-muted);'>{body}</div>
      </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
kpis = get_kpi_summary(session)
is_empty = kpis.get("posts", 0) == 0 and kpis.get("events", 0) == 0


# ===========================================================================
# EMPTY / FIRST-RUN STATE
# ===========================================================================
if is_empty:
    page_header(
        "Welcome · trial account",
        "Three reads before lunch.",
        "Comprenda scores how a draft will land in markets you don't speak — "
        "before you ship it. The fastest path is a thirty-second test drive on "
        "a draft of your own. Pick a starting point below.",
    )

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown(
            "<div style='display:inline-flex; align-items:center; justify-content:center;"
            " width:44px; height:44px; border:1px solid var(--rule-strong); border-radius:2px;"
            " font:700 22px/1 var(--serif); color:var(--ink-strong); margin-bottom:12px;'>C</div>",
            unsafe_allow_html=True)
        _section_head("How most teams start", "A three-step trial.")
        for n, h, p in [
            ("01", "Score one draft.",
             "Paste any tagline, headline, product name, or campaign line into "
             "Pre-Launch Risk. Pick two or three markets. You'll have a defensible "
             "read in about forty seconds."),
            ("02", "Generate a brief.",
             "Pick a recent event tag — a launch, a campaign, a news moment — and "
             "ask for a two-page cultural brief. It comes back source-cited and "
             "ready to forward."),
            ("03", "Subscribe one brand.",
             "Drift Alerts watches a brand or product across language communities "
             "and tells you when the conversation diverges. Set one up; the rest "
             "happens in the background."),
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

    with right:
        st.markdown(f"""
          <div class='nu-card'>
            <div class='nu-kicker'>Try with a sample draft</div>
            <div style='font:400 17px/1.5 var(--serif); color:var(--ink);
                        margin:10px 0 8px;'>
              "Live Free, Drive Fast — the new electric sports car that puts you first."
            </div>
            <div style='font:400 13px/1.55 var(--sans); color:var(--ink-muted);'>
              A real automotive launch line we've scored before. The result is
              striking — and worth seeing before you paste your own.
            </div>
          </div>
        """, unsafe_allow_html=True)
        if st.button("Score this draft →", type="primary", use_container_width=True):
            st.session_state["plcs_prefill"] = (
                "Live Free, Drive Fast — the new electric sports car that puts you first.")
            st.switch_page("pages/1_Pre_Launch_Risk.py")
        st.markdown("<div class='nu-kicker' style='margin-top:16px;'>Or start clean</div>",
                    unsafe_allow_html=True)
        if st.button("Open Pre-Launch Risk", use_container_width=True):
            st.switch_page("pages/1_Pre_Launch_Risk.py")
        if st.button("Open AI Brief", use_container_width=True):
            st.switch_page("pages/8_AI_Brief.py")

    st.divider()

    st.markdown("<div class='nu-kicker'>What you'll get</div>", unsafe_allow_html=True)
    g = st.columns(3, gap="medium")
    with g[0]:
        _onward_card("i.", "A score, not a vibe.",
                     "Every result is a number, a band, a confidence interval, and "
                     "three historical analogs you can name in a meeting.")
    with g[1]:
        _onward_card("ii.", "Frames, not translations.",
                     "The signal is <em>how</em> markets are reading the same event "
                     "differently — not whether the words translated.")
    with g[2]:
        _onward_card("iii.", "A page you can forward.",
                     "Every brief is exportable, source-cited, and written like an "
                     "intelligence report — not a dashboard screenshot.")
    st.stop()


# ===========================================================================
# POPULATED STATE — the morning read
# ===========================================================================
drift = get_recent_drift_events(session, limit=8)
plcs = get_recent_plcs_scores(session, limit=8)

n_drift = len(drift)
elevated = plcs[plcs["PLCS_SCORE"] >= 55] if not plcs.empty else plcs
m_elevated = len(elevated)
signals = n_drift + m_elevated

now = datetime.datetime.now()
kicker = f"{now:%A} · {now.day} {now:%b %Y} · {now:%H:%M} PT"

if signals == 0:
    headline = "Quiet morning."
    lede = (f"No drift events past tolerance, no elevated pre-launch scores in the "
            f"last 24 hours. The corpus is tracking {kpis['events']} events; the "
            f"next scheduled drift check runs on the hour.")
else:
    # Biggest story: the largest overnight drift move, else the top elevated score.
    if n_drift:
        top = drift.sort_values("DELTA_CDS", ascending=False).iloc[0]
        biggest = (f"{top['ENTITY_NAME']} ({top['LANGUAGE_A']}⇄{top['LANGUAGE_B']}) "
                   f"shows the largest overnight move")
    else:
        top = elevated.sort_values("PLCS_SCORE", ascending=False).iloc[0]
        biggest = (f"a {int(top['PLCS_SCORE'])}-score draft for {top['TARGET_MARKET']} "
                   f"is the one to watch")
    headline = (f"{_word(signals)} signal{'s' if signals != 1 else ''} worth your morning.")
    lede = (f"{_word(n_drift)} new drift event{'s' if n_drift != 1 else ''}, "
            f"{_word(m_elevated)} elevated pre-launch score{'s' if m_elevated != 1 else ''} "
            f"from overnight. {biggest}. The full read is below.")

page_header(kicker, headline, lede)

# --- KPI strip -------------------------------------------------------------
# NOTE: get_kpi_summary returns 4 counts and no week-over-week deltas, so this
# strip shows 4 metrics without deltas. The artboard envisions 6 metrics with
# weekly deltas — a real-data gap to resolve via the round-trip (see handoff §10).
cols = st.columns(4, gap="medium")
with cols[0]:
    kpi("Events tracked", f"{kpis['events']:,}")
with cols[1]:
    kpi("Languages analyzed", f"{kpis['languages']:,}")
with cols[2]:
    kpi("Posts in corpus", f"{kpis['posts']:,}")
with cols[3]:
    kpi("Drift events · 24h", f"{kpis['drift_24h']:,}")

st.divider()

# --- Two-column feeds ------------------------------------------------------
feed_l, feed_r = st.columns(2, gap="large")

with feed_l:
    _section_head(
        "Drift alerts · 24h",
        "Where communities are pulling apart.",
        "Sorted by Δ-CDS. Each row is one entity drifting between two language "
        "communities; the verdict is read off the new divergence score.")
    if drift.empty:
        st.info("No drift events yet. Subscribe an entity in **Drift Alerts**.")
    else:
        for _, r in drift.iterrows():
            tone = _cds_tone(r["NEW_CDS"])
            delta_color = "var(--ink)" if tone == "neutral" else f"var(--{tone})"
            st.markdown(f"""
              <div class='nu-card' style='padding:16px; margin-bottom:12px;'>
                <div style='display:flex; justify-content:space-between; align-items:baseline; gap:12px;'>
                  <div>
                    <span style='font:600 15px/1.2 var(--sans); color:var(--ink-strong);'>{r['ENTITY_NAME']}</span>
                    {pill(f"{r['LANGUAGE_A']} ⇄ {r['LANGUAGE_B']}")}
                  </div>
                  <div style='text-align:right; white-space:nowrap;'>
                    <span style='font-family:var(--mono); font-size:13px; color:{delta_color};'>{r['PREV_CDS']:.2f} → {r['NEW_CDS']:.2f}</span><br>
                    <span style='font-family:var(--mono); font-size:11px; color:var(--ink-muted);'>Δ {r['DELTA_CDS']:+.2f}</span>
                  </div>
                </div>
                <div style='margin-top:10px; display:flex; justify-content:space-between; align-items:center;'>
                  {pill(_CDS_VERDICT[tone], tone)}
                  <span style='font-family:var(--mono); font-size:11px; color:var(--ink-muted);'>detected · {r['DETECTED_AT']}</span>
                </div>
              </div>
            """, unsafe_allow_html=True)

with feed_r:
    _section_head(
        "Pre-launch scores · 24h",
        "What's at the door.",
        f"{len(plcs)} draft{'s' if len(plcs) != 1 else ''} scored overnight. "
        f"{_word(m_elevated)} elevated.")
    if plcs.empty:
        st.info("No PLCS runs yet. Try one in **Pre-Launch Risk**.")
    else:
        for _, r in plcs.iterrows():
            score = int(r["PLCS_SCORE"])
            band = band_of(score)
            st.markdown(f"""
              <div class='nu-card' style='padding:16px; margin-bottom:12px;'>
                <div style='display:flex; justify-content:space-between; gap:12px; align-items:flex-start;'>
                  <div style='font:400 14px/1.45 var(--serif); color:var(--ink);'>"{r['DRAFT_PREVIEW']}"</div>
                  <div style='text-align:right; white-space:nowrap;'>
                    <span class='nu-score-n nu-score-n--{band}' style='font-size:30px;'>{score}</span>
                    <div style='margin-top:2px;'>{badge(score)}</div>
                  </div>
                </div>
                <div style='margin-top:8px; font-family:var(--mono); font-size:11px; color:var(--ink-muted);'>
                  {r['TARGET_MARKET']} · conf {r['CONFIDENCE']:.0%} · {r['INFERENCE_TIMESTAMP']}
                </div>
              </div>
            """, unsafe_allow_html=True)

st.divider()

# --- Onward grid -----------------------------------------------------------
st.markdown("<div class='nu-kicker'>What's next</div>", unsafe_allow_html=True)
onward = st.columns(3, gap="medium")
with onward[0]:
    _onward_card("01", "Generate this morning's brief",
                 "A two-page synthesis across a recent event in your priority "
                 "markets. Source-cited, about forty seconds.")
    if st.button("Generate →", use_container_width=True, key="onward_brief"):
        st.switch_page("pages/8_AI_Brief.py")
with onward[1]:
    _onward_card("02", "Translate the elevated draft",
                 "Take the highest-scoring draft into the Cultural Translator for "
                 "frame-preserving variants per market.")
    if st.button("Open translator →", use_container_width=True, key="onward_translate"):
        st.switch_page("pages/2_Cultural_Translator.py")
with onward[2]:
    _onward_card("03", "Subscribe a new entity",
                 "Add a brand, product, or campaign to ongoing drift monitoring "
                 "across language communities.")
    if st.button("Add subscription →", use_container_width=True, key="onward_subscribe"):
        st.switch_page("pages/6_Drift_Alerts.py")
