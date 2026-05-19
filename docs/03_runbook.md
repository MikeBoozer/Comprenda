# Nuance — Minimal-Effort Runbook

This is exactly what *you* (Mike) do, in order, to ship Nuance. Anything not on this list is already done in the repo. Total active time: **~3 hours over 29 days**.

---

## Day 0 (30 min) — Snowflake setup

1. Go to `signup.snowflake.com`. Choose **AWS / us-west-2 / Enterprise**. Use your real email.
2. Verify email, set password, log into `app.snowflake.com`.
3. (Optional but recommended) Set up key-pair auth following Snowflake's quickstart at `docs.snowflake.com/en/user-guide/key-pair-auth`. Save the private key path.
4. Copy `data/snowflake_config.template.toml` to `~/.snowflake/config.toml` and fill in your account identifier and user. (You'll see your account identifier on the Snowflake UI, top-left dropdown.)

That's it for Day 0.

---

## Day 1 (5 min active, ~5 min query time) — Bootstrap

1. In Snowflake UI, open a new SQL worksheet.
2. Open `snowflake/00_bootstrap.sql` in your editor, copy the whole file.
3. Paste into the worksheet. Click **Run All**.
4. Wait ~90 seconds. Verify the two smoke tests near the end each print `AVAILABLE` (not `UNAVAILABLE`).

> **Note:** You may have already run Section 7 of this file separately to create `NUANCE_APP_ROLE`. That is fine — running the full file again is safe. Every statement uses `IF NOT EXISTS`, `MERGE`, or `CREATE OR REPLACE`, so nothing will be duplicated or broken.

If anything fails, the most likely cause is a Cortex feature not enabled. Snowflake → Admin → Account → Cortex — toggle everything on.

---

## Day 2 (10 min active, ~5 min run time) — Demo data

From your laptop terminal, in the project folder:

```bash
cd C:\Users\micha\Nuance
python -m venv .venv && .venv\Scripts\activate    # or `source .venv/bin/activate` on macOS/Linux
pip install -r data/requirements.txt
python data/generate_demo_data.py
python data/load_to_snowflake.py
```

The loader will tell you exactly how many rows ended up in `raw_data.social_posts`. Should be 25,000.

---

## Day 3 (3 min) — Sanity check

In a SQL worksheet, run:
```sql
USE NUANCE_DB.RAW_DATA;
SELECT detected_language, COUNT(*) FROM social_posts GROUP BY 1 ORDER BY 2 DESC;
SELECT event_tag, COUNT(*) FROM social_posts GROUP BY 1 ORDER BY 2 DESC;
```

You should see 12 languages and 8 event tags. If you do, you're golden.

---

## Days 4–9 (20 min active, ~15 min query time) — Enrichment

Open and Run All on each of these SQL files in order. Each is idempotent (safe to re-run).

| Day | File | Expected credits |
|---|---|---|
| 4–5 | `snowflake/05_embedding_pipeline.sql` | 3–6 |
| 6 | `snowpark/deploy.py` (run from terminal) | < 0.1 |
| 6–7 | `snowflake/06_frame_classification.sql` | 10–12 |
| 8 | `snowflake/07_cds_computation.sql` | < 0.5 |
| 9 | `snowflake/08_cortex_search.sql` | 1 + 0.1/day |

After Day 9, you have ~365 credits left and a fully-enriched dataset.

---

## Days 10–17 (60 min active) — App

1. **Day 10**: In Snowflake → Projects → Streamlit → **+ Streamlit App**. Name it `nuance_app`. Warehouse: `nuance_dev_wh`. Database: `nuance_db`. Schema: `outputs`.
2. After it creates, go to the file tree on the left of the Streamlit editor. Upload `streamlit/nuance_app.py` as the main file, and upload everything in `streamlit/pages/` and `streamlit/lib/` to matching folders inside Snowflake's Streamlit file tree.
3. Open `environment.yml` in the Streamlit editor and paste the contents of `streamlit/environment.yml` over it.
4. Click **Run**. The app launches in a new tab.

5. **Days 11–14**: Click through every page. Anything that looks wonky, open in Cursor and fix in 5-min chunks. The pages are functional out of the box; this is just polish.

6. **Day 15**: Upload `semantic_model/nuance_semantic_model.yaml` to a Snowflake stage:
```sql
CREATE STAGE IF NOT EXISTS nuance_db.internal.semantic_models;
PUT file://semantic_model/nuance_semantic_model.yaml @nuance_db.internal.semantic_models OVERWRITE = TRUE;
```
Then in Snowflake → AI & ML → Cortex Analyst → New Studio → point at the staged YAML. Run the 10 sample questions in the YAML header. Most will work. Iterate on the rest in Cursor by editing the YAML and re-uploading.

---

## Days 18–22 (90 min active) — Differentiators

1. **Day 18** (Pre-Launch Risk Score): Run from terminal:
```bash
python snowpark/deploy_plcs.py
```
This deploys the PLCS stored procedure. Then in the Streamlit app, go to Pre-Launch Risk page and run a test query: paste in `"Live free, drive fast"` as draft content, target markets `[ja, zh, de, es]`. Verify you get a sensible-looking risk report.

2. **Day 19** (Cultural Translator): `python snowpark/deploy_translator.py`. Test with the same draft.

3. **Day 20** (Drift Alerts): In Snowflake worksheet, Run All on `snowflake/09_alerts_and_tasks.sql`. Then run:
```sql
INSERT INTO nuance_db.library.tracked_entities (entity_name, owner_email)
VALUES ('iPhone 17', 'YOUR_EMAIL_HERE');
```
The Task will run hourly. To test immediately, manually `EXECUTE TASK nuance_db.internal.drift_check_task;`.

4. **Day 21** (Analog library): `python data/seed_analog_library.py`. This loads ~100 curated historical cases. Verify in Streamlit Analog Retrieval page.

5. **Day 22** (MCP server): See `mcp/README.md`. The fastest path is `fly launch` (free tier works for testing) and pasting the resulting URL into Claude Desktop's MCP config. Total time ~30 minutes.

---

## Days 23–29 (30 min active + waiting) — Launch

1. **Day 23**: Native App packaging is mostly already done in `native_app/`. Follow `native_app/README.md` — basically `snow app deploy` after installing Snowflake CLI.
2. **Day 24**: Submit Marketplace listing. Use copy from `go_to_market/marketplace_listing.md`. Submit and wait — approval is 3–7 business days.
3. **Day 25**: Set up Custom Event Billing in Marketplace Provider Studio. Copy the JSON config from `go_to_market/billing_config.json`.
4. **Day 26**: Open `go_to_market/icp_and_prospects.md`. Use Perplexity Pro with the prompts inside. Build a 50-row prospect spreadsheet.
5. **Day 27**: Record demo. Open `go_to_market/demo_script.md`. Use Loom. 5 minutes. Don't perfectionism — v1 is fine.
6. **Day 28**: Launch posts. Templates in `go_to_market/`. Send 50 cold emails using `go_to_market/cold_email_templates.md` — personalize 30 seconds each by adding one specific line about the company.
7. **Day 29**: Apply to Snowflake Startup Program at `snowflake.com/startup`. Run a final credit audit:
```sql
SELECT * FROM nuance_db.internal.credit_status;
```

---

## Daily credit check (30 seconds)

Once a day during Days 4–9 and 18–22, run:
```sql
SELECT * FROM nuance_db.internal.credit_status;
```

If you're trending over budget, the resource monitor will auto-suspend before damage is done. But this lets you see it coming.

---

## When something breaks (3 most likely cases)

1. **"Function CORTEX.AI_COMPLETE does not exist"** → Cortex AI not enabled for your account. Admin → Cortex → enable.
2. **"Model 'claude-4-sonnet' not found"** → Snowflake renamed the model. Run `SELECT * FROM SNOWFLAKE.CORTEX.LIST_MODELS()` and update `nuance_db.internal.config` table's `model_large` value.
3. **Streamlit app fails to import a package** → Add to `streamlit/environment.yml` and re-deploy in Snowflake UI.

For anything else, paste the error into Claude Code and ask. The repo is structured so individual files can be debugged in isolation.

---

## What you do NOT need to do

- Write SQL (done)
- Write Snowpark UDFs (done)
- Write the Streamlit app (done)
- Write the Cortex Analyst YAML (done)
- Write the Native App manifest (done)
- Write the MCP server (done)
- Write prompts (done, in `prompts/`)
- Design the pricing (done, in `docs/04_business_model.md`)
- Write landing page copy (done, in `go_to_market/`)
- Write cold emails (done, in `go_to_market/`)
- Write the demo script (done, in `go_to_market/`)
- Build prospect research from scratch (done, in `go_to_market/icp_and_prospects.md`)

Your job is execution; the build artifacts are all here.
