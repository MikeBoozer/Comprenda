"""Exercise the AI Brief: click Generate, then render the populated brief
(markdown parse + figures).

Run from streamlit/ with the harness venv python:
    python _harness/probe_brief.py
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


# Pre-gen: panel + inputs.
at = AppTest.from_file("pages/8_AI_Brief.py", default_timeout=60).run()
if at.exception:
    _fail(at, "pre-gen render")

# Click Generate brief -> on success the page reruns into the populated brief.
gen = [b for b in at.button if "Generate brief" in b.label]
assert gen, "Generate button not found"
gen[0].click().run()
if at.exception:
    _fail(at, "generate + brief render")

assert "brief_result" in at.session_state, "brief not stored"
print(f"ok — generate + brief render clean. markdown blocks: {sum(1 for _ in at.markdown)}")
