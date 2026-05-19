# Project Nuance — Build Session Transcript

A reconstructed log of the chat session in which Project Nuance was built end-to-end. The session ran in Claude's Cowork mode (Sonnet/Opus mix) on **May 17–18, 2026**. Mike (the user) gave a single directive and the rest is the back-and-forth that produced this repo.

> **Note:** Long generated artifacts (SQL scripts, Python files, Streamlit pages, HTML, etc.) are *not* re-pasted here — they live in their actual files in this repo. This transcript records the *conversational decisions*, *requirements*, *clarifications*, *commentary*, and *audit findings* that produced those files. If you want to know "why is X this way", search this transcript.

---

## Turn 1 — User opening directive

> You are an expert software engineer with extensive knowledge of state of the art data analytics methods and AI/ML methods. Note that it is May 17, 2026, and the recent and current state of business, economics, and technology development. Make Novel idea 2 a reality that would truly be highly likely to be the foundation for a viable and successful business. You will see in Project files that a preliminary build plan was drafted, with the working project name of CulturePulse. You may use that, but I want everything to be completed with minimal effort on my part, and I want the project to be name Nuance (or Project Nuance when clarity requires it). Think what features (especially creative, novel, innovative improvements) would further improve the product in any way or improve its potential to be a truly viable and successful business (remember to keep current and future state of technology, economics, and the saas market) and introduce/incorporate them into the product design. If possible, try to make use of my Snowflake free trial ($400 of credits/tokens). I also have Perplexity Pro, Claude Pro, Claude Code, and Cursor Pro. But prioritize quality of the product: if using one (or more) of these resources would detract from the quality of the product or unconstructively complicate things, then don't use them. Occasionally use a critical eye and ensure the quality and look for any areas of your approach, methods, or output to this prompt that may be incorrect or buggy, and then make sure to address them. Ask clarifications questions as needed, but remember that I want to do as little busy work as is practical, so long as it doesn't detract from the final product or its business success potential.

## Turn 2 — Claude reads the project files

Claude read:

- `CulturePulse Cross-Lingual Cultural Intelligence Engine — Business Plan & Step-by-Step Build Guide.md` — the preliminary build plan under the working name *CulturePulse*. Identified the core architectural insight (don't translate to English first; embed in native language space using `snowflake-arctic-embed-l-v2.0` and apply cultural-frame scoring), the existing competitive context (Brandwatch $800+/mo, Sprinklr $1,200+/mo, Meltwater ~$500-$1,000/mo, none with native-language analysis or self-serve trials), and the planned credit budget (~91–170 of the trial's 400 credits).
- `Snowflake AI Projects Playbook.md` — the broader playbook that defined Novel Idea 2 as the seed of CulturePulse.

## Turn 3 — Claude asks clarifying questions

Claude asked three questions via the AskUserQuestion tool:

1. **Wedge market** at launch — narrow to one buyer to maximize conversion.
2. **Execution scope** — full repo + execution kit, or repo + light Snowflake bootstrap, or plan + key code only.
3. **Snowflake account status** — spend credits this session, or stage everything for Mike's own timeline.

## Turn 4 — User answers

- Wedge: **Global brand / marketing teams** (recommended).
- Scope: **Build the full project repo + execution kit** (recommended).
- Snowflake: **Credits get spent later, not now** (recommended).

## Turn 5 — Claude plans the build

Claude created a 10-task plan via TaskCreate:

1. Write Nuance master plan & product design doc.
2. Build Snowflake SQL setup pack.
3. Build Snowpark Python UDFs/Procedures.
4. Build Streamlit-in-Snowflake app.
5. Build Cortex Analyst semantic model.
6. Build Native App + MCP server scaffolding.
7. Build data ingestion pack + demo dataset generator.
8. Build go-to-market kit.
9. Write minimal-effort runbook + README.
10. Verify quality, fix bugs, sanity check.

Tasks were executed in order, with TaskUpdate calls tracking in-progress → completed transitions.

## Turn 6+ — Claude executes the build

### Strategic / planning docs (Task 1)

Created in `docs/`:

- `00_executive_summary.md` — one-paragraph product description; table comparing CulturePulse v0 vs. Project Nuance v1; "what minimal effort actually means" list.
- `01_product_design.md` — primary buyer/ICP scorecard, anti-ICP, feature inventory (F1–F10 with rationale and UX surface), feature → buyer-value matrix.
- `02_master_plan.md` — 29-day phase-by-phase plan (Phase 0 pre-work through Phase 5 productization).
- `03_runbook.md` — exact step-by-step actions Mike does. Active time budgeted at ~3 hours over 29 days.
- `04_business_model.md` — pricing tiers (Pulse free / Studio $349 / Brand $1,290 / Enterprise custom), usage-based overages, GTM motion, 12-month revenue projection, defensibility table, funding path, exit positioning.
- `05_credit_budget.md` — line-item Snowflake credit budget totaling 95–180 credits of the 400-credit trial, with guardrails wired into the bootstrap script.
- `06_architecture.md` — high-level architecture, native-language embedding rationale, Native App framework, two-pass classification with model tiers, hybrid retrieval for PLCS, trust layer commitments.

### Key product design decisions

- Wedge buyer: VP/Director of Global Marketing or Head of Brand at mid-market consumer brands (200–5,000 headcount) selling in 5+ countries.
- Killer feature: **Pre-Launch Cultural Risk Score (PLCS)** — predictive, not retrospective.
- Workflow value-add: **Cultural Translator** — frame-preserving content adaptation, not just translation.
- Always-on layer: **Cultural Drift Alerts** via Snowflake Tasks + Cortex Alerts.
- Defensibility / moat: **Cultural Divergence Score (CDS)** as proprietary metric, **Analog Retrieval** over a curated library of ~40 historical cases (HSBC, Mercedes, Pepsi, Dolce&Gabbana, Bud Light, Balenciaga, etc.), **Cultural Frame Marketplace** as a roadmap network-effect play.
- Strategic 2026 positioning: **Nuance MCP Server** — exposes Nuance as the cultural-context substrate any enterprise AI agent can call. Brand-tier feature.
- Distribution: Snowflake **Native App** for the 14× EBITDA exit multiple and zero data-egress procurement story.
- Trust layer commitments codified in every output table: `confidence`, `model_used`, `prompt_version`, `inference_timestamp`, `inputs_json`.

### Snowflake SQL pack (Task 2)

Created in `snowflake/`:

- `00_bootstrap.sql` — single-file setup: resource monitor (300-credit cap), XS warehouse, database + 5 schemas, config table with model identifiers, raw/enriched/outputs/internal/library DDL, frame taxonomy seed (12 frames), pipeline_runs + inference_logs observability tables, credit_status view, smoke tests.
- `05_embedding_pipeline.sql` — generates 1024-dim multilingual embeddings via `snowflake-arctic-embed-l-v2.0`. Idempotent; batched.
- `06_frame_classification.sql` — two-pass classification: `mistral-7b` cheap first pass, `claude-4-sonnet` re-pass on flagged rows; plus sentiment (Cortex SENTIMENT) and emotional tone (Plutchik 7).
- `07_cds_computation.sql` — per-(event, language) centroids + pairwise CDS via Snowpark UDFs.
- `08_cortex_search.sql` — two Cortex Search services: enriched posts + analog library.
- `09_alerts_and_tasks.sql` — Cortex Alerts: hourly drift check + email notification.

### Snowpark Python (Task 3)

Created in `snowpark/`:

- `deploy.py` — registers `cosine_distance` UDF and `vector_avg` UDAF with full state-setter support.
- `deploy_plcs.py` — registers `SCORE_CONTENT` stored procedure with hybrid retrieval (Cortex Search primary, direct cosine fallback).
- `deploy_translator.py` — registers `TRANSLATE_CULTURE` stored procedure.
- `deploy_ai_brief.py` — registers `GENERATE_BRIEF` stored procedure.
- `deploy_analog_retrieval.py` — registers `FIND_ANALOGS` stored procedure.

### Streamlit app (Task 4)

Created in `streamlit/`:

- `nuance_app.py` — main / home dashboard (KPI cards + recent activity).
- `lib/nuance_queries.py` — shared query helpers used by every page.
- `lib/__init__.py` — package marker.
- `environment.yml` — Python environment manifest.
- `pages/1_Pre_Launch_Risk.py` — the killer-feature page (paste draft, multi-select markets, render risk scores + narratives + analog suggestions).
- `pages/2_Cultural_Translator.py` — frame-preserving adaptation page.
- `pages/3_Event_Explorer.py` — per-event summary stats + sentiment chart.
- `pages/4_Divergence_Matrix.py` — CDS heatmap.
- `pages/5_Frame_Distribution.py` — per-language cultural frame breakdowns.
- `pages/6_Drift_Alerts.py` — subscription management for tracked entities.
- `pages/7_Analog_Retrieval.py` — semantic search over the analog library.
- `pages/8_AI_Brief.py` — AI brief generation + Markdown download.
- `pages/9_Narrative_Search.py` — Cortex Search-backed search bar over the corpus.

### Cortex Analyst semantic model (Task 5)

`semantic_model/nuance_semantic_model.yaml` — five tables (enriched_content, cds_scores, plcs_scores, drift_events, tracked_entities), measures, dimensions, time dimensions, synonyms for natural-language flexibility, 10 sample questions, 3 verified queries, one relationship.

### Native App + MCP server (Task 6)

Native App in `native_app/`:

- `manifest.yml` — manifest with two configurable references (consumer_raw_data, consumer_notification), privileges, version metadata.
- `setup_script.sql` — versioned schema + app_data schema + all tables/procs + reference callbacks + Streamlit registration.
- `README.md` — packaging and Marketplace publishing instructions.

MCP server in `mcp/`:

- `nuance_mcp_server.py` — FastMCP server exposing 7 tools (`score_content`, `translate_culture`, `get_divergence`, `find_analogs`, `generate_brief`, `list_events`, `list_tracked_entities`) over either stdio (for Claude Desktop) or streamable HTTP (for hosted deployment).
- `requirements.txt`.
- `README.md` — local install + Fly.io / Cloud Run hosted deployment.

### Data ingestion pack (Task 7)

Created in `data/`:

- `generate_demo_data.py` — generates a 25K-row synthetic-but-realistic multilingual dataset across 12 languages and 8 events, with hand-crafted per-(event, language) frame tendencies that produce *interesting* divergence patterns for demos.
- `download_gdelt.py` — pulls real multilingual news data from GDELT GKG v2 (65+ languages, free).
- `download_huggingface.py` — pulls the cardiffnlp/tweet_sentiment_multilingual dataset.
- `load_to_snowflake.py` — Snowpark write_pandas loader.
- `seed_analog_library.py` — loads ~40 curated historical cultural-failure cases into the analog library with server-side embedding.
- `requirements.txt` — pinned Snowpark version.
- `snowflake_config.template.toml` — template for `~/.snowflake/config.toml`.

### Prompt library

Created in `prompts/`:

- `cultural_frame_classification.txt`
- `pre_launch_risk_scoring.txt`
- `cultural_translator.txt`
- `ai_brief_synthesis.txt`

Each prompt is versioned with a `VERSION:` header so output rows can reference the exact prompt used.

### Go-to-market kit (Task 8)

Created in `go_to_market/`:

- `landing_page.html` — full marketing page with dark-mode design, feature grid, incumbent comparison table, four-tier pricing.
- `cold_email_templates.md` — four templates (VP Global Marketing, boutique PR agency, hedge fund analyst, Snowflake-native ICP) plus follow-up template and pacing guidance.
- `demo_script.md` — 5-minute Loom demo script with shot list and exact narration.
- `linkedin_launch_post.md` — opening-week launch post hook + follow-up content calendar.
- `product_hunt_copy.md` — PH launch checklist, maker's first comment, gallery assets, voting strategy.
- `icp_and_prospects.md` — Perplexity Pro research workflow, 10-criterion ICP scorecard, industries to prioritize/deprioritize, weekly outreach pacing.
- `marketplace_listing.md` — Snowflake Marketplace listing copy.
- `billing_config.json` — Marketplace billing tier configuration (subscriptions + usage overages + free trial).

### Runbook + quickstart (Task 9)

- `README.md` (project root) — overview, file layout, quick start, business pitch in a paragraph.
- `QUICKSTART.md` (project root) — 30-second-to-read, 45-minutes-to-deploy checklist.
- `docs/03_runbook.md` — full day-by-day execution book.

### Audit + fix pass (Task 10)

Claude launched an independent subagent (general-purpose agent) to audit the entire repo for SQL correctness, Snowpark Python issues, Cortex API mismatches, cross-file consistency, and stored-procedure return semantics. The audit returned a prioritized list of findings:

**Critical (would block first run):**

1. `09_alerts_and_tasks.sql` used `SQLROWCOUNT` outside `EXECUTE IMMEDIATE` → wouldn't capture rowcount.
2. `09_alerts_and_tasks.sql` `notify_drift()` used `FOR row IN rec DO` on a `RESULTSET` (invalid; needs `CURSOR`).
3. `09_alerts_and_tasks.sql` Task body had a multi-statement `BEGIN…END` (Tasks must be one statement).
4. UDAF in `deploy.py` missing `aggregate_state` setter → distributed execution would fail to rehydrate state.
5. `deploy_plcs.py` fallback path bound a Python list as a `VECTOR(FLOAT, 1024)` parameter (not supported by Snowpark).
6. `07_cds_computation.sql` truncated `cultural_divergence_scores` on every run → drift alerts would always read prev_cds = 0 and spam.
7. `09_alerts_and_tasks.sql` join key mismatch: `tracked_entities.entity_name` ("iPhone 17") didn't join to `event_tag` ("iPhone_17_launch").

**High:**

8. `06_frame_classification.sql` `ALTER TABLE … ADD COLUMN` failed on script re-run.
9. String interpolation of user content into SQL queries in PLCS / Translator (injection + breakage on backslashes).
10. `08_cortex_search.sql` `EMBEDDING_MODEL = '…'` clause not universally accepted.
11. `deploy_ai_brief.py` `ArrayType` parameter doesn't bind cleanly across Snowpark versions.

**Medium / cosmetic:**

12. `00_bootstrap.sql` smoke test used `LENGTH()` on a string and `ARRAY_SIZE()` on a vector (vector isn't an array).
13. Native-app reference callbacks used `CASE WHEN … THEN SELECT …` (invalid Scripting syntax).
14. Unicode `…` and `✓` in `print()` statements break Windows console default codepage.

Claude applied **all 14 fixes** and documented them in `docs/07_audit_and_fixes.md`, along with known residual risks (Cortex model availability by region, SEARCH_PREVIEW return shape variance, CLASSIFY_TEXT vs. AI_CLASSIFY function name, etc.) and a 12-step end-to-end verification path.

## Turn N — Archive and file housekeeping

Claude moved the original CulturePulse build guide and the Snowflake AI Projects Playbook into `archive/` so they don't conflict with the current product spec but remain available for traceability. Added an `archive/README.md` clarifying their read-only nature.

## Turn N+1 — Final summary

Claude reported back to Mike:

- Wedge sharpened to global brand / marketing teams.
- Six novel features beyond the original CulturePulse plan: PLCS, Cultural Translator, Drift Alerts, Analog Retrieval, MCP server, Cultural Frame Marketplace (roadmap).
- Pricing tightened: Studio $349 / Brand $1,290 / Enterprise custom + usage-based overages.
- Trust layer enforced at the schema level.
- ~95–180 credit estimate of the 400-credit Snowflake trial; resource monitor caps total spend at 300 as a hard safety net.
- Active work for Mike: ~3 hours spread across 29 days.
- Recommended reading order: `QUICKSTART.md` → `docs/03_runbook.md` → `docs/07_audit_and_fixes.md`.

## Turn N+2 — Export request

Mike asked Claude to export the entire chat thread as a markdown file and place it where Claude Code would find it. Claude wrote this transcript at `docs/08_build_session_transcript.md` and added a small `CLAUDE.md` pointer at the project root so a future Claude Code session entering this directory surfaces it on the first turn.

---

## Decision log (quick-reference)

Pulled from the conversation, the binding decisions are:

| Topic | Decision | Rationale |
|---|---|---|
| Project name | Nuance (Project Nuance for clarity) | Mike's directive |
| Wedge buyer | Global brand / marketing teams at mid-market consumer companies | Highest self-serve conversion potential; pairs with PLCS killer feature |
| Killer feature | Pre-Launch Cultural Risk Score (PLCS) | Predictive vs. retrospective; aligns with 2026 AI-content QA pain |
| Defensibility | CDS metric + native-language architecture + Analog Library + MCP positioning | Multi-layered moat; incumbents would break customer APIs to copy |
| Distribution | Snowflake Native App + Marketplace | 14× EBITDA exit multiple; zero data-egress procurement story |
| Pricing | $0 / $349 / $1,290 / Custom + usage overages | Below all incumbents; usage overages drive expansion revenue |
| Demo data | Engineered synthetic dataset (25K rows, 12 langs, 8 events) | Deterministic, signal-rich, repeatable demos without credit spend |
| Initial language coverage | en, ja, zh, de, es, fr, ko, pt, ar, hi, it, ru | Covers ~85% of mid-market consumer global launches |
| Two-pass classification | mistral-7b first, claude-4-sonnet re-pass on ambiguous | ~70% credit savings vs. all-claude |
| Trust layer | confidence + model_used + prompt_version + inference_timestamp on every output | Enterprise auditability; prompt A/B testability |

---

## Open items for Mike (residual TODO)

These were called out in the runbook but worth restating here:

1. Sign up for a fresh Snowflake trial (AWS us-west-2, Enterprise) — Day 0.
2. Copy `data/snowflake_config.template.toml` → `~/.snowflake/config.toml` with your account locator.
3. Verify that the four Cortex models (`claude-4-sonnet`, `mistral-7b`, `mistral-large2`, `snowflake-arctic-embed-l-v2.0`) are live in your region with `SELECT * FROM TABLE(SNOWFLAKE.CORTEX.LIST_MODELS())`. If any are renamed, update `nuance_db.internal.config`.
4. After the first end-to-end pipeline run, iterate the prompts in `prompts/` to taste — the bones are right but the phrasing benefits from a half-day of polish on real data.
5. Replace the placeholder email in `09_alerts_and_tasks.sql` notification integration with your actual address (or move to an `ALLOWED_RECIPIENTS` allow-list).
6. For the Cultural Translator "Copy" button to actually copy to clipboard, swap in `streamlit-extras` or a `components.html` hack — currently decorative.
