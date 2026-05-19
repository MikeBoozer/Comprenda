# Nuance — Quickstart (30 seconds to read, 45 minutes to deploy)

If you remember nothing else from this repo, remember this single page.

## Day 0 — sign up (10 min)

1. Go to **signup.snowflake.com**. Pick **AWS / us-west-2 / Enterprise**.
2. Copy `data/snowflake_config.template.toml` → `~/.snowflake/config.toml`. Fill in your account id, user, and password.

## Day 1 — one click setup (5 min)

3. In Snowflake UI, open a SQL worksheet. Paste **`snowflake/00_bootstrap.sql`**. Click **Run All**.

## Before Day 2 — verify Cortex is enabled ⚠️

Before loading data, confirm Cortex AI is available on your account. Run these in a Snowflake worksheet:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE nuance_dev_wh;
SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-7b', 'Say OK.') AS test;
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', 'test') AS test;
```

Both must return a result (not an error) before proceeding. If you get "not available for trial accounts", contact Snowflake support and ask them to enable Cortex on your account. Cortex is required for the entire pipeline.

## Day 2 — load demo data (10 min)

4. From your laptop terminal, in this folder:
   ```bash
   pip install -r data/requirements.txt
   python data/generate_demo_data.py
   python data/load_to_snowflake.py
   ```

## Days 3-9 — run the enrichment pipeline (30 min, mostly waiting)

5. Run from terminal:
   ```bash
   python snowpark/deploy.py
   python snowpark/deploy_plcs.py
   python snowpark/deploy_translator.py
   python snowpark/deploy_ai_brief.py
   python snowpark/deploy_analog_retrieval.py
   python data/seed_analog_library.py
   ```

6. In Snowflake UI, **Run All** on these in order:
   - `snowflake/05_embedding_pipeline.sql`
   - `snowflake/06_frame_classification.sql`
   - `snowflake/07_cds_computation.sql`
   - `snowflake/08_cortex_search.sql`
   - `snowflake/09_alerts_and_tasks.sql`

## Day 10 — deploy the app (10 min)

7. In Snowflake → Projects → Streamlit → **+ Streamlit App**. Name: `nuance_app`. Warehouse: `nuance_dev_wh`. Database: `nuance_db`. Schema: `outputs`.
8. Upload `streamlit/nuance_app.py` and the `streamlit/pages/` and `streamlit/lib/` folders. Paste `streamlit/environment.yml`.
9. Click **Run**.

## You're live

Now read **`docs/03_runbook.md`** for the productization + go-to-market phase (Days 11-29).

For the full strategy, read in order:
- `docs/00_executive_summary.md`
- `docs/01_product_design.md`
- `docs/02_master_plan.md`
- `docs/04_business_model.md`
- `docs/06_architecture.md`

Total active time across all 29 days: ~3 hours. Total Snowflake credits: ~95-180 of your 400.
