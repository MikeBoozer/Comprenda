"""Headless smoke test for the public demo on real exported fixtures.

Runs the full demo router and every view through Streamlit's AppTest and asserts
no uncaught exceptions. Exercised with the harness venv:
    _harness/.venv/Scripts/python.exe _harness/_smoke.py
"""
import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../streamlit/_harness
STREAMLIT = HERE.parent                          # .../streamlit
for p in (str(STREAMLIT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["COMPRENDA_DEMO"] = "1"

# Set up the same swap demo_app.py / sitecustomize.py perform, so views imported
# directly resolve lib.comprenda_queries -> fixtures and get_active_session -> fake.
import fixtures
import snowflake.snowpark.context as _ctx
_ctx.get_active_session = lambda: fixtures.FakeSession()
sys.modules["lib.comprenda_queries"] = fixtures.build_query_module()

from streamlit.testing.v1 import AppTest  # noqa: E402

targets = ["demo_app.py"] + [f"views/{p.name}" for p in
                             sorted((STREAMLIT / "views").glob("*.py"))]

failures = 0
for rel in targets:
    path = str(STREAMLIT / rel)
    try:
        at = AppTest.from_file(path, default_timeout=30).run()
        if at.exception:
            failures += 1
            print(f"FAIL  {rel}")
            for ex in at.exception:
                print(f"      {ex.type}: {ex.message}")
        else:
            print(f"ok    {rel}")
    except Exception as exc:  # AppTest itself blew up
        failures += 1
        print(f"ERROR {rel}: {type(exc).__name__}: {exc}")

print(f"\n{'PASS' if failures == 0 else 'FAILURES: ' + str(failures)}")
sys.exit(1 if failures else 0)
