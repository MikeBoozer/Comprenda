# ADR-0002: Reconcile the diverged Snowsight-workspace app copy with the git repo during native-app packaging

- **Status:** Accepted
- **Date:** 2026-05-26
- **Deciders:** Mike (operator)

## Context

Discovered 2026-05-26 (verified via the `snow` CLI against the `default` connection) that
the running Streamlit app and the git repo are **two separate, manually-diverged file
trees**:

- **Deployed:** Streamlit object `NUANCE_DB.OUTPUTS.NUANCE_APP` (title "nuance"),
  `main_file = streamlit_app.py`, served from a Snowsight **Workspace**
  `USER$.PUBLIC.DEFAULT$/nuance_app` — **not git-backed** (no commit hash). Contains
  `streamlit_app.py`, `.streamlit/config.toml`, `snowflake.yml`, `pyproject.toml`,
  `pages/`, `lib/`. **No `environment.yml`.**
- **Repo** (`C:\Users\micha\Nuance\streamlit`): entry file `nuance_app.py`, plus
  `environment.yml`; no `.streamlit/`, `snowflake.yml`, or `pyproject.toml`.
- `pages/` and `lib/` filenames match across both; the entry-file name differs
  (`streamlit_app.py` vs `nuance_app.py`).

Consequences already observed from this split:
- Editing repo files does **not** change the running app — the workspace is edited in
  Snowsight, independent of the repo.
- The repo's `environment.yml` (which listed `plotly`) was never deployed, so the chart
  pages threw `ModuleNotFoundError: plotly` while the deployed package set is only
  `python==3.11.*, snowflake-snowpark-python, streamlit`. (Altair ships inside Streamlit,
  so the Altair chart rewrite needs no package change.)
- The "streamlit app" sidebar label is simply the `streamlit_app.py` filename.

## Decision

Two-part:

1. **Now:** apply the current round of fixes — Altair chart conversion, the Drift-Alerts
   and AI-Brief bug fixes, and the home-page "Overview" relabel — **directly into the
   deployed Snowsight workspace** so they go live through the operator's existing Deploy
   step, rather than blocking ready fixes on a full reconciliation.
2. **Deferred to the native-app packaging session (Day 23):** consolidate to a **single
   source of truth**. The native-app build already requires authoring `snowflake.yml`
   artifacts and re-targeting schema references, so the workspace/repo split must be
   resolved there. Target end state: **the git repo is canonical** and the deployed app
   is produced from it (CLI deploy or a git-backed workspace), eliminating the manual
   two-tree drift.

## Alternatives considered

- **Reconcile now, before shipping these fixes.** Rejected for now — reconciliation is
  entangled with the native-app `snowflake.yml`/artifacts work and would delay simple,
  already-tested bug fixes. Recorded here so it is not lost.
- **Keep two trees indefinitely, syncing by hand.** Rejected — manual drift already
  produced a shipped failure (undeclared `plotly`) and divergent entry filenames, and
  will keep producing "fixed in the repo but not live" confusion.

## Consequences

**Positive**
- Current fixes ship without waiting on a larger refactor.
- The divergence is now documented and verified rather than folkloric.

**Negative / follow-up (binding)**
- Until the native-app session reconciles them, the **repo is not authoritative** for
  what is deployed: any repo-only edit is NOT live until pushed into the workspace.
- The native-app packaging session **MUST** perform this reconciliation — it is a
  prerequisite of that work, not optional cleanup. This ADR is the binding reminder.
- **Demo-data fitness is in scope of that same data-bundling work.** Live-data findings
  (uneven ~17× duplication; and — more importantly — all CDS scores < 0.20, so the
  headline divergence feature shows nothing "meaningful") are recorded in
  `docs/07_audit_and_fixes.md` → "Data-quality findings (2026-05-26)". The flat-CDS root
  cause must be diagnosed and the demo corpus rebuilt to demonstrate real divergence
  before the marketplace listing.

## Notes

Deployment-architecture specifics (object name, workspace URI, package set, write path)
are also captured in Claude auto-memory under `streamlit-deploy-workflow`. This ADR is the
canonical record; external notes link here.
