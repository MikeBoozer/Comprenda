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
2. ✅ **DONE (2026-05-30).** Rebuilt the demo corpus dedup'd at source —
   `data/generate_demo_data.py` now emits **one row per distinct `post_text` per
   (event, language)** (deterministic enumeration of the frame-template inventory; the
   weighted-sampling/`build_tendencies` machinery is gone, and English-fallback rows for
   tendency frames a language had no template for are no longer emitted). Live corpus is
   now **1,440 rows / 1,440 distinct** (was 24,960 / 1,434). Re-embedded + re-classified +
   recomputed CDS on the live `NUANCE_DB` (≈1 credit vs the old ~15). All 528 language
   pairs survive; headline JSD range unchanged (0.013–0.483).
3. ✅ **DONE (2026-05-30).** `cds_confidence` was the only degenerate metric (Finding C):
   a new `internal.config` key `cds_confidence_saturation` (=25) replaces the hardcoded
   `/100.0` in `07_cds_computation.sql`. Confidence now spans **0.4 / 0.6 / 0.8** by sample
   size (was a flat 1.0); the AI Brief narrates it honestly (no more "1.0 across all pairs /
   English (562)"). The frame-JSD thresholds (0.23 / 0.34) were **verified unchanged** —
   the CDS SQL already deduped internally, so the rebuild didn't move the JSD distribution.
4. ✅ **DONE (2026-05-30).** Updated the multi-axis CDS references:
   `semantic_model/nuance_semantic_model.yaml` (description → frame-JSD headline + 0.23/0.34,
   added `situation_label` dimension and frame/sentiment/topical measures) and
   `native_app/setup_script.sql` (added the multi-axis columns to the bundled
   `cultural_divergence_scores` DDL; config seed + `tracked_entities` drift defaults moved
   from the old 0.35/0.55 centroid scale to the multi-axis scale).

*Decision gates (pre-Marketplace metric / data polish):*
4a. ❓ **DECIDE (ask Mike): expand demo-corpus lexical variety?** The dedup rebuild (#2) left the
   corpus honest but **template-thin** — ~5 phrasings per (language, frame), so one template
   rendered across 8 events yields near-identical Narrative Search results (e.g. "What an
   opportunity! the new iPhone / the rebrand / the final just dropped"). Not a bug (rows are
   distinct); it's the small authored template pool. The **hero features (Divergence Matrix, AI
   Brief) don't depend on lexical variety** and are already credible, so this is optional —
   weigh it against whether Narrative Search is spotlighted in demos.
   - **If yes:** generate richer native-language posts per (event, language, frame) — Cortex-
     generate is the scalable, on-brand path — then reload → re-run embed→classify→CDS →
     re-derive `cds_confidence_saturation` + verify thresholds → refresh `docs/12` expected
     values. ~1 credit, same loop as the 2026-05-30 rebuild.
   - **Hard ordering constraint:** if done at all, it must land **before #6 bundles the corpus**
     into the Marketplace package — otherwise the thin corpus ships and has to be re-bundled.
     Pull it forward only if recording demo footage that spotlights Narrative Search.
   - **Demo linkage:** when done, refresh `streamlit/_harness/fixtures.py` (the public-demo data
     served by `streamlit/demo_app.py`) from the rebuilt corpus — export the real CDS matrix /
     frame distributions / sample posts / a real AI Brief + PLCS — so the demo becomes faithful
     *and* compelling in one pass. (Decision 2026-05-30: keep the curated fixtures until then.)
4b. ✅ **DECIDED (2026-05-31, Mike) — build deferred.** Replace the sample-size **sufficiency**
   proxy `cds_confidence = LEAST(min(distinct_posts)/25, 1.0)` (`07_cds_computation.sql`) — a
   transparent sample-size measure, *not* statistical confidence (arbitrary saturation, linear
   not 1/√n scaling, not tied to the JSD's sampling variance) — with a statistically grounded
   uncertainty measure on the per-pair frame-JSD. **Relabeled honestly 2026-05-30** (matrix
   aside + AI Brief now read "sample sufficiency"; brief prompt → `ai-brief-v3`) as the stopgap
   that ships until this lands.
   - **Chosen measure — the combo:** a **Dirichlet-posterior credible interval** as the
     displayed uncertainty (each language's frame counts already define a Dirichlet posterior
     via the existing `frame_smoothing_alpha` prior → sample `P_A`, `P_B` from their posteriors,
     recompute JSD, read a credible interval), **plus a permutation test** (shuffle language
     labels → null JSD distribution at that n) surfaced as a "✓ above chance" flag. They're
     complementary: the interval gives magnitude + precision and degrades gracefully at small n
     (vs. a plain bootstrap resampling ~10 discrete points); the permutation p attacks the
     small-n upward bias of plug-in JSD and answers "is this fault line real?" Compute-only (no
     Cortex). Plain bootstrap-CI was considered and ranked third (weakest exactly at the
     thin-language pairs; a variance-only CI doesn't touch the bias).
   - **Timing:** **not** needed for the portfolio capture or the current trial window —
     deferred. Do it before the matrix/brief go in front of methodology-savvy buyers; not gated
     on corpus bundling.

*Native-app packaging (from [ADR-0001](decisions/0001-native-app-distribution-with-demo-data.md)):*
5. **Re-target schemas** — procedures + Streamlit from `NUANCE_DB.*` to `app_data.*`,
   parameterized so one codebase serves both the dev instance and the app.
   Write `setup_script` idempotent + migration-safe (consumer data persists across upgrades);
   open this work with a 10-min upgrade-readiness pass over `manifest.yml` + `setup_script.sql`.
6. **Apply the security / data-privacy guardrails** (ADR-0001, "binding for the build"):
   bundle only synthetic data + enrichment + analog corpus; **exclude** `tracked_entities`
   (real owner email), `pre_launch_risk_scores`, `cultural_translator_runs`, `ai_briefs`,
   `drift_events`; tight `snowflake.yml` artifacts allow-list (never glob the project root —
   it would bundle `.mcp.json` / `~/.snowflake/config.toml`); least-privilege manifest;
   audit the staged package before publishing.

## Deferred / nice-to-have

- **Rename / clarify the analog "gap" metric (UI polish).** The analog cards (PLCS results +
  Analog Retrieval) surface the retrieval `distance` as a bare "gap N" with no explanation, and
  "gap" collides with the Divergence Matrix's **topical gap** (= 1 − overlap) — same word, two
  meanings. In a UI pass, either add a one-line caption/tooltip ("semantic distance; lower =
  closer") or rename the analog field to "distance"/"match" and reserve "gap" for the matrix axis.
- **Reconcile PLCS "confidence" with what it actually is (honesty).** The Pre-Launch Risk cards
  (the "% conf" bar) + the "Confidence calculation" expander show a per-market **confidence** that
  the UI explains as *corpus density* ("how densely the target market is represented in the
  corpus"). In reality `SCORE_CONTENT` (`deploy_plcs.py`) sets `plcs_confidence` to **the LLM's
  self-reported `confidence`** parsed from its JSON (default 0.5 on parse failure), or a hard-coded
  **0.1 when no target-market neighbours are found**, clamped to [0,1]. There is **no corpus-density
  computation** — so the UI's "how densely the target market is represented" explanation does not
  match the code. (Aside: the deployed proc builds an *inline* prompt, not the versioned
  `prompts/pre_launch_risk_scoring.txt`; the file's edge-case rules — e.g. "cap confidence at 0.5 if
  <10 neighbours" — are absent from the deployed string, a separate prompt-drift worth a look.) The
  matrix's honesty fix (`cds_confidence` → "sample sufficiency") never reached PLCS. **Not a "sample
  sufficiency" rename** — a different quantity than the matrix's min-post-count proxy. Options:
  (a) replace it with a real computed corpus-support / nearest-neighbour-density measure so the
  existing explanation becomes true (the PLCS analog of #4b); (b) re-explain it honestly as a model
  self-estimate; or (c) drop it.

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
