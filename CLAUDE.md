# Claude Code — Project Nuance entry point

Welcome. This is Project Nuance — a Snowflake-native cultural intelligence SaaS. If you (Claude Code) are entering this directory for the first time in a session, read these files in order:

1. **`README.md`** — top-of-stack overview, file layout, quick start.
2. **`QUICKSTART.md`** — 30-second-read deploy checklist.
3. **`docs/00_executive_summary.md`** — what the product is and what changed from the predecessor CulturePulse plan.
4. **`docs/01_product_design.md`** — feature inventory (F1–F10) and ICP definition.
5. **`docs/02_master_plan.md`** — 29-day build plan.
6. **`docs/03_runbook.md`** — exact actions Mike (the operator) does, day by day.
7. **`docs/06_architecture.md`** — technical architecture and the reasoning behind key decisions.
8. **`docs/07_audit_and_fixes.md`** — bugs caught in pre-flight audit and the fixes applied. Read this if you hit any unexpected behavior during deployment.
9. **`docs/08_build_session_transcript.md`** — full transcript of the chat session that produced this repo. Use this to recover *why* a decision was made.
10. **`docs/09_streamlit_ops_runbook.md`** — how to inspect/edit/**deploy** the live Streamlit app from the CLI. **Read this before changing the running app** — editing repo or workspace files does NOT update it.
11. **`docs/10_project_status.md`** — living snapshot of current state + **binding open items** (read before the native-app build). Kept separate so this file stays lean.

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
