"""Exercise the PLCS interactions: click the sample button (callback path),
then click Score and render results.

Run from streamlit/ with the harness venv python:
    python _harness/probe_plcs.py
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

SAMPLE = "Live Free, Drive Fast — the new electric sports car that puts you first."


def _fail(at, where):
    print(f"FAIL — exceptions on {where}:")
    for e in at.exception:
        print("   ", e.value)
    raise SystemExit(1)


# 1. Fresh empty state, then click the sample button (widget-key callback path).
at = AppTest.from_file("views/1_Pre_Launch_Risk.py", default_timeout=60).run()
if at.exception:
    _fail(at, "initial empty render")
sample_btns = [b for b in at.button if "sample" in b.label.lower()]
assert sample_btns, "no sample button found"
sample_btns[0].click().run()
if at.exception:
    _fail(at, "click 'use sample' (callback)")
assert at.session_state["plcs_draft"] == SAMPLE, "sample did not fill draft"

# 2. Click Score → results render.
score = [b for b in at.button if "Score cultural risk" in b.label]
assert score, "Score button not found"
score[0].click().run()
if at.exception:
    _fail(at, "scored render")

print(f"ok — sample click + scored render clean. "
      f"markdown blocks: {sum(1 for _ in at.markdown)}, "
      f"results in state: {'plcs_results' in at.session_state}")
