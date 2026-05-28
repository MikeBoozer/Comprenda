"""Exercise the PLCS scored path: fill the draft, click Score, render results.

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

at = AppTest.from_file("pages/1_Pre_Launch_Risk.py", default_timeout=60)
at.session_state["plcs_draft"] = SAMPLE
at.run()

btns = [b for b in at.button if "Score cultural risk" in b.label]
assert btns, "Score button not found"
btns[0].click().run()

if at.exception:
    print("FAIL — exceptions on scored render:")
    for e in at.exception:
        print("   ", e.value)
    raise SystemExit(1)

# Surface what rendered, as a sanity check.
heads = [h.value for h in at.subheader] if hasattr(at, "subheader") else []
mds = sum(1 for _ in at.markdown)
print(f"ok — scored render clean. markdown blocks: {mds}, "
      f"results in state: {'plcs_results' in at.session_state}")
