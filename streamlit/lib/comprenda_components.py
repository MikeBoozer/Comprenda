"""Comprenda design-system components.

Per-component helpers built on the CSS injected by ``comprenda_theme.inject_css()``.
Each helper either emits Streamlit primitives directly or renders one
``st.markdown(unsafe_allow_html=True)`` call using the ``nu-*`` classes from the
theme module. The small string builders (``pill``, ``badge``, ``frame_label``)
return HTML so they can be composed inside larger components.

Reference: §5 (component specs) and §7.6 (frame labels) of the design handoff.
"""
import streamlit as st

# ---------------------------------------------------------------------------
# Bands & labels — the verdict vocabulary, centralized so every score on
# screen reads from the same thresholds (§2.1 risk bands).
# ---------------------------------------------------------------------------

# score thresholds → band key.  0–35 safe · 35–55 caution · 55–75 warn · 75+ risk
_BAND_LABELS = {"safe": "Low", "caution": "Moderate", "warn": "Elevated", "risk": "High"}


def band_of(score):
    """Map a 0–100 score to its band key (safe / caution / warn / risk)."""
    return ("risk" if score >= 75 else "warn" if score >= 55
            else "caution" if score >= 35 else "safe")


def frame_label(token: str) -> str:
    """Turn a snake_case corpus frame token into a display string (§7.6).

    Never render the raw token in UI — it reads as a database leak.
    """
    return token.replace("_", " ").replace("-", " ").capitalize()


# ---------------------------------------------------------------------------
# Small composable chips — return HTML strings (§5, pill/badge).
# ---------------------------------------------------------------------------

def pill(text, tone="neutral"):
    """Return a mono-font pill chip. tone in {neutral, risk, warn, safe}."""
    cls = "nu-pill" if tone == "neutral" else f"nu-pill nu-pill--{tone}"
    return f"<span class='{cls}'>{text}</span>"


def badge(score):
    """Return a verdict badge for a 0–100 score, banded and labeled."""
    band = band_of(score)
    return f"<span class='nu-badge nu-badge--{band}'>{_BAND_LABELS[band]}</span>"


# ---------------------------------------------------------------------------
# Sidebar wordmark — the typographic brand mark (§2.2). Never an image.
# ---------------------------------------------------------------------------

def sidebar_brand():
    """Render the Comprenda wordmark above the page nav. Serif, roman, 700."""
    st.sidebar.markdown(
        "<div style='font:700 32px/1 var(--serif); letter-spacing:-0.01em;"
        " color:var(--ink-strong); padding:12px 6px 2px;'>Comprenda</div>"
        "<div class='nu-kicker' style='padding:0 6px 10px; text-transform:none;"
        " letter-spacing:0;'>Don't translate. Understand.</div>",
        unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page header — kicker → h1 → lede → divider (§5.1).
# ---------------------------------------------------------------------------

def page_header(kicker, headline, lede):
    """The opening contract for every page: kicker, serif headline, lede."""
    st.caption(kicker)
    st.title(headline)
    st.markdown(f"<p class='nu-lede'>{lede}</p>", unsafe_allow_html=True)
    st.divider()


def section_head(kicker, headline, dek=None):
    """A mid-page section opener: kicker → serif h2 → optional serif dek (§5.1).

    The shared form of the local ``_section_head`` used on the PLCS / Translator
    screens, so every page introduces a section the same way.
    """
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:680px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KPI metric — restyled st.metric (§5.2).
# ---------------------------------------------------------------------------

def kpi(label, value, delta=None, kind="neutral"):
    """A single KPI. kind='neutral' keeps the delta uncolored (informational)."""
    delta_color = "off" if kind == "neutral" else "normal"
    st.metric(label, value, delta, delta_color=delta_color)


# ---------------------------------------------------------------------------
# PLCS per-market card (§5.3).
# ---------------------------------------------------------------------------

def plcs_card(market_code, market_name, score, conf, one_liner, frames):
    """One market's pre-launch cultural risk score. Render four in st.columns(4)."""
    band = band_of(score)
    label = _BAND_LABELS[band]
    frames_html = "".join(pill(frame_label(f)) for f in frames)
    st.markdown(f"""
      <div class='nu-card' style='border-top: 3px solid var(--{band});
                                  min-height: 280px; display:flex;
                                  flex-direction:column; gap:12px;'>
        <div style='display:flex; justify-content:space-between;'>
          <div>
            <div class='nu-kicker'>{market_code}</div>
            <div style='font:600 16px/1.2 var(--sans);
                        color:var(--ink-strong);'>{market_name}</div>
          </div>
          <span class='nu-badge nu-badge--{band}'>{label}</span>
        </div>
        <div style='display:flex; align-items:baseline; gap:4px;'>
          <span class='nu-score-n nu-score-n--{band}'
                style='font-size:64px;'>{score}</span>
          <span class='nu-score-denom'>/100</span>
        </div>
        <div style='display:flex; align-items:center; gap:8px;'>
          <div class='nu-conf-bar' style='flex:1;'>
            <div class='nu-conf-fill' style='width:{conf*100:.0f}%;'></div>
          </div>
          <span style='font-family:var(--mono); font-size:11px; color:var(--ink-muted);'>
            {conf*100:.0f}% conf
          </span>
        </div>
        <div style='font:400 13px/1.5 var(--serif); color:var(--ink);'>
          {one_liner}
        </div>
        <div style='margin-top:auto; display:flex; flex-wrap:wrap; gap:3px;'>
          {frames_html}
        </div>
      </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Risk band — the signature viz (§5.4).
# ---------------------------------------------------------------------------

def risk_band(markers, analogs=()):
    """The signature risk band.

    markers: list of (label, score, band) — drawn on top.
    analogs: list of (label, score) — drawn as light ticks behind.

    Marker pills are nudged apart when two scores fall within 4 points so the
    labels stay legible (§5.4).
    """
    # Nudge overlapping pill labels: order by score, push later pills right
    # when they crowd the previous one.
    ordered = sorted(enumerate(markers), key=lambda t: t[1][1])
    pill_left = {}
    last = -100.0
    for idx, (_lbl, score, _band) in ordered:
        pos = max(score, last + 4)
        pill_left[idx] = pos
        last = pos

    analog_html = "".join(
        f"<div class='nu-band-analog' style='left:{s}%;' title='{lbl}'></div>"
        for lbl, s in analogs)
    marker_html = "".join(
        f"<div class='nu-band-marker' style='left:{s}%;'>"
        f"<div class='nu-band-marker-pill' "
        f"style='left:{pill_left[i]}%; transform:translateX(-50%);'>{lbl} · {s}</div>"
        f"</div>"
        for i, (lbl, s, _band) in enumerate(markers))
    st.markdown(f"""
      <div class='nu-band'>{analog_html}{marker_html}</div>
      <div style='display:flex; justify-content:space-between;
                  margin-top:8px; font:500 11px/1 var(--mono);
                  color:var(--ink-muted);'>
        <span>0 · safe</span><span>35</span><span>55</span>
        <span>75</span><span>100 · do not ship</span>
      </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Analog list item (§5.5).
# ---------------------------------------------------------------------------

def analog(year, company, case_name, outcome, gap):
    """One historical analog row."""
    st.markdown(f"""
      <div style='display:flex; gap:16px; padding:12px 0;
                  border-bottom:1px solid var(--rule);'>
        <div style='min-width:76px;'>
          <div style='font:600 13px/1.2 var(--sans);'>{year}</div>
          <div style='font:400 10px/1.2 var(--mono);
                      color:var(--ink-muted);'>gap {gap}</div>
        </div>
        <div>
          <div style='font:600 13px/1.2 var(--sans);
                      color:var(--ink-strong);'>{company}</div>
          <div style='font:italic 400 13px/1.3 var(--serif);'>{case_name}</div>
          <div style='font:400 12px/1.4 var(--sans);
                      color:var(--ink-muted);'>{outcome}</div>
        </div>
      </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Recommendation band — the dark CTA strip (§5.6).
# ---------------------------------------------------------------------------

def rec_band(kicker, headline, body, primary_label, primary_action,
             secondary=()):
    """The dark recommended-next-move strip. Buttons sit outside the band so
    they stay native and clickable."""
    st.markdown(f"""
      <div class='nu-cta-band'>
        <div>
          <div class='nu-kicker'>{kicker}</div>
          <h2>{headline}</h2>
          <p>{body}</p>
        </div>
        <div></div>
      </div>
    """, unsafe_allow_html=True)
    cols = st.columns([1, 1, 1])
    if cols[0].button(primary_label, type="primary",
                      use_container_width=True):
        primary_action()
    for i, (lbl, fn) in enumerate(secondary, start=1):
        if cols[i].button(lbl, use_container_width=True):
            fn()


# ---------------------------------------------------------------------------
# Frame-share bar — per-language frame distribution (§5.8).
# ---------------------------------------------------------------------------

# Graded ink→paper neutrals so adjacent segments are distinguishable. The
# risk_frame segment overrides to oxblood. All §2 palette tokens:
# ink · ink-muted · ink-faint · rule-strong · paper-deeper · paper-deep.
_SEG_SHADES = ["#1C1A17", "#6E665B", "#9C9586", "#C3B99F", "#E2DAC5", "#ECE6D7"]


def frame_share_bar(language, share_dict, risk_frame=None):
    """A horizontal stacked bar of frame shares for one language.

    share_dict: {frame_token: share} where shares sum to ~1.0.
    risk_frame: the frame your content is being absorbed into — that segment
                gets the oxblood treatment (§5.8).
    """
    items = list(share_dict.items())

    def _color(i, tok):
        return "var(--risk)" if tok == risk_frame else _SEG_SHADES[i % len(_SEG_SHADES)]

    segments = "".join(
        f"<div title='{frame_label(tok)} · {share*100:.0f}%' "
        f"style='width:{share*100:.1f}%; height:100%; background: {_color(i, tok)}; "
        f"border-right:1px solid var(--paper-card);'></div>"
        for i, (tok, share) in enumerate(items))
    legend = "".join(
        "<span style='display:inline-flex; align-items:center; gap:4px; margin-right:10px;'>"
        f"<span style='width:9px; height:9px; border-radius:2px; background:{_color(i, tok)};'></span>"
        f"<span style=\"color: var(--{'risk' if tok == risk_frame else 'ink-muted'});\">"
        f"{frame_label(tok)} {share*100:.0f}%</span></span>"
        for i, (tok, share) in enumerate(items))
    st.markdown(f"""
      <div style='margin: 10px 0;'>
        <div style='display:flex; justify-content:space-between;
                    align-items:baseline; margin-bottom:4px;'>
          <span style='font:600 13px/1.2 var(--sans); color:var(--ink-strong);'>{language}</span>
        </div>
        <div style='display:flex; height:22px; border:1px solid var(--rule-strong);
                    border-radius:2px; overflow:hidden;'>{segments}</div>
        <div style='margin-top:5px; font:400 11px/1.4 var(--mono);'>{legend}</div>
      </div>
    """, unsafe_allow_html=True)
