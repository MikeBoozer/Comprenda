# Local preview harness (mock mode)

Render the Comprenda Streamlit app in a browser **without Snowflake** — no trial
credits, no Snowflake connection (so Norton's TLS interception is a non-issue),
fixture data only. This is the rig for the §9 critique loop: view a page, compare
it side-by-side with the matching artboard in `design/index.html`, screenshot,
iterate.

## Run it

```powershell
! streamlit\_harness\run.ps1
```

First run builds a venv under `_harness/.venv` and installs `streamlit` + `altair`
(snowpark + pandas are reused from the system Python via `--system-site-packages`).
Then it opens `http://localhost:8501`.

## How it works

- `sitecustomize.py` is auto-imported by Python at interpreter startup (the
  launcher puts `_harness/` on `PYTHONPATH`). It runs *before* any app code.
- It patches `snowflake.snowpark.context.get_active_session` to return a
  `FakeSession`, and pre-seeds `sys.modules['lib.comprenda_queries']` with
  fixture-backed stubs, so every page gets realistic data with zero SQL.
- `fixtures.py` holds the mock data. Shapes are grounded in the real contracts
  (`snowpark/deploy_plcs.py`, `snowpark/deploy_ai_brief.py`,
  `lib/comprenda_queries.py`), so the screens reflect what the app actually
  returns rather than invented values.

## What it does NOT cover

This is the ~80% proxy described in the design handoff §10.3. It will **not**
reveal: whether real `SCORE_CONTENT`/`GENERATE_BRIEF` JSON fits the layout,
whether the trial role's permissions allow the SQL, or whether SiS falls back
past the serif to Georgia on a Windows VDI. Snowsight also wraps the app in its
own chrome that this local render doesn't reproduce. Do one real Snowflake
deploy at the end as the source-of-truth QA pass.

## Production safety

Nothing here ships to Snowflake. Production never sets the harness `PYTHONPATH`,
so `sitecustomize.py` is inert outside the launcher. Don't upload `_harness/`
when deploying.
