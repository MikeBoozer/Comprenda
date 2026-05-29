"""Exercise the Divergence Matrix interactions: from the empty state, click an
"Open ->" button (widget-key callback path) and render the populated view.

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


def _fail(at, where):
    print(f"FAIL — exceptions on {where}:")
    for e in at.exception:
        print("   ", e.value)
    raise SystemExit(1)


# Empty state by default (placeholder event).
at = AppTest.from_file("views/4_Divergence_Matrix.py", default_timeout=60).run()
if at.exception:
    _fail(at, "initial empty render")

# Click the first "Open ->" button (callback sets the widget-keyed event).
opens = [b for b in at.button if "Open" in b.label and "explorer" not in b.label.lower()]
assert opens, "no Open button found"
opens[0].click().run()
if at.exception:
    _fail(at, "click 'Open ->' (callback)")
# AppTest session_state has no .get(); access by key.
ev = at.session_state["matrix_event"]
assert ev and ev != "— pick an event —", f"event not selected after click: {ev!r}"

print(f"ok — open-event click + populated render clean. "
      f"markdown blocks: {sum(1 for _ in at.markdown)}, event: {ev}")
