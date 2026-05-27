# Claude Code — Project Nuance entry point

Welcome. This is Project Nuance — a Snowflake-native cultural intelligence SaaS.

**New to the repo this session?** Skim two files to orient, then stop: **`README.md`** (overview + file layout) and **`docs/00_executive_summary.md`** (what the product is). Everything else is reference — pull it *when the task calls for it*, using the map below. Don't read it all up front.

**Read when you're about to…**

- **Deploy or change the live Streamlit app** → `docs/09_streamlit_ops_runbook.md`. Editing `streamlit/` or the Snowsight workspace does **not** update the running app.
- **Touch `streamlit/` styling or the UI redesign** → `docs/11_ui_ux_design_brief.md` (locked design decisions + SiS guardrails).
- **Debug unexpected behavior or an error** → `docs/07_audit_and_fixes.md` (residual-risks + fixes), plus the "When something fails" section below.
- **Work on features or check the ICP** → `docs/01_product_design.md` (feature inventory F1–F10, ICP).
- **Check current state / before the native-app build** → `docs/10_project_status.md` (living snapshot + **binding open items**).
- **Recover *why* a decision was made** → `docs/decisions/` (ADRs) and `docs/08_build_session_transcript.md` (build-session transcript).
- **Understand the architecture** → `docs/06_architecture.md` (technical decisions + reasoning).
- **See the plan / operator steps** → `docs/02_master_plan.md` (29-day plan), `docs/03_runbook.md` (day-by-day operator actions), `QUICKSTART.md` (deploy checklist).

Background, rarely needed inline: `docs/04_business_model.md`, `docs/05_credit_budget.md`, `archive/` (read-only history).

The other top-level directories are:

- `snowflake/` — SQL setup pack (bootstrap + per-stage scripts).
- `snowpark/` — Python UDFs + stored procedures (deploy with `python snowpark/deploy*.py`).
- `streamlit/` — the Streamlit-in-Snowflake app (`nuance_app.py` + `pages/`).
- `semantic_model/` — Cortex Analyst YAML.
- `native_app/` — Snowflake Native App manifest + setup_script for Marketplace.
- `mcp/` — Nuance MCP server (Claude Desktop / Cursor / enterprise agents).
- `data/` — demo data generator, GDELT/HuggingFace loaders, analog library seeder.
- `prompts/` — versioned prompt templates referenced by the stored procedures.
- `go_to_market/` — landing page, pricing, cold emails, demo script, ICP research workflow.
- `archive/` — original CulturePulse plan + Snowflake AI playbook (read-only history).

## Working in this repo

- **Snowflake credentials** live in `~/.snowflake/config.toml`. Template: `data/snowflake_config.template.toml`.
- **Model identifiers** are centralized in the `nuance_db.internal.config` table created by `snowflake/00_bootstrap.sql`. If a Cortex model is renamed, update one row there.
- **Prompts** are versioned in `prompts/`. The `prompt_version` is recorded on every inference row.
- **Idempotency**: every SQL script is safe to re-run. Snowpark deploy scripts use `replace=True`.
- **Credit guard**: a resource monitor caps total trial spend at 300 of the 400 credits.
- **Architecture decisions** are recorded as ADRs in `docs/decisions/` (numbered, append-only). Read them to recover *why* a structural choice was made; when a decision changes, add a new ADR that supersedes the old one rather than editing it.
- **Deploying the live Streamlit app**: the running app serves from the Streamlit object's own stage — editing `streamlit/` or the Snowsight workspace does NOT update it. Follow the CLI deploy sequence in `docs/09_streamlit_ops_runbook.md` (`ALTER STREAMLIT … ABORT → ADD LIVE VERSION FROM LAST → PUT → COMMIT`).

## When something fails

- "Function CORTEX.X does not exist" → Cortex AI not enabled. Snowflake UI → Admin → Cortex → enable.
- "Model 'claude-4-sonnet' not found" → swap the model name in `nuance_db.internal.config` after checking `SELECT * FROM TABLE(SNOWFLAKE.CORTEX.LIST_MODELS())`.
- Streamlit import error → confirm `streamlit/lib/__init__.py` made it into the Snowflake-side file tree.
- Deployed app won't update / shows old behavior / Deploy button missing / `ModuleNotFoundError` → see `docs/09_streamlit_ops_runbook.md` (covers stale SPCS container, the CLI deploy sequence, and the package set).
- Any other error → check `docs/07_audit_and_fixes.md` for the residual-risks section first; many gotchas are pre-documented.
