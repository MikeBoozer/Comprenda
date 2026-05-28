"""Exercise the Divergence Matrix populated path (an event selected).

Run from streamlit/ with the harness venv python:
    python _harness/probe_matrix.py
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

at = AppTest.from_file("pages/4_Divergence_Matrix.py", default_timeout=60)
at.session_state["matrix_event"] = fixtures.EVENT_TAGS[0]
at.run()

if at.exception:
    print("FAIL — exceptions on populated render:")
    for e in at.exception:
        print("   ", e.value)
    raise SystemExit(1)

print(f"ok — matrix populated render clean. markdown blocks: {sum(1 for _ in at.markdown)}")
