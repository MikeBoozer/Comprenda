"""Headless smoke check: run every page through Streamlit's AppTest under mock
mode and report any uncaught exceptions.

This executes each script top-to-bottom with fixture data (no Snowflake), which
catches import errors, bad attribute access, and template bugs. It does NOT
verify visual fidelity — that still needs the browser (run.ps1) compared with
design/index.html.

Usage (from the streamlit/ directory, with the harness venv python):
    python _harness/check.py            # all pages
    python _harness/check.py comprenda_app.py pages/1_Pre_Launch_Risk.py
"""
import os
import sys

# Activate the same stubs sitecustomize installs, in-process.
_HARNESS = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_HARNESS)  # streamlit/
for _p in (_HARNESS, _APP_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import fixtures  # noqa: E402

import snowflake.snowpark.context as _ctx  # noqa: E402
_ctx.get_active_session = lambda: fixtures.FakeSession()

# Import the real lib package first so its __path__ is set and the real
# theme/components submodules resolve, then override only the queries submodule.
import lib  # noqa: E402,F401
_fake_q = fixtures.build_query_module()
sys.modules["lib.comprenda_queries"] = _fake_q
lib.comprenda_queries = _fake_q

from streamlit.testing.v1 import AppTest  # noqa: E402

DEFAULT_TARGETS = [
    "comprenda_app.py",
    "pages/0_Overview.py",
    "pages/1_Pre_Launch_Risk.py",
    "pages/2_Cultural_Translator.py",
    "pages/3_Event_Explorer.py",
    "pages/4_Divergence_Matrix.py",
    "pages/5_Frame_Distribution.py",
    "pages/6_Drift_Alerts.py",
    "pages/7_Analog_Retrieval.py",
    "pages/8_AI_Brief.py",
    "pages/9_Narrative_Search.py",
]


def check(path):
    try:
        at = AppTest.from_file(path, default_timeout=30).run()
    except Exception as exc:  # construction / fatal error
        return [f"FATAL: {type(exc).__name__}: {exc}"]
    return [f"{e.value}" for e in at.exception]


def main(argv):
    targets = argv or DEFAULT_TARGETS
    failed = 0
    for t in targets:
        norm = t.replace("\\", "/")
        errors = check(norm)
        if errors:
            failed += 1
            print(f"FAIL  {norm}")
            for e in errors:
                print(f"        {e}")
        else:
            print(f"ok    {norm}")
    print(f"\n{len(targets) - failed}/{len(targets)} pages ran clean.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
