"""Exercise the Cultural Translator interactions: click the sample button
(widget-key callback path), click Generate, then click the opt-in Re-score
button (composes call_plcs) and render the risk comparison.

Run from streamlit/ with the harness venv python:
    python _harness/probe_translator.py
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
at = AppTest.from_file("views/2_Cultural_Translator.py", default_timeout=60).run()
if at.exception:
    _fail(at, "initial empty render")
sample_btns = [b for b in at.button if "sample" in b.label.lower()]
assert sample_btns, "no sample button found"
sample_btns[0].click().run()
if at.exception:
    _fail(at, "click 'use sample' (callback)")
assert at.session_state["translator_source"] == SAMPLE, "sample did not fill source"

# 2. Click Generate → variant cards render.
gen = [b for b in at.button if "Generate adapted variants" in b.label]
assert gen, "Generate button not found"
gen[0].click().run()
if at.exception:
    _fail(at, "generated render")
assert "translator_results" in at.session_state, "results not persisted"

# 3. Click the opt-in Re-score button → risk comparison renders (call_plcs path).
rescore = [b for b in at.button if "Re-score" in b.label]
assert rescore, "Re-score button not found"
rescore[0].click().run()
if at.exception:
    _fail(at, "re-scored render")
assert "translator_rescored" in at.session_state, "re-scored data not persisted"

print(f"ok — sample + generate + re-score clean. "
      f"markdown blocks: {sum(1 for _ in at.markdown)}, "
      f"rescored: {at.session_state['translator_rescored']}")
