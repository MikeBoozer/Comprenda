# 10 — Project status & open items (living doc)

A running snapshot of *where things stand now* and the concrete open work. Kept here —
not in `CLAUDE.md` — so the always-loaded entry file stays lean. **This doc is expected to
drift if neglected; when it conflicts with the linked ADRs/code, trust those.** Update it
as state changes.

## Current state (2026-05-26)

- **Streamlit app:** live and working. Deployed via the CLI sequence in
  [`09_streamlit_ops_runbook.md`](09_streamlit_ops_runbook.md) — *not* the Snowsight Deploy
  button (which broke on a main-file rename). Entry file is `nuance.py`.
- **Cultural Divergence Score:** now a **multi-axis profile** — topical overlap +
  frame-divergence (JSD) + sentiment divergence — per
  [ADR-0003](decisions/0003-multi-axis-divergence-profile.md), replacing the old
  text-embedding centroid distance (which measured topic, not stance, and showed zero
  divergence). Thresholds + smoothing live in `nuance_db.internal.config`. The Divergence
  Matrix page inlines its query on purpose (SiS caches `lib/` imports — see the runbook).

## Binding open items (before the native-app / Marketplace build)

*Data & metric (this round of work):*
1. ✅ **DONE (2026-05-29).** Cut the deployed app over to the git repo as the single source of
   truth — [ADR-0004](decisions/0004-repo-canonical-deploy-cutover.md), which **supersedes**
   [ADR-0002](decisions/0002-reconcile-workspace-repo-divergence.md). Executed as a one-way
   **cutover + workspace decommission**: SPCS `USE WAREHOUSE`/`USE DATABASE` fix folded into
   `comprenda_app.py`, repo tree PUT into the Streamlit object stage, old `pages/`-structure
   orphans removed, `MAIN_FILE = comprenda_app.py`, committed as `VERSION$2`, and the Snowsight
   workspace emptied so its Deploy button can't revert it. **Confirmed live + rendering on real
   SiS** (`st.navigation` runtime ≥1.36 verified). Git-backed deploy deferred to Marketplace-prep.
2. **Rebuild the demo corpus** — it is ~17× unevenly duplicated; verify the divergence
   signal. See [`07_audit_and_fixes.md`](07_audit_and_fixes.md) "Data-quality findings"
   (includes re-measurement queries).
3. **Re-derive divergence thresholds** from the rebuilt data and update `internal.config`.
4. **Update CDS references** in `semantic_model/nuance_semantic_model.yaml` and
   `native_app/setup_script.sql` to the multi-axis model.

*Native-app packaging (from [ADR-0001](decisions/0001-native-app-distribution-with-demo-data.md)):*
5. **Re-target schemas** — procedures + Streamlit from `NUANCE_DB.*` to `app_data.*`,
   parameterized so one codebase serves both the dev instance and the app.
6. **Apply the security / data-privacy guardrails** (ADR-0001, "binding for the build"):
   bundle only synthetic data + enrichment + analog corpus; **exclude** `tracked_entities`
   (real owner email), `pre_launch_risk_scores`, `cultural_translator_runs`, `ai_briefs`,
   `drift_events`; tight `snowflake.yml` artifacts allow-list (never glob the project root —
   it would bundle `.mcp.json` / `~/.snowflake/config.toml`); least-privilege manifest;
   audit the staged package before publishing.

## Deferred / nice-to-have

- **Consumer-BYO-data (Option B)** — the customer binds their own content table; the
  long-term product, a known post-launch milestone (ADR-0001).
- **Operator setup & polish TODOs** — [`08_build_session_transcript.md`](08_build_session_transcript.md)
  "Open items for Mike" (Cortex model verification, prompt polish on real data, the email
  placeholder in `09_alerts_and_tasks.sql`, the decorative Translator "Copy" button). Some
  may already be done — verify against current state.
- **UI/UX design-system pass** before the Marketplace launch — direction now locked in
  [`11_ui_ux_design_brief.md`](11_ui_ux_design_brief.md) (editorial aesthetic, CMO/Brand-VP
  persona, priority screens, SiS guardrails). Next: Claude Design delivers mockups + a handoff
  spec → build a local mock-data preview harness → implement into `streamlit/lib/ui.py` with a
  critique loop on the Claude Code side. Target file: `streamlit/lib/ui.py`.
- Distributional sentiment divergence (vs the current scaled mean-difference).
- A one-command deploy script — sensible only **after** the ADR-0002 reconciliation makes
  the repo a clean deploy source (flagged in [`09_streamlit_ops_runbook.md`](09_streamlit_ops_runbook.md)).
