# Project Nuance — Master Plan (29-Day Build & Launch)

This is the single source of truth for what gets built when. It is designed for one operator (Mike) with the resources listed below.

## Resources

- **Snowflake free trial** — $400 credits, 29 days. The credit budget in `docs/05_credit_budget.md` keeps total spend under $400.
- **Perplexity Pro** — used for prospect research (Day 25–27) and live-source citations in the AI Brief.
- **Claude Pro / Claude Code** — used for SQL, Snowpark, prompt iteration. (Already in use producing this repo.)
- **Cursor Pro** — used for Streamlit polish; everything is pre-scaffolded here, so Cursor's job is mostly autocomplete on edits.

## Phases at a glance

| Phase | Days | Goal | Output |
|---|---|---|---|
| 0. Pre-work | 0 | Snowflake trial active, repo cloned | Working environment |
| 1. Foundation | 1–3 | DB, schemas, demo data loaded | Queryable Nuance dataset in Snowflake |
| 2. Enrichment | 4–9 | All AI enrichment running | Populated `enriched.*` and `outputs.*` tables |
| 3. App | 10–17 | Streamlit app fully functional | Internal-quality v1 |
| 4. Differentiators | 18–22 | PLCS, Translator, Alerts, MCP, Analogs | Externally-demoable Nuance |
| 5. Native App + GTM | 23–29 | Marketplace listing, demo video, outreach | Public launch |

---

## Phase 0 — Pre-work (Day 0)

Goal: get Mike to the point of running SQL inside Snowflake with auth ready.

Tasks (Mike does):
1. Activate Snowflake trial at `signup.snowflake.com`. Choose **AWS us-west-2** (most Cortex features available there) and **Enterprise edition**.
2. In Account → Cortex AI, enable: `AI_COMPLETE`, `AI_CLASSIFY`, `AI_SENTIMENT`, `AI_TRANSLATE`, `EMBED_TEXT_1024`, `AI_EXTRACT`, Cortex Search, Cortex Analyst, Cortex Agents.
3. Install SnowSQL or use Snowflake's Python connector with key-pair auth. The `data/load_to_snowflake.py` script expects either an `~/.snowflake/config.toml` or env vars (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`). Template included in `data/snowflake_config.template.toml`.

That's it for Day 0. Total time: 30 minutes.

---

## Phase 1 — Foundation (Days 1–3)

### Day 1 — Bootstrap

Run `snowflake/00_bootstrap.sql` in a Snowflake worksheet (Run All). This single file:
- Creates warehouse `nuance_dev_wh` (XS, auto-suspend 60s)
- Creates database `nuance_db` and schemas `raw_data`, `enriched`, `outputs`, `internal`, `library`
- Creates all base tables from `02_raw_tables.sql`, `03_enriched_tables.sql`, `04_output_tables.sql`
- Sets per-warehouse credit guardrails (resource monitors capping at 50 credits/day for `nuance_dev_wh`)
- Verifies Cortex availability with a smoke test on `AI_COMPLETE` and `EMBED_TEXT_1024`

Expected runtime: 90 seconds. Expected credit cost: < 0.05.

### Day 2 — Demo data load

Run from laptop:
```
pip install -r data/requirements.txt
python data/generate_demo_data.py --out data/nuance_demo.csv
python data/load_to_snowflake.py --file data/nuance_demo.csv --table raw_data.social_posts
```

`generate_demo_data.py` creates a synthetic-but-realistic dataset of 25,000 multilingual social posts across 12 languages and 8 event tags (recent product launches, sporting events, geopolitical moments). This dataset is good enough for a compelling demo and lets the rest of the build run *without* spending credits on real data ingestion.

Mike can swap in real data later via `data/download_gdelt.py` (free, 65 languages) or by subscribing to a Snowflake Marketplace social-data provider — but the demo data is sufficient for v1.

### Day 3 — Smoke tests

Run the test queries embedded at the bottom of `02_raw_tables.sql`:
- Count posts per language
- Count posts per event_tag
- Sample 5 posts from each major language to eyeball quality
- Run `SNOWFLAKE.CORTEX.SENTIMENT` and `AI_TRANSLATE` on a 10-row sample as cost calibration

Credit budget so far: ~0.1 credits. (Yes, that low. The XS warehouse + auto-suspend is doing the work.)

---

## Phase 2 — Enrichment (Days 4–9)

### Days 4–5 — Embeddings

Run `snowflake/05_embedding_pipeline.sql`. This file:
- Creates `enriched.post_embeddings` with `arctic-embed-l-v2.0` 1024-dim vectors
- Processes in 5,000-row batches with explicit progress logging to `internal.pipeline_runs`
- Stops at 80% of the credit guardrail to leave headroom

Credit cost: ~3–6 for 25K posts.

### Days 6–7 — Frame classification + sentiment + emotional tone

Run `snowflake/06_frame_classification.sql`. This file:
- Runs `mistral-7b` first-pass classification on all 25K posts (~6 credits)
- Flags posts where the model's output doesn't match any of the 12 taxonomy values
- Re-runs flagged posts on `claude-4-sonnet` (typically < 2,000 posts → ~3 credits)
- Adds `sentiment_score` via `SENTIMENT` (~0.5 credits)
- Adds `emotional_tone` via `AI_CLASSIFY` against Plutchik's 7 basic emotions (~1 credit)
- Writes everything to `enriched.cultural_frames` with confidence + model_used columns

Credit cost: ~10–12 for 25K posts.

### Day 8 — Cultural Divergence Score

Run `snowflake/07_cds_computation.sql`. This file:
- Calls the Snowpark UDFs from `snowpark/centroid_udaf.py` and `snowpark/cosine_distance_udf.py` (these need to be deployed once via `snowpark/deploy.py` — Day 4 task, takes 2 minutes)
- Computes per-(event_tag, language) centroids
- Computes pairwise CDS between language pairs per event
- Writes to `outputs.cultural_divergence_scores`

Credit cost: negligible (compute only, no LLM calls).

### Day 9 — Cortex Search service

Run `snowflake/08_cortex_search.sql`. Creates the search index over the enriched corpus that powers PLCS, Analog Retrieval, and the Narrative Search feature.

Credit cost: ~1 to build + ~0.1/day to maintain.

**End of Phase 2**: Total credits used ~25–35. We have ~365 credits left. All enriched tables populated. Ready to build app.

---

## Phase 3 — App (Days 10–17)

### Days 10–11 — Streamlit scaffold

In Snowflake → Projects → Streamlit, create app `nuance_app` using warehouse `nuance_dev_wh`. Upload `streamlit/nuance_app.py` and the `streamlit/pages/` directory. The app immediately works against the populated tables — no further wiring needed.

### Days 12–14 — Per-page polish

For each page in `streamlit/pages/`:
- Event Explorer (world map + summary stats)
- Divergence Matrix (CDS heatmap)
- Frame Distribution (side-by-side bar charts)
- Narrative Search (Cortex Search-backed search bar)
- AI Brief Generator (button → 2-page brief)

These are scaffolded fully — Cursor's job here is to wire in your customer's actual logo/colors and tighten any chart that looks off. Plan a half-day of polish per page.

### Days 15–17 — Cortex Analyst integration

Upload `semantic_model/nuance_semantic_model.yaml` to a Snowflake stage. Test 10 sample NL questions (provided in the file's header comment). Iterate on any that fail by:
1. Reading the SQL Cortex Analyst generated
2. Spotting which dimension/metric definition was ambiguous
3. Tightening the YAML

**End of Phase 3**: Working app, NL-queryable, looks like a v1 SaaS product.

---

## Phase 4 — Differentiators (Days 18–22)

### Day 18 — Pre-Launch Cultural Risk Score

Deploy `snowpark/pre_launch_risk_scorer.py` as a Snowflake Python stored procedure (instructions in the file header). Wire it into the Pre-Launch Risk page in Streamlit. Test on 20 sample drafts and tune the prompt in `prompts/pre_launch_risk_scoring.txt` until results feel right.

### Day 19 — Cultural Translator

Deploy `snowpark/cultural_translator.py`. Wire it into the Cultural Translator page. Test on the same 20 sample drafts — verify outputs are noticeably different (frame-shifted), not just translations.

### Day 20 — Drift Alerts

Run `snowflake/09_alerts_and_tasks.sql`. This creates:
- A `library.tracked_entities` table
- A Snowflake Task that recomputes CDS hourly for tracked entities
- A Cortex Alert that fires on threshold breach
- A `Sendmail` integration (or webhook) for delivery

Subscribe a tracked entity (e.g., "iPhone 17") and watch the alert fire after manually inserting a synthetic divergence spike.

### Day 21 — Analog Retrieval

Run `data/seed_analog_library.py`. This loads ~100 curated historical cases into `library.analog_corpus` with embeddings. Wire into the Analog Retrieval page in Streamlit. Verify quality by querying for known historical events and confirming the right analogs come back.

### Day 22 — MCP Server

The MCP server in `mcp/nuance_mcp_server.py` runs as a separate process (we'll host it on a tiny Cloud Run or Fly.io instance — instructions in `mcp/README.md`). Configure Claude Desktop's MCP settings to point at it. Verify the 5 tools work.

**End of Phase 4**: All killer features live. Externally demoable.

---

## Phase 5 — Native App + GTM (Days 23–29)

### Day 23 — Package as Native App

Convert the Streamlit-in-Snowflake app to a Native App via `native_app/manifest.yml` and `native_app/setup_script.sql`. Test internal installation in a second Snowflake account (use the trial's secondary user). Verify the install works end-to-end.

### Day 24 — Marketplace listing

Submit the listing to Snowflake Marketplace. Use the copy in `go_to_market/marketplace_listing.md`. Approval typically takes 3–7 business days.

### Day 25 — Pricing + billing

Configure billing in Snowflake Marketplace:
- Subscription tiers: Studio $349/mo, Brand $1,290/mo
- Custom Event Billing for PLCS overage ($1/score), AI Briefs ($10/brief), Translator runs ($2/run)

### Day 26 — Outreach list

Use Perplexity Pro to research 50 named prospects across the wedge ICP. The prompt template is in `go_to_market/icp_and_prospects.md`. Spreadsheet template in `go_to_market/prospects_template.csv`.

### Day 27 — Demo video

Record a 5-minute Loom following the `go_to_market/demo_script.md`. Story arc:
1. The pain (Pepsi/HSBC/Mercedes one-liner)
2. PLCS in action — paste a real-looking draft, get the risk score live
3. CDS heatmap on a real launch
4. AI Brief produced live
5. Cultural Translator producing two adapted variants
6. CTA: start a trial

### Day 28 — Public launch

Post:
- LinkedIn (copy in `go_to_market/linkedin_launch_post.md`)
- Product Hunt (copy in `go_to_market/product_hunt_copy.md`)
- r/marketing, r/startups, r/snowflake
- Hacker News (Show HN format)

Send cold outreach to the 50 prospects (templates in `go_to_market/cold_email_templates.md`). Aim for 5 demo bookings in the first week.

### Day 29 — Snowflake Startup Program

Apply to:
- Snowflake Startup Program (apply at `snowflake.com/startup`)
- Snowflake Startup Challenge (winners get credit grants + investor intros)
- a16z, Y Combinator (with Marketplace metrics as proof of traction)

Audit credits. If under-budget (likely), use remaining credits to expand the seed dataset to GDELT 65 languages or run more PLCS demos for prospects.

---

## Definition of done (Day 29)

- ✅ Live Streamlit app in Snowflake with all 9 pages functional
- ✅ Cortex Analyst NL queries working
- ✅ MCP server running and connectable from Claude Desktop
- ✅ Native App submitted to Marketplace
- ✅ 5-minute demo video published
- ✅ 50 cold emails sent
- ✅ Public launch posts live
- ✅ First demo booked

## Reality check — what could derail this

Three things and only three things:

1. **Snowflake Cortex API changes between this writing (May 2026) and your trial activation.** Mitigation: the `snowflake/*.sql` files are written defensively with try/except patterns and the model strings (`claude-4-sonnet`, `mistral-7b`, `snowflake-arctic-embed-l-v2.0`) are centralized in `snowflake/00_bootstrap.sql` as variables. If a model name has changed, fix it in one place.

2. **Arctic Embed multilingual quality on a target language insufficient.** Mitigation documented in `docs/06_architecture.md` — fallback to Voyage AI embeddings (also available in Cortex) for that language.

3. **Demo data feels too synthetic to a real prospect.** Mitigation: switch demo to a slice of GDELT for one well-known global event before recording the Loom (Day 27).

If any of these happens, expect to lose 1–2 days. The credit budget has buffer for re-runs.
