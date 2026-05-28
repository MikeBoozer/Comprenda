"""Local preview harness activation (auto-imported by Python at startup).

Python imports a module named ``sitecustomize`` automatically during interpreter
initialization if it is importable on ``sys.path``. The launcher puts this
``_harness/`` directory on PYTHONPATH, so this runs *before* Streamlit executes
any app code — early enough to (1) patch ``get_active_session`` and (2) pre-seed
``sys.modules['lib.comprenda_queries']`` with fixture-backed stubs.

Production never sets that PYTHONPATH, so this file is inert outside the harness.
"""
import sys

try:
    import fixtures
except Exception as exc:  # pragma: no cover - harness only
    print(f"[harness] could not import fixtures: {exc}", file=sys.stderr)
    fixtures = None

if fixtures is not None:
    # 1. Patch get_active_session() to return the fake Snowpark session.
    try:
        import snowflake.snowpark.context as _ctx
        _ctx.get_active_session = lambda: fixtures.FakeSession()
    except Exception as exc:  # pragma: no cover
        print(f"[harness] could not patch get_active_session: {exc}", file=sys.stderr)

    # 2. Pre-seed the query module so `from lib.comprenda_queries import ...`
    #    resolves to fixtures instead of running SQL. Pages import it after this.
    sys.modules["lib.comprenda_queries"] = fixtures.build_query_module()

    print("[harness] MOCK MODE active — no Snowflake connection, fixture data only.",
          file=sys.stderr)
