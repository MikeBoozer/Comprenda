# ADR-0004: Cut the deployed app over to the git repo now (supersedes ADR-0002's reconciliation)

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** Mike (operator)
- **Supersedes:** [ADR-0002](0002-reconcile-workspace-repo-divergence.md)

## Context

[ADR-0002](0002-reconcile-workspace-repo-divergence.md) (2026-05-26) deferred resolving the
three diverged file trees (git repo / Snowsight workspace / Streamlit-object stage) to the
native-app packaging session, framing it as a *reconciliation of diverged peers* and, in the
interim, shipping fixes by editing the **Snowsight workspace** directly.

Three things have overtaken that framing:

1. **The entire Comprenda UI redesign was built in the git repo and nowhere else** —
   `st.navigation` router (`comprenda_app.py`), the `views/` page tree, the editorial theme
   (`lib/comprenda_theme.py` / `comprenda_components.py`). The trees are no longer drifted
   *copies of one app*: the **repo holds the actual product**, while the Snowsight workspace
   and the deployed stage hold the **stale, pre-redesign Nuance app**.
2. **Sequencing decided this session:** deploy-QA the redesign *before* the native-app build
   (highest-uncertainty risk — the `st.navigation` runtime — and most expensive failure mode,
   so flush it first). There is no path to a live redesigned app that does not push
   repo → stage, so the cutover happens *now*, not at the native-app session.
3. **Norton TLS interception is resolved** — the `snow` CLI control-plane path is verified
   working from Claude Code (2026-05-29: `snow connection test` → `Status OK`, `LIST`/
   `DESCRIBE` succeed), so the operator no longer has to hand-run the deploy. (The S3/`PUT`
   path is a separate Norton exclusion; verify before the full cutover — see Consequences.)

Point-in-time deployed state (will be false after the cutover): object
`NUANCE_DB.OUTPUTS.NUANCE_APP` serves `VERSION$8`, `main_file = nuance.py`, workspace-backed
(`git_commit_hash: null`), `default_packages` only (no `user_packages`), with old-structure
files on the stage (`nuance.py`, `lib/nuance_queries.py`, a 9-file `pages/` tree,
`pyproject.toml`, `snowflake.yml`).

## Decision

Keep ADR-0002's **goal** (the repo is the single source of truth; eliminate manual drift),
but replace its **mechanism** and **timing**:

1. **The git repo is canonical. The Snowsight workspace is abandoned, not reconciled.**
   There is nothing to merge — the workspace holds only the superseded app. We stop treating
   it as an editable deploy surface.
2. **Execute a one-way cutover now, as part of deploy-QA.** Minimal slice:
   - Fold the SPCS `USE WAREHOUSE nuance_dev_wh` / `USE DATABASE nuance_db` startup into
     `comprenda_app.py` (currently missing from the repo home file; required for correct
     container context). Verify in the local harness before deploying.
   - `PUT` the repo tree into the Streamlit object's **own stage** (`comprenda_app.py`,
     `views/`, `lib/comprenda_*`, `.streamlit/config.toml`). Do **not** upload `_harness/`
     or `environment.yml` (default package set already covers the redesign — only `pandas`,
     transitive via snowpark, and Altair, bundled in Streamlit).
   - `REMOVE` the old-structure orphans — **critically the entire `pages/` directory**, which
     would otherwise trigger Streamlit's auto-multipage discovery and double-route against
     `st.navigation` — plus `nuance.py`, `lib/nuance_queries.py`, and the inert
     `pyproject.toml` / `snowflake.yml`.
   - `SET MAIN_FILE = 'comprenda_app.py'`, then `LIST` (operator-reviewed) → `COMMIT`.
   - **Preserve the existing app object and URL:** PUT-into-stage + `COMMIT`, never
     `CREATE OR REPLACE` (which mints a new URL and re-provisions the SPCS container).
3. **Defer git-backed deploy to the Marketplace-prep phase, as its own decision.** A
   git-sourced Streamlit (deploy = `git push` + `PULL`) is the better long-term end state —
   it *achieves* "no manual drift" rather than relying on convention — but it is an infra
   migration that would churn the app URL and contaminate this pass's `st.navigation`
   runtime-blocker verification. Out of scope here; revisit deliberately later.

## Alternatives considered

- **Reconcile/merge the workspace, per ADR-0002.** Rejected — no longer a merge of peers;
  the workspace holds only the superseded app. Merging stale code in is pointless.
- **Defer the cutover to the native-app session, per ADR-0002's timing.** Rejected —
  deploy-QA must run first and forces the cutover now; deferring leaves the redesign
  un-shippable and un-verifiable.
- **Re-create the app git-backed now.** Rejected for this pass — see Decision 3 (URL churn +
  mixing infra migration into UI verification). Held as the Marketplace-prep end state.
- **Keep deploying via the Snowsight workspace / Deploy button.** Rejected — that *is* the
  drift mechanism, and the Deploy button already breaks on a main-file rename.

## Consequences

**Positive**
- The repo becomes the single source of truth *in fact*, not just intent.
- The redesign becomes deployable and QA-able; the dead workspace stops producing
  "fixed-in-repo-but-not-live" confusion.
- Preserves the existing app URL and SPCS container.

**Negative / follow-up (binding)**
- **After the cutover:** update `docs/09_streamlit_ops_runbook.md` (it self-flags as
  describing the *pre-reconciliation* state) and close open-item #1 in
  `docs/10_project_status.md`.
- The **SiS Streamlit runtime ≥ 1.36** (`st.navigation`) is unverifiable until app load —
  the first thing to check on `COMMIT` + container reopen.
- The **`PUT`/S3 path** depends on the `*.s3.amazonaws.com` Norton exclusion (distinct from
  the now-verified `*.snowflakecomputing.com` login path); verify with a throwaway test
  `PUT` before the full cutover, or the upload step fails with error 253003.
- **Git-backed deploy** remains an open decision for Marketplace-prep.
- The demo-corpus / data-bundling follow-ups ADR-0002 also referenced are unaffected and
  remain tracked in `docs/10` and [ADR-0003](0003-multi-axis-divergence-profile.md).

## Notes

The deployed-state snapshot in Context is point-in-time and becomes false the moment the
cutover commits — do not treat it as durable. This ADR records the *decision*; execution and
its verification land in `IMPLEMENTATION_NOTES.md` §8 and the updated `docs/09`.
