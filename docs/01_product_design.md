# Project Nuance — Product Design

This document specifies what the product *is*, who it's for, and how each feature creates measurable value for the buyer. The codebase is organized 1:1 against the features listed here.

---

## 1. Primary buyer & ICP

**Buyer**: VP/Director of Global Marketing, or Head of Brand at a mid-market consumer brand that sells in 5+ countries. Headcount range 200–5,000. Annual marketing budget $2M–$50M.

**Secondary buyer**: Boutique international PR/comms agency principals serving multinational clients.

**Why they buy**: They are now responsible for AI-generated content quality across markets they don't speak the language of. Their existing tools (Brandwatch, Sprout Social, Meltwater) translate first and produce English-shaped reports that miss the cultural signal. They have no proactive QA before launch and no early-warning system after. One viral cultural misstep is a career event.

**Budget origin**: Marketing intelligence line ($30K–$200K/yr at mid-market) or AI/data tooling line.

**Decision cycle**: Self-serve for Studio tier; one demo call + one trial for Brand tier; standard procurement (4–10 weeks) for Enterprise.

---

## 2. Anti-ICP (do not pursue at launch)

- Fortune-500 brands already locked into Sprinklr (3-year contracts; battle for replacement is not winnable solo).
- Pure social-media-management buyers — they want Hootsuite-like scheduling, not intelligence.
- US-only brands — Nuance's value is multilingual; if they only sell in English markets, they're not a fit.

---

## 3. Feature inventory

### F1. Cultural Divergence Score (CDS) — the foundational metric

**What it is.** For a given event_tag (e.g., "iPhone 17 launch", "Olympics opening ceremony", "Brand X rebrand"), compute the per-language centroid in `arctic-embed-l-v2.0` embedding space. CDS = cosine distance between centroids for any pair of language communities. Range [0, 1]. CDS > 0.35 → meaningful semantic divergence. CDS > 0.55 → cultural risk signal.

**Why it's defensible.** Proprietary, citable, publishable as research. Requires the architectural conviction to *not* translate first — a switch incumbents can't easily make without breaking customer commitments. Embedding-space comparisons are the right way to measure "do these communities mean the same thing" and no competitor surfaces this today.

**UX surface.** Heatmap on the Divergence Matrix page, table on the Event Explorer page, JSON output via API/MCP.

---

### F2. Cultural Frame Taxonomy + Classification

**What it is.** A 12-category taxonomy: `individualist`, `collectivist`, `nationalist`, `globalist`, `threat_framing`, `opportunity_framing`, `historical_grievance`, `status_quo`, `reform_seeking`, `spiritual_ethical`, `pragmatic`, `ambiguous`. Each post is classified using `AI_CLASSIFY` (cheap first pass with mistral-7b) and the bottom-confidence 10% are re-classified with `AI_COMPLETE` on claude-4-sonnet.

**Why it matters.** Sentiment alone is a single number per post. Frames are a structured *why* — they explain divergence. Marketers want to know not just "Japan reacted negatively" but "Japan reacted negatively because the messaging tripped a historical-grievance frame."

**UX surface.** Side-by-side bar charts on Frame Distribution page; frame filter on every other page.

**Roadmap upsell.** Cultural Frame Marketplace — domain experts (regional consultancies) author and sell custom taxonomies (e.g., "Gulf consumer culture frames v2", "Japanese seasonality frames"). 70/30 rev share. Network effect.

---

### F3. Pre-Launch Cultural Risk Score (PLCS) — the killer feature

**What it is.** A user pastes 1–3 pieces of draft content (tagline, hero copy, product name, ad creative caption) plus target markets. Nuance returns:

- A 0–100 risk score per market, with a confidence interval.
- The top 3 cultural frames the content activates *in each target language*.
- 3–5 semantically nearest historical posts that produced the largest negative CDS swings — these are the "near-miss" examples.
- An LLM-synthesized risk narrative (~150 words) citing the matched frames and analogs.
- Optional: a "Cultural Translator" recommendation if PLCS > 60 in any market (auto-routes to F4).

**Mechanism.** Embed the draft content in `arctic-embed-l-v2.0` → kNN search via Cortex Search over historical embeddings filtered by target language → aggregate the historical CDS, frame distribution, and sentiment outcomes of nearest neighbors → claude-4-sonnet synthesizes the risk narrative using a structured prompt (in `prompts/pre_launch_risk_scoring.txt`).

**Why it closes deals.** Every other tool is retrospective. PLCS is *predictive*. The buyer has direct line-of-sight to ROI: a single avoided launch disaster pays for years of Brand tier.

**UX surface.** Pre-Launch Risk page. Input box, target market checkboxes, "Score" button, results in 5–8 seconds.

**API/MCP surface.** `POST /plcs` and `mcp__nuance__score_content`. This is the feature enterprise agents will most often call.

---

### F4. Cultural Translator — frame-preserving content adaptation

**What it is.** Given a source piece of content + target market, generate 2–3 culturally adapted variants that preserve intent but *shift the cultural frame* appropriately. Powered by `AI_COMPLETE(claude-4-sonnet)` with a structured prompt that specifies the source frames, the target market's dominant frames (computed from the analyzed corpus), and a directive to adapt accordingly.

**Why it's different from translation.** Google Translate gives you literal meaning. Cultural Translator gives you culturally-resonant content. The output is drop-in usable in the marketer's workflow.

**Cost control.** Cultural Translator runs cost ~0.05 credits each — billed as $2/run in usage-based pricing. Studio gets 20/mo, Brand unlimited within reason.

**UX surface.** Cultural Translator page; also auto-suggested from the PLCS results page when PLCS > 60.

---

### F5. Cultural Drift Alerts — the always-on layer

**What it is.** Customer subscribes a brand name, product, or event tag to drift monitoring. A Snowflake Task runs hourly (or on a 6-hr cadence on Studio) to recompute CDS for the tracked entity across configured language pairs. When CDS rises above a customer-set threshold (default: +0.15 absolute in 24 hours, or > 0.50 absolute), a Cortex Alert fires.

**Channels.** Email by default; Slack webhook for Brand tier; PagerDuty webhook for Enterprise.

**Why it converts trial → paid.** It's the feature that makes Nuance a daily-active product. Once you're getting actionable alerts, churning is painful.

**UX surface.** Drift Alerts page (subscribe/unsubscribe, threshold tuning, history).

---

### F6. Analog Retrieval — pattern matching as moat

**What it is.** A curated library of historical campaign-launch divergence patterns (we'll seed with ~100 well-documented cases, then auto-augment from customer data with consent). Given a current event's CDS+frame profile, semantic search returns the 5 most similar historical events with their outcomes.

**Why it matters.** Marketers don't always trust raw data. They trust analogies. "This looks like X" is a uniquely powerful narrative device, and no competitor has indexed cultural divergence at this granularity.

**Initial seed corpus** (lives in `data/seed_analog_library.json`, generated by `data/generate_demo_data.py`):
- 30 documented marketing translation/cultural failures (Pepsi "come alive" → "bring ancestors back from dead", HSBC "Assume Nothing", Mercedes/Bensi name, etc.)
- 40 product-launch reactions across APAC/EU/LATAM/MENA
- 30 geopolitical-event reaction patterns (good source: GDELT GKG events with cross-lingual coverage)

**UX surface.** Analog Retrieval page; also embedded in PLCS and Event Explorer outputs.

---

### F7. AI Cultural Brief Generator

**What it is.** One-button "give me the PDF I can put in a deck." A Cortex Agent synthesizes the data into a 2-page brief covering executive summary, key divergences with CDS scores, dominant frames per region, risk flags, and messaging recommendations. Sources are cited (post IDs, dates, languages) so the brief is auditable.

**Why it matters.** This is the deliverable that justifies the subscription internally. A marketing director shares it with their CMO; the CMO sees the value.

**Output formats.** Markdown rendered in-app; PDF export; Notion-friendly export.

**UX surface.** AI Brief page; available as a button on Event Explorer.

---

### F8. Cortex Analyst (Natural Language Query)

**What it is.** Cortex Analyst's NL → SQL layer over our semantic model (in `semantic_model/nuance_semantic_model.yaml`). A non-technical user asks "which language community had the strongest negative framing for the iPhone 17 launch, and what frames drove it?" and gets a structured, cited answer.

**Why it matters.** This is the difference between a tool an analyst uses and a tool a CMO can use directly. Vital for buy-in past the analyst layer.

**UX surface.** Search-bar input on every page; dedicated NL Query page.

---

### F9. Nuance MCP Server

**What it is.** A standalone MCP server (Python) that exposes 5 tools to any MCP-compatible client (Claude Desktop, Claude Code, Cursor, ChatGPT MCP clients):

- `nuance.score_content` (PLCS)
- `nuance.translate_culture` (Cultural Translator)
- `nuance.get_divergence` (CDS lookup)
- `nuance.find_analogs` (Analog Retrieval)
- `nuance.generate_brief` (AI Brief)

**Why it's strategic.** 2026's enterprise reality: every team has internal AI agents drafting content, planning campaigns, analyzing reports. Those agents need governed cultural context. Nuance becomes the cultural-context substrate. This is a Brand-tier feature ($1,290/mo unlocks MCP) — and it's the lever for an enterprise-wide land-and-expand motion.

**Authentication.** OAuth 2.1 against Snowflake (the customer's own account) — so the MCP calls run inside *their* data boundary. This is the security story enterprises want.

---

### F10. Native App distribution

**What it is.** Nuance ships as a Snowflake Native App via the Marketplace. The customer installs it into *their* Snowflake account, brings their own data, and runs Nuance on their own compute. Their data never leaves their boundary.

**Why it matters commercially.** Native Apps trade at 14× EBITDA at exit vs. 6–8× for connected SaaS. Procurement is faster (no DPA, no SOC2 questionnaire — the data never leaves Snowflake). Customer trust is structurally higher.

**Pricing on Marketplace.** Both seat-based (subscription) and event-based custom billing — charge per PLCS scored, per AI brief generated, per Cultural Translator run beyond plan. Mature in 2025/26.

---

## 4. Feature → buyer-value mapping

| Feature | Saves them money | Reduces their risk | Wins them deals |
|---|---|---|---|
| F1 CDS | — | ✅ | — |
| F2 Frames | — | ✅ | — |
| F3 PLCS | ✅ (avoid disaster) | ✅✅✅ | — |
| F4 Translator | ✅ (saves agency fees) | ✅ | ✅ |
| F5 Drift Alerts | — | ✅✅ | — |
| F6 Analogs | — | ✅ | ✅ |
| F7 AI Brief | ✅ (saves analyst time) | — | ✅ |
| F8 Cortex Analyst | ✅ | — | — |
| F9 MCP | — | — | ✅✅ (enterprise expansion) |
| F10 Native App | ✅ (procurement) | ✅✅ | ✅ |

Every feature touches at least one of "save money / reduce risk / win deals". No feature is decoration.

---

## 5. What we are *not* building in v1

- Image/video understanding (cultural framing of visual content). Roadmap H2 2026.
- Voice/podcast ingestion. Roadmap 2027.
- Real-time scraping infrastructure. We rely on customer-provided data + GDELT + Snowflake Marketplace social-data providers.
- A separate iOS/Android app. Mobile traffic for this product is negligible (B2B web-first).
- Per-language fine-tuned models. Arctic Embed v2.0 multilingual is sufficient for v1; we revisit if a customer-specific market shows insufficient quality.

---

## 6. Quality bar / trust requirements

This is a product where wrong outputs damage the customer's brand. Three trust commitments:

1. **Every score has a confidence interval.** PLCS, CDS, sentiment all returned with CI computed from sample size and model agreement.
2. **Every brief is source-cited.** Each claim links to underlying post IDs and timestamps.
3. **The customer can audit any score.** All inputs, prompts, and model outputs are logged in the customer's own Snowflake account (Native App architecture makes this free).

These commitments are codified in `snowflake/03_enriched_tables.sql` (every output table has `model_used`, `prompt_version`, `inference_timestamp`, `confidence` columns) and `prompts/` (versioned prompts with checksums).
