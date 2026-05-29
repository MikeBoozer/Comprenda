"""Exercise the session-diagnostics footer on the router: click 'Load details'
and confirm the (fixture) session context + corpus freshness render.

Run from streamlit/ with the harness venv python:
    python _harness/probe_diag.py
"""
import os
import sys

_HARNESS = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_HARNESS)
for _p in (_HARNESS, _APP_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import fixtures  # noqa: E402

import snowflake.snowpark.context as _ctx  # noqa: E402
_ctx.get_active_session = lambda: fixtures.FakeSession()
import lib  # noqa: E402,F401
_fake_q = fixtures.build_query_module()
sys.modules["lib.comprenda_queries"] = _fake_q
lib.comprenda_queries = _fake_q

from streamlit.testing.v1 import AppTest  # noqa: E402


def _fail(at, where):
    print(f"FAIL — exceptions on {where}:")
    for e in at.exception:
        print("   ", e.value)
    raise SystemExit(1)


at = AppTest.from_file("comprenda_app.py", default_timeout=60).run()
if at.exception:
    _fail(at, "router initial render")

load = [b for b in at.button if b.label == "Load details"]
assert load, "diagnostics 'Load details' button not found"
load[0].click().run()
if at.exception:
    _fail(at, "diagnostics load")

assert "diag" in at.session_state, "diag not persisted"
diag = at.session_state["diag"]
assert diag.get("ctx"), "session context empty"
assert diag.get("fresh"), "corpus freshness empty"
print(f"ok — diagnostics load clean. context keys: {len(diag['ctx'])}, "
      f"fresh: {diag['fresh']}")
