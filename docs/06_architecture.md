# Project Nuance — Technical Architecture

## High-level diagram (described)

```
                ┌──────────────────────────────────────────────┐
                │            CUSTOMER'S SNOWFLAKE              │
                │                                              │
   Data sources │   raw_data.social_posts                      │
   ─────────────▶  └─▶ enriched.post_embeddings  (arctic-      │
   (GDELT,         │      embed-l-v2.0 multilingual)            │
    Marketplace,   │  └─▶ enriched.cultural_frames (12 frames,  │
    customer       │      mistral-7b + claude-4-sonnet         │
    first-party)   │      hybrid pipeline)                     │
                │                                              │
                │   outputs.cultural_divergence_scores         │
                │   outputs.pre_launch_risk_scores             │
                │   outputs.cultural_translator_runs           │
                │   outputs.ai_briefs                          │
                │   library.analog_corpus  (seeded by Nuance)  │
                │   library.tracked_entities (customer)        │
                │                                              │
                │   Cortex Search service (over enriched)      │
                │   Cortex Analyst (semantic_model YAML)       │
                │   Cortex Alerts (Drift Alerts)               │
                │                                              │
                │   ┌───────────────────────────────┐          │
                │   │   Streamlit-in-Snowflake App  │          │
                │   │   (9 pages, see below)        │          │
                │   └───────────────────────────────┘          │
                └──────────────────────────────────────────────┘
                         ▲                       ▲
                         │                       │
              ┌──────────┴────┐         ┌────────┴────────┐
              │   Web user    │         │   External MCP  │
              │   (marketer)  │         │   (Claude       │
              │               │         │    Desktop,     │
              │               │         │    Cursor,      │
              │               │         │    enterprise   │
              │               │         │    agents)      │
              └───────────────┘         └─────────────────┘
```

## Why this architecture

### Native-language embedding-first (vs. translate-first)

Every social-listening incumbent runs `translate(post, src→en) → sentiment(en_text)`. This destroys cultural framing: sarcasm, irony, in-group references, historical grievance invocations are all lost in translation. Nuance uses Snowflake's `EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', post)` which produces a 1024-dim vector *in the native language* and is shared semantic space across languages by design (it's a multilingual model trained on parallel data). The Cultural Divergence Score works because we can compare centroids across languages in the same vector space without translating either.

When we need natural-language outputs *about* a non-English post (e.g., explaining the frame to an English-speaking user), `claude-4-sonnet` reads the native text directly — Claude is strong multilingual and doesn't need a translation hop. The translation only happens at the final "show the user" step, never in the analytical pipeline.

### Snowflake Native App (vs. external SaaS)

The Native App Framework lets us ship Nuance as code that installs into the customer's Snowflake account. The customer brings their own data (in their warehouse) and pays their own compute. We charge subscription + usage via Marketplace billing.

Consequences:
- **Customer data never leaves their boundary.** This is the strongest privacy story available in B2B SaaS and removes ~80% of procurement friction.
- **Our COGS at scale approach zero on compute.** Gross margin → 90%+ at Enterprise tier.
- **Distribution moat.** Once installed and integrated, the switching cost is high — we are part of their data fabric, not an external integration.
- **Valuation premium.** 14× EBITDA at exit vs. 6–8× for connected SaaS (multiple sources, 2026 benchmarks).

### Two-pass classification with model tiers

Cultural frame classification is the most credit-intensive step. We use a cost-optimal two-pass strategy:
1. **Pass 1**: `mistral-7b` (cheap, 3–10× cheaper per token than claude) classifies all posts. Outputs include a self-reported confidence (we prompt for it).
2. **Confidence triage**: Posts where mistral output doesn't match the 12 known taxonomy values OR where confidence < 0.7 are flagged.
3. **Pass 2**: `claude-4-sonnet` re-classifies only the flagged posts (typically 5–15% of corpus).

Net effect: ~70% credit savings vs. all-claude, with no measurable quality degradation on the high-confidence majority.

### Hybrid retrieval for PLCS

Pre-Launch Cultural Risk Score uses a hybrid retrieval pattern:
1. Embed the draft content using arctic-embed-l-v2.0.
2. Cortex Search over `enriched.post_embeddings` filtered by target language, returning top-50 historical neighbors.
3. Re-rank neighbors by `cultural_frame` overlap and recency.
4. Aggregate the historical CDS and sentiment outcomes of top-15 neighbors.
5. `AI_COMPLETE(claude-4-sonnet)` synthesizes the risk narrative grounded in the retrieved evidence — explicit RAG.

This pattern combines lexical (Cortex Search has full-text + vector hybrid) and semantic retrieval with structured business-logic re-ranking. It is more accurate than pure vector search for this task because cultural-frame overlap is a stronger signal than embedding distance alone for predicting cultural risk.

### Trust layer (confidence, citations, audit)

Every output table has:
- `confidence FLOAT` — model-reported or computed from agreement/sample size
- `model_used STRING` — exact model identifier (so we can pin versions)
- `prompt_version STRING` — checksum of the prompt template used
- `inference_timestamp TIMESTAMP_NTZ` — when the score was produced
- `inputs_json VARIANT` — full inputs to the inference, for replay

This is non-negotiable for an enterprise product where wrong outputs damage the customer's brand. It also makes A/B testing prompts trivial and gives us a defensible "show your work" answer to regulators / auditors when (not if) cultural intelligence becomes a regulated category.

## Streamlit app pages

1. **Home / Dashboard** — KPIs across tracked events, recent drift alerts, recent PLCS scores.
2. **Event Explorer** — world map (Pydeck) colored by sentiment for a selected event_tag; per-language summary cards.
3. **Divergence Matrix** — CDS heatmap (Plotly) for selected event across language pairs.
4. **Frame Distribution** — side-by-side bar charts per language showing cultural frame breakdown.
5. **Pre-Launch Risk** — input box for draft content, target market multiselect, runs PLCS, renders risk report.
6. **Cultural Translator** — input box for source content, target market multiselect, renders 2–3 adapted variants.
7. **Drift Alerts** — table of tracked entities, threshold tuning, alert history.
8. **Analog Retrieval** — search box → semantically similar historical campaign-launch divergence events.
9. **AI Brief Generator** — event_tag selector + language picker → 2-page Markdown brief, exportable to PDF/Notion.
10. **Narrative Search** (Cortex Search) — search bar across full corpus, filter by language/frame/event.

Cortex Analyst NL query is a top-of-screen omnibox on every page (powered by the YAML semantic model).

## MCP server design

Standalone Python service (FastMCP framework) hosted on Fly.io or Cloud Run free tier. Authenticates against the customer's Snowflake account via OAuth 2.1 — every tool call runs SQL against *their* Native App tables, so all data access is governed by their Snowflake grants.

Tools exposed:
- `nuance.score_content(content, target_markets)` → PLCS for each market.
- `nuance.translate_culture(content, target_market)` → 2–3 adapted variants.
- `nuance.get_divergence(event_tag, lang_pair)` → CDS lookup.
- `nuance.find_analogs(content_or_event)` → 5 nearest historical analogs.
- `nuance.generate_brief(event_tag, languages)` → AI Brief in Markdown.

Each tool call returns a structured JSON envelope with `data`, `confidence`, `sources`, `latency_ms`, `cost_credits`. Enterprise agents can render this as natural language or pipe it to downstream tools.

## Fallback paths

| Component | Failure mode | Fallback |
|---|---|---|
| `claude-4-sonnet` unavailable | Cortex outage or rename | Auto-fallback to `mistral-large2` via the `model_large` config var. Quality drops 5–10% but service stays up. |
| Arctic Embed v2 quality on rare language | Tested-poor for, e.g., Swahili | Voyage AI (`voyage-multilingual-2`) drop-in via the `EMBED_TEXT_1024` function. Documented in `snowflake/05_embedding_pipeline.sql` as commented alternative. |
| Cortex Analyst SQL generation fails on a question | YAML ambiguity | App falls back to "let me run a default query for you" with a button to see the SQL Cortex Analyst tried. Logged for YAML improvement. |
| Cortex Search latency spike | Indexing pressure | Direct vector cosine search via Snowpark UDF on `post_embeddings` table — slower but always available. |

## Versioning

- **Prompts** live in `prompts/` and are versioned by file checksum. The version is stored alongside every inference result.
- **Code** is versioned by semver in `manifest.yml` for the Native App. Customer can pin or upgrade.
- **Semantic model** is versioned in `semantic_model/nuance_semantic_model.yaml`; old versions are kept in staged copies.

## Observability

- `internal.pipeline_runs` — every batch pipeline run with start/end/rows/credits consumed.
- `internal.inference_logs` — every LLM call with inputs/outputs/cost.
- `internal.credit_status` — view over Snowflake's `ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY` filtered to our warehouse.

These power the resource monitor and the `nuance.audit_run` MCP tool that customer agents can call to verify a given output.

## Scaling roadmap (post-MVP)

- **H2 2026**: Image/video content understanding (cultural framing of visual content) using Cortex's multimodal AI_COMPLETE.
- **H1 2027**: Real-time ingestion via Snowpipe Streaming for customer-owned data sources.
- **2027**: Cultural Frame Marketplace — third-party authors contribute taxonomies via a sub-app inside Nuance.
- **2027+**: Voice / podcast cultural analysis via `AI_TRANSCRIBE` + cultural frame pipeline.
