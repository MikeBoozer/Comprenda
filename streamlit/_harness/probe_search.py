"""Exercise the button-gated result paths on the consistency-pass pages:
Analog Retrieval (sample callback -> Find -> analog cards) and Narrative Search
(type query -> Search -> result cards). These render real fields, so a wrong
column/key name surfaces here, not in check.py (which only renders defaults).

Run from streamlit/ with the harness venv python:
    python _harness/probe_search.py
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


# --- Analog Retrieval: sample (callback) -> Find -> analog cards -----------
at = AppTest.from_file("views/7_Analog_Retrieval.py", default_timeout=60).run()
if at.exception:
    _fail(at, "Analog initial render")
sample = [b for b in at.button if "example" in b.label.lower()]
assert sample, "Analog sample button not found"
sample[0].click().run()
if at.exception:
    _fail(at, "Analog sample click (callback)")
find = [b for b in at.button if "Find analogs" in b.label]
assert find, "Find analogs button not found"
find[0].click().run()
if at.exception:
    _fail(at, "Analog results render")
assert "analog_results" in at.session_state, "analog results not persisted"

# --- Narrative Search: type query -> Search -> result cards ----------------
at2 = AppTest.from_file("views/9_Narrative_Search.py", default_timeout=60).run()
if at2.exception:
    _fail(at2, "Narrative initial render")
at2.text_input(key="nsearch_q").set_value("launch reaction").run()
search = [b for b in at2.button if b.label == "Search"]
assert search, "Search button not found"
search[0].click().run()
if at2.exception:
    _fail(at2, "Narrative results render")
assert "nsearch_results" in at2.session_state, "search results not persisted"

print(f"ok — analog cards + search cards render clean. "
      f"analog markdown: {sum(1 for _ in at.markdown)}, "
      f"search markdown: {sum(1 for _ in at2.markdown)}")
