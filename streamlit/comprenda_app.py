"""Comprenda — Cultural Intelligence Platform · router + chrome.

Uses st.navigation (Streamlit >= 1.36) to register every page explicitly and
render the editorial grouped sidebar (Workbench / Analysis / Synthesis) via
render_sidebar(). The Overview/home content lives in views/0_Overview.py; this
file is now purely the router + shared chrome.

DEPLOY NOTE: st.navigation requires the Streamlit-in-Snowflake runtime to be
>= 1.36. Verify the SiS Streamlit version on deploy — older runtimes lack
st.navigation and the app will not start. (Harness runs 1.58, so dev is fine.)
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_theme import inject_css
from lib.comprenda_components import render_sidebar, omnibar, session_diagnostics, demo_note

st.set_page_config(page_title="Comprenda — Cultural Intelligence",
                   layout="wide", initial_sidebar_state="expanded")

# (path, title, glyph) grouped into the three editorial sections. Order, titles,
# and glyphs match the design artboard (screens.jsx NAV_ITEMS); titles override
# Streamlit's filename-derived labels.
_NAV_SPEC = [
    ("Workbench", [
        ("views/0_Overview.py", "Overview", "◉"),
        ("views/1_Pre_Launch_Risk.py", "Pre-launch risk", "◐"),
        ("views/2_Cultural_Translator.py", "Cultural translator", "⇄"),
        ("views/3_Event_Explorer.py", "Event explorer", "◇"),
    ]),
    ("Analysis", [
        ("views/4_Divergence_Matrix.py", "Divergence matrix", "▦"),
        ("views/5_Frame_Distribution.py", "Frame distribution", "▥"),
        ("views/6_Drift_Alerts.py", "Drift alerts", "◔"),
        ("views/7_Analog_Retrieval.py", "Analog retrieval", "◊"),
    ]),
    ("Synthesis", [
        ("views/8_AI_Brief.py", "AI brief", "▤"),
        ("views/9_Narrative_Search.py", "Narrative search", "∃"),
    ]),
]

# Build st.Page objects once; reuse them for both the router and the sidebar.
groups = []
for _section, _items in _NAV_SPEC:
    _built = []
    for _path, _title, _glyph in _items:
        _page = st.Page(_path, title=_title, default=(_path == "views/0_Overview.py"))
        _built.append((_page, _glyph))
    groups.append((_section, _built))

ordered_pages = [page for _section, items in groups for page, _glyph in items]

pg = st.navigation(ordered_pages, position="hidden")
inject_css()
render_sidebar(groups)

session = get_active_session()
# SPCS containers start with the wrong warehouse/database context; pin it once, before
# any page query runs. Moved here from the old deployed home file per ADR-0004 (the repo
# home file lacked it). Harmless in the local harness (FakeSession.sql is a no-op).
#
# BEST-EFFORT: inside the installed Native App, nuance_db / nuance_dev_wh are NOT
# accessible — the app already runs in its own database with the consumer's warehouse.
# Without this guard the first USE throws "Object does not exist" and every page errors
# right after the sidebar renders. The comprenda_queries resolver then detects app mode
# on its own (it probes app_data.config), so skipping these pins in the app is correct.
try:
    session.sql("USE WAREHOUSE nuance_dev_wh").collect()
    session.sql("USE DATABASE nuance_db").collect()
except Exception:
    pass
session_diagnostics(session)  # small popover at the bottom of the sidebar

# Top utility bar: breadcrumb (left) + quiet Cortex search pill (right), per the
# artboard topbar — keeps each page's headline the dominant element.
active_section = next(
    (s for s, items in groups for p, _g in items if p.title == pg.title), "")
crumb_l, crumb_r = st.columns([2, 1], vertical_alignment="center")
crumb_l.markdown(
    f"<div class='nu-crumb'>{active_section}{' / ' if active_section else ''}"
    f"{pg.title}</div>", unsafe_allow_html=True)
with crumb_r:
    omnibar(session)

# In the public demo, LLM-output pages return fixed worked examples (the fixtures
# ignore user input), so flag that to avoid the canned output reading as a bug.
# No-op in the live app (demo_note() checks the demo flag).
_DEMO_LLM_PAGES = {"Pre-launch risk", "Cultural translator", "Analog retrieval",
                   "AI brief", "Narrative search"}
if pg.title in _DEMO_LLM_PAGES:
    demo_note()
pg.run()
