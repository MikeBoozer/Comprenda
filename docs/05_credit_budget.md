# Project Nuance — Snowflake Credit Budget

Trial budget: **$400 credits** (29 days from activation). At Snowflake's April 2026 flat $2.00/credit AI pricing, this is roughly 200 Snowflake credits of compute *plus* the AI usage. All numbers below are credits (compute-equivalent).

## Headline

**Total estimated spend for full MVP build + 10 sample demos: 95–180 credits.** Leaves 220–305 credits as buffer.

## Cost breakdown

| Bucket | Detail | Est. credits |
|---|---|---|
| Warehouse compute (XS, auto-suspend 60s) | Development + queries across 29 days | 10–20 |
| Cortex `EMBED_TEXT_1024` (arctic-embed-l-v2.0) | 25K demo posts at ~$0.0001/post | 3–6 |
| Cortex `SENTIMENT` | 25K posts | 0.5–1 |
| Cortex `AI_CLASSIFY` (Plutchik emotions, mistral-7b) | 25K posts | 1.5–3 |
| Cortex `AI_COMPLETE` (mistral-7b, frame classification first pass) | 25K posts | 5–8 |
| Cortex `AI_COMPLETE` (claude-4-sonnet, ambiguous re-pass) | ~2,000 posts | 4–8 |
| Cortex `AI_TRANSLATE` (validation only, not the main pipeline) | 1K posts | 0.5–1 |
| Cortex Search index build + maintenance | Build + 29 days of low-volume queries | 3–6 |
| Cortex Analyst | Initial setup + ~200 test queries | 2–5 |
| Cortex Agent (AI Brief Generator) | ~10 briefs for demos | 5–15 |
| Pre-Launch Risk Scoring (claude-4-sonnet) | ~50 PLCS runs during dev + demos | 8–15 |
| Cultural Translator runs (claude-4-sonnet) | ~30 runs during dev + demos | 5–10 |
| Drift Alerts task | Hourly runs for ~14 days × 12 entities tracked | 4–8 |
| Streamlit-in-Snowflake serving | App rendering across 29 days | 8–15 |
| Snowflake Tasks + Streams | Pipeline orchestration | 2–4 |
| Buffer for iteration / re-runs | 30% safety margin | 25–55 |
| **Total** | | **95–180** |

## Guardrails (already wired in `00_bootstrap.sql`)

```sql
-- Resource monitor: 50 credits per day, 300 credits per trial period
CREATE OR REPLACE RESOURCE MONITOR nuance_trial_monitor
WITH CREDIT_QUOTA = 300
FREQUENCY = NEVER  -- one-time quota for trial
START_TIMESTAMP = IMMEDIATELY
TRIGGERS
    ON 50 PERCENT DO NOTIFY
    ON 80 PERCENT DO NOTIFY
    ON 95 PERCENT DO SUSPEND
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE nuance_dev_wh SET RESOURCE_MONITOR = nuance_trial_monitor;
```

This means: even if a bug runs a 100K-row pipeline against claude-4-sonnet by mistake, Snowflake will suspend the warehouse at 285 credits and refuse to spend more. Mike's worst-case loss is capped.

## Cost-saving choices baked into the build

1. **XS warehouse only.** L warehouses are 16× as expensive; we never use them during development.
2. **AUTO_SUSPEND = 60s.** A forgotten warehouse left running for a weekend would otherwise burn 100+ credits.
3. **mistral-7b for bulk, claude-4-sonnet for hard cases.** The two-pass classification approach is ~70% cheaper than running everything on claude-4-sonnet.
4. **Cortex Search vs. dense vector self-search.** Cortex Search service is far cheaper than scanning embeddings via Snowpark vector functions for the same retrieval task.
5. **`SENTIMENT` for bulk sentiment.** It's ~30× cheaper than asking an LLM to score sentiment.
6. **Batch processing.** Embedding and classification queries process in 5,000-row batches with explicit `LIMIT` so a typo doesn't run the entire table.
7. **Demo data scale: 25K posts.** Enough for a believable demo. Enough for analog retrieval to work. Not so much that we burn budget.

## When to scale up (and what it costs)

If Mike gets a paying customer who wants to analyze their full real dataset (say, 1M posts):
- Embedding: ~120 credits ($240 if customer pays Cortex direct; ~$0 if Native App and they pay)
- Frame classification (mistral-7b first pass): ~200 credits
- Frame classification (claude-4-sonnet re-pass on 10%): ~150 credits
- Total: ~500 credits / ~$1,000 of compute

This is fine even on Studio tier ($349/mo) economics — the per-customer compute cost is amortized over time and most customers don't run a full 1M backfill more than once.

## Where the buffer goes if not used

If Mike finishes the build at ~100 credits used (likely), 300 credits remain for:
- Expanding demo dataset to GDELT 65 languages
- Running PLCS on 50+ prospect-specific draft contents during sales demos
- Recomputing the full pipeline on real customer data during paid pilots
- Snowflake Tasks running drift alerts for weeks of "live" demonstration

In other words, the buffer is the customer-acquisition runway.
