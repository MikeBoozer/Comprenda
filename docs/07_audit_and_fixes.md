# Project Nuance — Pre-flight Audit & Fixes Log

An independent code audit was run against the full Nuance repo before any of it touched a real Snowflake account. This document records what was found, what was fixed, and what residual risks remain. Read this if you hit anything unexpected during your first run.

---

## Files audited

- All `snowflake/*.sql` (00–09)
- All `snowpark/*.py` (deploy, PLCS, Translator, AI Brief, Analog Retrieval)
- The Streamlit app (`nuance_app.py`, `lib/`, `pages/*`)
- `semantic_model/nuance_semantic_model.yaml`
- `native_app/setup_script.sql`
- `data/*.py` (demo generator, loader, seed library)

---

## Critical fixes applied

| # | Issue | Where | Fix |
|---|---|---|---|
| 1 | Drift-alert Scripting block used invalid `SQLROWCOUNT` semantics outside `EXECUTE IMMEDIATE` | `snowflake/09_alerts_and_tasks.sql` | Wrapped the INSERT in `EXECUTE IMMEDIATE` so `SQLROWCOUNT` works |
| 2 | `notify_drift()` iterated a `RESULTSET` with `FOR row IN rec DO` (not valid) | `snowflake/09_alerts_and_tasks.sql` | Rewritten using `DECLARE c CURSOR FOR SELECT ...` |
| 3 | Snowflake Task body used a multi-statement `BEGIN…END` (Task body must be a single statement) | `snowflake/09_alerts_and_tasks.sql` | Created wrapper `internal.run_drift_cycle()` and call that from the Task |
| 4 | `tracked_entities.entity_name` ("iPhone 17") never joined to `event_tag` ("iPhone_17_launch") → drift detection silently produced zero rows | `snowflake/09_alerts_and_tasks.sql` | Added `event_tag_pattern` column with ILIKE/`_`/space-normalized matching |
| 5 | UDAF state setter missing → distributed centroid computation would fail to rehydrate state across executors | `snowpark/deploy.py` | Added `aggregate_state` setter; added vector-length guard in `accumulate()` |
| 6 | PLCS fallback bound a Python list to a `VECTOR(FLOAT, 1024)` parameter via `params=[embedding_vec, …]` (not supported by Snowpark) | `snowpark/deploy_plcs.py` | Removed embed-then-bind path; query now inlines `EMBED_TEXT_1024(?, ?)` so the VECTOR is constructed server-side |
| 7 | `07_cds_computation.sql` truncated `cultural_divergence_scores` on every run → drift-alert prior-CDS lookup always returned 0 → false-positive alert spam | `snowflake/07_cds_computation.sql` | Changed truncate to append; each run adds a new historical row keyed by `computed_at` |
| 8 | `06_frame_classification.sql` `ALTER TABLE … ADD COLUMN` would fail on script re-run | `snowflake/06_frame_classification.sql` | Used `ADD COLUMN IF NOT EXISTS`; final INSERT now skips post_ids already present |
| 9 | String-interpolation of user content into SQL strings in PLCS / Translator created a backslash-injection vector and breakage on any draft containing an unescaped char | `snowpark/deploy_plcs.py`, `snowpark/deploy_translator.py` | Switched to parameterized `params=[…]` everywhere |
| 10 | Native-app reference callbacks used `CASE WHEN … THEN SELECT …` syntax that Snowflake Scripting rejects | `native_app/setup_script.sql` | Rewritten as `IF/ELSEIF/END IF` with `SELECT … INTO :rv` |
| 11 | AI Brief sproc registered with `ArrayType(StringType())` input, which doesn't bind cleanly across Snowpark versions | `snowpark/deploy_ai_brief.py` | Switched to `VariantType()`; handler normalizes a JSON string or list to a Python list |
| 12 | `00_bootstrap.sql` smoke test used `LENGTH(...)` and `ARRAY_SIZE(VECTOR)` (vector isn't an array) | `snowflake/00_bootstrap.sql` | Switched to `IS NOT NULL` checks and added a commented-out `LIST_MODELS` reference |
| 13 | `Cortex Search` `EMBEDDING_MODEL = '…'` clause is not universally supported; with the explicit clause the service may refuse to create | `snowflake/08_cortex_search.sql` | Clause commented out — service auto-picks the multilingual default. Uncomment if your region accepts the override |
| 14 | Unicode `…` and `✓` markers in `print()` statements break Windows console default codepage | All `data/*.py` and `snowpark/*.py` runtime scripts | Replaced with ASCII `[OK]` and `...` |

---

## Medium-priority fixes applied

- Added comment in `00_bootstrap.sql` near the model-name config rows telling you to verify with `SELECT * FROM TABLE(SNOWFLAKE.CORTEX.LIST_MODELS())` if anything fails.
- Pinned `snowflake-snowpark-python>=1.20.0` in `data/requirements.txt` (VectorType + UDAF support requires ≥1.11; we go higher to stay current).

---

## Open bugs (found post-deploy)

- **Translator target market resets to Arabic after the PLCS handoff (FIXED in repo 2026-05-31 — pending deploy).**
  From Pre-Launch Risk, **Open Translator with this draft →** lands on the Cultural Translator with
  the target market set correctly (e.g. Japanese), but then clicking **Generate adapted variants**
  returns variants for **Arabic**. *Root cause:* in `streamlit/views/2_Cultural_Translator.py` the
  target-market `st.selectbox` (L150) is **unkeyed** and its `index` is read from
  `prefill_markets = st.session_state.pop("translator_target_markets", [])` (L98), which is popped
  on first render. The Generate click reruns the script with `prefill_markets` now empty → `index`
  falls back to `0` → the unkeyed widget resets to `languages[0]` = `"ar"` (Arabic is alphabetically
  first; `list_languages` is `ORDER BY detected_language`), so the value read on that rerun is "ar".
  The draft text survives only because its `st.text_area` **is** keyed (`key="translator_source"`,
  L138) — the contrast confirms the cause. *Scope:* specific to the PLCS→Translator prefill; a
  manually chosen market persists fine (index is a stable `0` with no prefill, so the unkeyed widget
  keeps the pick). *Fix:* give the target-market selectbox a stable `key`
  (e.g. `key="translator_target_market"`) and seed `st.session_state[...]` from the prefill once
  (`setdefault` / callback-safe) instead of relying on `index=` + a popped one-shot value — the same
  keyed pattern the source draft already uses; then redeploy (docs/09). *Demo impact:* SHOT 3 of
  `go_to_market/demo_script.md` walks this exact handoff — once deployed this is clean.
  *Status (2026-05-31):* fix applied — the target-market selectbox is now keyed
  (`key="translator_target_market"`) and seeded once from the prefill via `setdefault`; verified
  headless via AppTest (target stays "ja" through the Generate rerun). **Code change is in the repo;
  pending the live deploy (docs/09).**

---

## Known residual risks (handle if you hit them)

These are not bugs in the code — they are environmental sensitivities you may encounter on first run.

1. **Cortex model availability by region.** `claude-4-sonnet`, `mistral-7b`, `mistral-large2`, and `snowflake-arctic-embed-l-v2.0` are available on AWS US East 1 / US West 2 / EU West and most major Azure regions, but availability changes. If a step fails with `model 'X' not found`, run:
   ```sql
   SELECT * FROM TABLE(SNOWFLAKE.CORTEX.LIST_MODELS());
   UPDATE nuance_db.internal.config SET config_value = '<live_model_name>' WHERE config_key = 'model_large';
   ```
2. **Cortex Search `SEARCH_PREVIEW` return shape.** In some versions the function returns a `VARCHAR` (JSON string), in others an `OBJECT`. The PLCS and Analog Retrieval handlers both `isinstance` check the result before parsing — they will tolerate either.
3. **`AI_CLASSIFY` vs `CLASSIFY_TEXT`.** `06_frame_classification.sql` uses `SNOWFLAKE.CORTEX.CLASSIFY_TEXT`. Both function names exist; `CLASSIFY_TEXT` is the older, stable one. If your account is on a newer release where only `AI_CLASSIFY` works, swap the function name (it's a single occurrence).
4. **`SNOWFLAKE.CORTEX.LIST_MODELS` function name.** In some regions the helper is exposed as `LIST_AVAILABLE_MODELS()` instead. Try both if needed.
5. **Cortex Analyst `MANY_TO_MANY` relationship.** The semantic model uses one M2M relationship between `enriched_content` and `cds_scores` via `event_tag`. If Cortex Analyst's YAML validator rejects this, switch the relationship to `MANY_TO_ONE` and model an intermediate `events` dimension table.
6. **Streamlit-in-Snowflake import of `lib/`.** The deploy creates `streamlit/lib/__init__.py` (already in repo). If Streamlit can't import `nuance_queries`, double-check that the `lib/` folder structure is preserved in the Snowflake-side file tree.
7. **Email integration for Drift Alerts.** `09_alerts_and_tasks.sql` creates a notification integration without an `ALLOWED_RECIPIENTS` allow-list. If your account requires it, add `ALLOWED_RECIPIENTS = ('you@example.com', ...)` to the integration definition before resuming the task.
8. **`load_to_snowflake.py --mode overwrite` fails on `POST_TIMESTAMP`.** With `overwrite`, `write_pandas` serialized the datetime column as `NUMBER`, which the existing `TIMESTAMP_NTZ` column rejects (`Expression type does not match column data type`). Observed during the 2026-05-30 data rebuild. **Workaround:** `TRUNCATE TABLE … SOCIAL_POSTS` first, then load with `--mode append` (the append path serializes timestamps correctly). The append path is also what `docs/03_runbook.md`/`QUICKSTART.md` use.

---

## Data-quality findings (live demo data, measured 2026-05-26)

These were found by querying the *live* data after the pipeline ran — they are not in
the original static audit. They concern **demo-data fitness**, and the fix belongs to the
ADR-0002 reconciliation / native-app data-bundling work, not a piecemeal patch.
**Numbers are point-in-time; re-run the queries below after any data rebuild.**

### Finding A — the demo corpus is heavily and *unevenly* duplicated

> ✅ **RESOLVED 2026-05-30.** `data/generate_demo_data.py` now dedups at source (one row
> per distinct `post_text` per event/language). Live corpus rebuilt to **1,440 rows /
> 1,440 distinct** — duplication eliminated. The numbers below are the pre-rebuild state.

`raw_data.social_posts` / `enriched.cultural_frames` hold **24,960 rows but only ~1,434
distinct `post_text`** (≈17× average duplication; same text, distinct `post_id`). The
duplication is **not uniform**: by language **10.4× (ru) → 28.1× (en)**; by frame
**10.8× (historical_grievance) → 22.4× (opportunity_framing)**. Root cause: the generator
in `data/generate_demo_data.py` draws from an unbalanced template pool.

Impact by feature:
- **Narrative Search** — returns visually-identical rows (the user-facing symptom). Being
  addressed with result-level dedup; the underlying data is the real fix.
- **Frame Distribution** — *mildly* skewed: `opportunity_framing` 18.4% raw vs 13.9%
  deduped (**+33% relative overstatement**); `historical_grievance` 5.6% vs 8.8%
  (**−36% understatement**); `ambiguous` 30.9%→33.7%; all others move <1.5pp. Frame
  *ranking* is preserved, so the qualitative story holds; exact percentages do not.
- **Per-language mean sentiment** — robust except **English** (raw 0.331 vs deduped 0.239,
  Δ 0.092 ≈ 28%); all other languages Δ ≤ 0.015. Matters only for features that surface
  mean sentiment directly (CDS does not — see Finding B).

### Finding B — CDS is robust to duplication, but the demo shows NO meaningful divergence

CDS (`snowflake/07_cds_computation.sql`) is **embedding-centroid cosine distance**, not
sentiment. Recomputing all **528** language pairs on *deduplicated* embeddings vs the
stored scores: average |Δ| **0.008**, max |Δ| **0.065**, and **0 → 0** pairs cross the
0.35 "meaningful" threshold either way. So **the Divergence Matrix is robust to the
duplication.**

The larger problem: **every CDS value is < 0.20 (max 0.196)**, well under the product's own
0.35 "meaningful" / 0.55 "risk" thresholds. The headline feature — cultural *divergence* —
currently shows none on the demo data. This is a **demo-fitness / possibly methodology**
issue (candidates: multilingual posts embedding close together; English-centric embedding
model; centroid-cosine insensitivity; mis-calibrated thresholds) and is **more important
than the duplication** for product credibility. Root cause not yet diagnosed.

### Finding C — multi-axis CDS resolved Finding B; now `cds_confidence` is degenerate (measured 2026-05-29)

Since [ADR-0003](decisions/0003-multi-axis-divergence-profile.md) replaced the embedding-centroid
CDS with the multi-axis frame-JSD profile (now live), **Finding B's "no meaningful divergence" is
resolved**: `headline_score` (= frame JSD) spans **0.01–0.48** with ~58–62 distinct values across
the 66 pairs per event — real dynamic range.

**The residual degenerate metric is `cds_confidence` — exactly 1.0 on every pair, every event.**
Its formula in `snowflake/07_cds_computation.sql` is `LEAST(LEAST(posts_a, posts_b)/100.0, 1.0)`
over **raw** post counts. With Finding A's ~17–28× duplication every language's count far exceeds
100, so it always clamps to 1.0. The true *distinct* counts (~15–20 per event/language) would give
~0.15–0.20 — informative and varied. The JSD headline is unaffected because it uses **normalized**
frame distributions (uniform duplication cancels), so score and confidence meet opposite fates on
the same corpus.

> ✅ **RESOLVED 2026-05-30.** Corpus dedup'd at source; `07_cds_computation.sql` now reads
> a `cds_confidence_saturation` config key (=25) instead of the hardcoded `/100.0`. Live
> `cds_confidence` now spans **0.4 / 0.6 / 0.8** by sample size (was a flat 1.0), and the AI
> Brief narrates it honestly. The frame-JSD thresholds were verified unchanged.

**Fix (data-rebuild scope):** dedup the corpus (one row per distinct `post_text` per
event/language), recompute `cds_confidence` on distinct-text counts, and re-derive the `/100`
saturation threshold (100 is too high for a ~15–20-post regime). The Divergence Matrix's uniform
"confidence 100%" is **deliberately left faithful** in the UI (not special-cased) — it becomes
meaningful once the data is fixed. (Verified 2026-05-29 during deploy-QA: the live AI Brief
`GENERATE_BRIEF` narrates this `1.0` confidence and the duplicated sample sizes — "confidence
high (1.0 across all pairs)… English (562), Japanese (312)…" — as a credibility *strength*, so the
rebuild also stops the brief from making false confidence claims, not just the matrix column.)

### Re-measurement queries

```sql
-- Duplication overall + by language / frame
SELECT COUNT(*) total, COUNT(DISTINCT post_text) distinct_texts FROM NUANCE_DB.RAW_DATA.SOCIAL_POSTS;
SELECT detected_language, COUNT(*) total, COUNT(DISTINCT post_text) distinct_texts FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES GROUP BY 1 ORDER BY 2 DESC;
SELECT cultural_frame, COUNT(*) total, COUNT(DISTINCT post_text) distinct_texts FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES GROUP BY 1 ORDER BY 2 DESC;

-- CDS spread (are any pairs "meaningful"?) — should have rows >= 0.35 once data is fit
SELECT ROUND(MAX(cds_score),3) max_cds,
       SUM(CASE WHEN cds_score>=0.35 THEN 1 ELSE 0 END) meaningful_pairs,
       COUNT(*) total_pairs
FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES;
```

(The full deduped-CDS recompute uses `outputs.vector_avg` + `outputs.cosine_distance` over
`enriched.post_embeddings` grouped by distinct `post_text` — see session history if needed.)

---

## Verification path before going live

Before sharing a demo with a real prospect, run this end-to-end test in order:

1. Run `snowflake/00_bootstrap.sql`. Verify both smoke-test queries return `AVAILABLE`.
2. Run `python data/generate_demo_data.py` and `python data/load_to_snowflake.py`. Verify 25,000 rows landed in `raw_data.social_posts`.
3. Run `python snowpark/deploy.py`, then `python snowpark/deploy_plcs.py`, `deploy_translator.py`, `deploy_ai_brief.py`, `deploy_analog_retrieval.py`. Each should print `[OK]`.
4. Run `python data/seed_analog_library.py`. Verify ~40 analog cases land in `library.analog_corpus`.
5. Run `snowflake/05_embedding_pipeline.sql` → verify `enriched.post_embeddings` populated.
6. Run `snowflake/06_frame_classification.sql` → verify `enriched.cultural_frames` populated.
7. Run `snowflake/07_cds_computation.sql` → verify `outputs.cultural_divergence_scores` populated.
8. Run `snowflake/08_cortex_search.sql` → verify the test `SEARCH_PREVIEW` returns results.
9. Run `snowflake/09_alerts_and_tasks.sql`.
10. Test one PLCS: `CALL NUANCE_DB.OUTPUTS.SCORE_CONTENT('Live free, drive fast', 'en', 'ja', NULL);`
11. Test one Translator: `CALL NUANCE_DB.OUTPUTS.TRANSLATE_CULTURE('Live free, drive fast', 'en', 'ja', NULL, NULL);`
12. Test one Brief: `CALL NUANCE_DB.OUTPUTS.GENERATE_BRIEF('iPhone_17_launch', PARSE_JSON('["en","ja","zh","de"]'), NULL);`

If all 12 succeed, the pipeline is fully validated.

---

## What the audit did not catch (your eye still matters)

- Visual polish of the Streamlit pages (chart colors, layout density).
- The exact phrasing of LLM outputs from PLCS / Translator / Brief — these depend on the live model and your demo data. Plan a half-day to iterate on the prompts in `prompts/` after your first end-to-end run.
- Streamlit's clipboard "Copy" button in `2_Cultural_Translator.py` is decorative — it doesn't actually copy. Add `streamlit-extras` or a custom `components.html` clipboard hack if you want real copy behavior.
