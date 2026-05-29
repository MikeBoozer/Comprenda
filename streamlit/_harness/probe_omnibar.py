"""Exercise the Cortex omnibar on the router: open the popover, submit a query
through the form, and render Cortex Search results. The omnibar is rendered by
comprenda_app.py (the st.navigation router), so this drives the router.

Run from streamlit/ with the harness venv python:
    python _harness/probe_omnibar.py
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


# Run the router (renders sidebar + omnibar + the default Overview page).
at = AppTest.from_file("comprenda_app.py", default_timeout=60).run()
if at.exception:
    _fail(at, "router initial render")

# Fill the omnibar query and submit the form.
assert at.text_input, "no text inputs found (omnibar form missing?)"
at.text_input[0].set_value("launch reaction")
# Find the omnibar's form submit by label (the sidebar diagnostics popover also
# renders a button, so index-0 is no longer reliable).
submit = [b for b in at.button if b.label == "Search"]
assert submit, "omnibar Search submit not found"
submit[0].click().run()
if at.exception:
    _fail(at, "omnibar search submit")

assert "omni_results" in at.session_state, "omni_results not persisted"
n = 0 if at.session_state["omni_results"] is None else len(at.session_state["omni_results"])
print(f"ok — omnibar search clean. results persisted: {n} rows")
