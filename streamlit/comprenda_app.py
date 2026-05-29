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
from lib.comprenda_components import render_sidebar, omnibar

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
omnibar(get_active_session())
pg.run()
