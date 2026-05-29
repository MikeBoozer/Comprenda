"""Comprenda design-system theme — single CSS injection helper.

Call ``inject_css()`` once per page, as the first Streamlit operation right
after ``st.set_page_config()``. One big string injected once avoids the
multi-``st.markdown`` flicker and keeps the design tokens in one place.

Anti-pattern avoided: this never targets Streamlit's rotating
``.st-emotion-cache-*`` classes. It only targets stable ``[data-testid]``
attributes, semantic HTML elements, or our own ``nu-`` prefixed classes.
"""
import streamlit as st

# Pulled from the design tokens in §2. Single source of truth.
_TOKENS = """
:root {
  --paper-bg:#F5F1E8; --paper-card:#FAF7EF; --paper-deep:#ECE6D7;
  --paper-deeper:#E2DAC5;
  --ink:#1C1A17; --ink-strong:#0E0D0B; --ink-muted:#6E665B; --ink-faint:#9C9586;
  --rule:#D8D1BE; --rule-strong:#C3B99F;
  --risk:#8B2A1F; --risk-bg:#F2DDD8;
  --warn:#B5781E; --warn-bg:#F5E6CD;
  --safe:#2F6B4A; --safe-bg:#DCE9DF;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"URW Palladio L","Book Antiqua",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Helvetica Neue",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace;
}
"""

# Stable Streamlit selectors — testids, semantic tags. NO emotion-cache hashes.
_BASE = """
html, body, .stApp { background: var(--paper-bg); color: var(--ink); }
.stApp { font-family: var(--sans); }

/* Editorial type for headings — Streamlit renders st.title -> h1, etc. */
h1, h2, h3, h4 { font-family: var(--serif); color: var(--ink-strong); letter-spacing:-0.01em; font-weight: 400; }
h1 { font-size: 44px; line-height: 1.05; }
h2 { font-size: 22px; line-height: 1.25; }
h3 { font-size: 16px; line-height: 1.3; font-family: var(--sans); font-weight: 600; }

/* st.caption — used as kicker */
[data-testid="stCaptionContainer"] {
  font-family: var(--sans); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.12em; color: var(--ink-muted);
}

/* st.metric — neutralize the default emoji-y look */
[data-testid="stMetric"] { background: transparent; padding: 0; }
[data-testid="stMetricLabel"] {
  font-family: var(--sans); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.12em; color: var(--ink-muted);
}
[data-testid="stMetricValue"] {
  font-family: var(--serif); font-size: 32px; line-height: 1; color: var(--ink-strong);
  font-variant-numeric: tabular-nums;
}
[data-testid="stMetricDelta"] { font-family: var(--mono); font-size: 11px; }

/* Buttons */
.stButton > button {
  font-family: var(--sans); font-size: 13px; font-weight: 500;
  border-radius: 2px; border: 1px solid var(--rule-strong);
  background: var(--paper-card); color: var(--ink); letter-spacing: 0.01em;
  padding: 10px 14px;
}
.stButton > button:hover { background: var(--paper-deep); border-color: var(--ink-muted); }
.stButton > button[kind="primary"] {
  background: var(--ink-strong); color: var(--paper-bg); border-color: var(--ink-strong);
}
.stButton > button[kind="primary"]:hover { background: var(--risk); border-color: var(--risk); }

/* Inputs */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextArea textarea {
  border-radius: 2px !important; border-color: var(--rule-strong) !important;
  background: var(--paper-card) !important; font-family: var(--sans) !important;
}

/* Dividers */
[data-testid="stDivider"] hr { border-top: 1px solid var(--rule); }

/* Dataframe — strip the rounded chrome, set serif numerals */
[data-testid="stDataFrame"] { border: 1px solid var(--rule); border-radius: 2px; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--paper-card); border-right: 1px solid var(--rule); }

/* Editorial content column — cap + center the main area so the page reads like
   a publication, not a full-bleed dashboard. */
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1280px !important; margin-left: auto !important; margin-right: auto !important;
}
"""

# Custom component classes — used by st.markdown(unsafe_allow_html=True).
_COMPONENTS = """
.nu-kicker { font: 600 11px/1 var(--sans); text-transform: uppercase;
             letter-spacing: 0.14em; color: var(--ink-muted); }
.nu-lede   { font: 400 17px/1.55 var(--serif); color: var(--ink); max-width: 720px; }

.nu-card   { background: var(--paper-card); border: 1px solid var(--rule);
             padding: 20px; border-radius: 2px; }

.nu-pill   { display:inline-block; padding:2px 7px; font:500 11px/1.4 var(--mono);
             background: var(--paper-deep); color: var(--ink-muted);
             border:1px solid var(--rule); border-radius:2px; margin: 0 2px; }
.nu-pill--risk { background: var(--risk-bg); color: var(--risk); border-color: var(--risk); }
.nu-pill--warn { background: var(--warn-bg); color: var(--warn); border-color: var(--warn); }
.nu-pill--safe { background: var(--safe-bg); color: var(--safe); border-color: var(--safe); }

.nu-badge { display:inline-flex; gap:5px; align-items:center;
            padding:3px 8px; font:500 11px/1.4 var(--sans);
            border:1px solid var(--rule); border-radius:2px;
            letter-spacing: 0.04em; text-transform: uppercase; }
.nu-badge--safe { background: var(--safe-bg); color: var(--safe); border-color: var(--safe); }
.nu-badge--caution { background: var(--paper-deep); color: var(--ink); border-color: var(--rule-strong); }
.nu-badge--warn { background: var(--warn-bg); color: var(--warn); border-color: var(--warn); }
.nu-badge--risk { background: var(--risk-bg); color: var(--risk); border-color: var(--risk); }

/* The PLCS hero — the signature visualization. Pure CSS, no JS. */
.nu-score { display: flex; flex-direction: column; gap: 8px; }
.nu-score-n { font: 400 96px/0.95 var(--serif); color: var(--ink-strong);
              font-variant-numeric: tabular-nums; }
.nu-score-n--risk { color: var(--risk); }
.nu-score-n--warn { color: var(--warn); }
.nu-score-n--safe { color: var(--safe); }
.nu-score-denom { font: 400 22px/1 var(--serif); color: var(--ink-faint); }

.nu-band { position: relative; height: 72px; border: 1px solid var(--rule);
           background: linear-gradient(to right,
             var(--safe-bg)    0%,  var(--safe-bg)    35%,
             var(--paper-deep) 35%, var(--paper-deep) 55%,
             var(--warn-bg)    55%, var(--warn-bg)    75%,
             var(--risk-bg)    75%, var(--risk-bg)    100%); }
.nu-band-marker { position:absolute; top:0; bottom:0; width:2px;
                  background: var(--ink-strong); transform: translateX(-50%); }
.nu-band-marker-pill { position:absolute; top:-24px; left:50%; transform:translateX(-50%);
                       background: var(--ink-strong); color: var(--paper-bg);
                       padding: 3px 8px; font: 600 11px/1 var(--sans);
                       border-radius: 2px; white-space: nowrap; }
.nu-band-analog { position: absolute; top: 50%; transform: translate(-50%,-50%);
                  width: 1px; height: 56px; background: var(--ink-muted); opacity: 0.55; }

/* Confidence bar */
.nu-conf-bar { height: 3px; background: var(--paper-deep); position: relative; }
.nu-conf-fill { position: absolute; inset: 0 auto 0 0; background: var(--ink-strong); }

/* Recommendation band — the dark CTA strip at the bottom of every result */
.nu-cta-band { background: var(--ink-strong); color: var(--paper-bg);
               padding: 28px 40px; display: grid;
               grid-template-columns: 2fr 1fr; gap: 28px; align-items: center;
               border-radius: 2px; }
.nu-cta-band h2 { color: var(--paper-bg); font-family: var(--serif);
                  font-size: 22px; margin: 4px 0 0; }
.nu-cta-band .nu-kicker { color: rgba(245,241,232,0.55); }
.nu-cta-band p { color: rgba(245,241,232,0.75); margin: 8px 0 0;
                 font-family: var(--sans); font-size: 14px; line-height: 1.5; }
"""

# Custom grouped sidebar nav — rendered by render_sidebar() on top of
# st.navigation(position="hidden"). Targets only stable testids + nu- classes.
_SIDEBAR = """
/* No Streamlit auto-nav — render_sidebar() owns the whole sidebar. */
[data-testid="stSidebarNav"] { display: none; }

[data-testid="stSidebar"] .nu-brand-wm {
  font: 700 30px/1 var(--serif); letter-spacing: -0.01em;
  color: var(--ink-strong); padding: 10px 12px 0; }
[data-testid="stSidebar"] .nu-brand-tag {
  font: italic 400 13px/1.3 var(--serif); color: var(--ink-muted);
  padding: 3px 12px 14px; border-bottom: 1px solid var(--rule); }
[data-testid="stSidebar"] .nu-nav-kicker {
  font: 600 10px/1 var(--sans); text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--ink-faint); padding: 20px 12px 10px; }

[data-testid="stSidebar"] [data-testid="stPageLink"] { margin: 0; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  font-family: var(--sans); font-size: 14px; color: var(--ink-muted);
  padding: 6px 12px; border-radius: 2px; border-left: 2px solid transparent;
  letter-spacing: 0.01em; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background: var(--paper-deep); color: var(--ink-strong); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
  color: var(--risk); background: var(--risk-bg);
  border-left: 2px solid var(--risk); font-weight: 600; }

[data-testid="stSidebar"] .nu-nav-footer {
  margin-top: 20px; padding: 12px; border-top: 1px solid var(--rule);
  font: 400 11px/1.5 var(--mono); color: var(--ink-muted); }
[data-testid="stSidebar"] .nu-nav-footer .nu-dot {
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: var(--safe); margin-right: 6px; vertical-align: middle; }

/* Always-visible legal microcopy in the sidebar footer. */
[data-testid="stSidebar"] .nu-legal {
  display: block; margin-top: 8px; font: 400 10px/1.5 var(--sans);
  color: var(--ink-faint); }

/* Sidebar popover triggers (diagnostics, legal) — small + quiet. */
[data-testid="stSidebar"] [data-testid="stPopover"] > button {
  font-size: 11px; padding: 5px 10px; color: var(--ink-faint);
  border-color: var(--rule); margin-top: 10px; }
[data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
  color: var(--ink-muted); }
"""

# Cortex omnibar — the popover trigger styled as a full-width search bar.
# Scoped to stPopover, which is unique to the omnibar (no other popovers).
_OMNI = """
[data-testid="stPopover"] > button {
  width: 100%; max-width: 680px; justify-content: flex-start; text-align: left;
  background: var(--paper-card); border: 1px solid var(--rule-strong);
  color: var(--ink-faint); font-family: var(--sans); font-weight: 400;
  font-size: 13px; border-radius: 2px; padding: 9px 14px; letter-spacing: 0.01em; }
[data-testid="stPopover"] > button:hover {
  border-color: var(--ink-muted); background: var(--paper-card);
  color: var(--ink-muted); }

/* The popover panel needs room so the placeholder + form hint don't collide. */
[data-testid="stPopoverBody"] { min-width: 460px; }

/* Topbar breadcrumb (left of the omnibar) — quiet, so the headline dominates. */
.nu-crumb { font: 500 12px/1.6 var(--mono); color: var(--ink-faint);
            letter-spacing: 0.04em; }
"""


def inject_css():
    """Call once per page, right after st.set_page_config()."""
    st.markdown(f"<style>{_TOKENS}{_BASE}{_COMPONENTS}{_SIDEBAR}{_OMNI}</style>",
                unsafe_allow_html=True)
