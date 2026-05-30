"""Public demo entry — Streamlit Community Cloud / Hugging Face Spaces.

Runs the REAL Comprenda app (router + all 10 pages) on illustrative fixture data
with NO Snowflake connection. It reuses the same mock layer the local `_harness/`
uses, but self-contained so it works on a cloud host that (a) can't set
PYTHONPATH the way run.ps1 does and (b) may not have `snowflake-snowpark-python`
installed.

DEPLOY (Streamlit Community Cloud):
  - Repo: this repo. Branch: main. **Main file path: `streamlit/demo_app.py`.**
  - Dependencies: `streamlit/requirements.txt` (streamlit, pandas, altair).
    If the host instead picks up `streamlit/environment.yml` (the in-Snowflake
    conda env, which includes snowpark), the demo STILL works — get_active_session
    is force-overridden below regardless — it just builds heavier.
  - No secrets are needed or read. The app never connects to Snowflake here.

This file is demo-only; production (Streamlit-in-Snowflake) runs `comprenda_app.py`
directly and never imports this.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

# 1. Make `lib`, `views`, and the harness `fixtures` importable.
HERE = Path(__file__).resolve().parent            # .../streamlit
HARNESS = HERE / "_harness"
for _p in (str(HERE), str(HARNESS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fixtures  # noqa: E402  (lives in _harness/)

# 2. Ensure `snowflake.snowpark.context` imports even when the connector is not
#    installed (cloud hosts won't have it), then FORCE get_active_session to
#    return the fixture session whether or not the real package is present.
try:
    import snowflake.snowpark.context as _ctx  # type: ignore
except Exception:
    _sf = sys.modules.setdefault("snowflake", types.ModuleType("snowflake"))
    _sp = sys.modules.setdefault("snowflake.snowpark", types.ModuleType("snowflake.snowpark"))
    _ctx = sys.modules.setdefault(
        "snowflake.snowpark.context", types.ModuleType("snowflake.snowpark.context"))

    class _Session:  # placeholder so `from snowflake.snowpark import Session` resolves
        pass

    _sp.Session = _Session
    _sp.context = _ctx
    _sf.snowpark = _sp
_ctx.get_active_session = lambda: fixtures.FakeSession()

# 3. Replace the query module with fixture-backed stubs so no SQL ever runs.
sys.modules["lib.comprenda_queries"] = fixtures.build_query_module()

# 4. Run the real router in this module's namespace. Streamlit reruns this file
#    on each interaction, so the router re-executes each time, as expected.
_router = HERE / "comprenda_app.py"
exec(compile(_router.read_text(encoding="utf-8"), str(_router), "exec"))

# 5. Honest demo banner — appended to the sidebar after the app's own chrome
#    (can't render before exec: comprenda_app.py owns the first st.set_page_config).
import streamlit as st  # noqa: E402

st.sidebar.markdown(
    "<div style='margin-top:12px; padding:8px 10px; border:1px solid #BF6C4B;"
    " border-radius:6px; font:400 12px/1.45 system-ui;'>"
    "<b style='color:#8B2A1F;'>Demo mode</b><br>"
    "<span style='color:#5b5b5b;'>Illustrative sample data — no live Snowflake. "
    "The production app runs inside Snowflake on Cortex.</span></div>",
    unsafe_allow_html=True)
