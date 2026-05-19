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
