# Snowflake Marketplace — Nuance Listing Copy

Use this verbatim when submitting the Nuance Native App listing through Snowflake's Provider Studio.

---

## Listing Title

**Nuance — Cultural Intelligence Engine**

## Short description (140 char)

> Cross-lingual cultural intelligence for global marketing. Pre-launch cultural risk scoring, divergence tracking, AI cultural briefs.

## Long description

Nuance is the cultural intelligence platform for global brands in the AI era. Every other social-listening tool translates non-English content to English and then runs English-trained sentiment — which destroys the cultural signal you actually needed. Nuance keeps content in its native embedding space using Snowflake's multilingual `arctic-embed-l-v2.0`, classifies it on a 12-category Cultural Frame Taxonomy, and exposes:

- **Pre-Launch Cultural Risk Score (PLCS)** — 0-100 risk score for any draft marketing content in any target market, grounded in 100+ historical analogs.
- **Cultural Divergence Score (CDS)** — proprietary metric quantifying how differently language communities reacted to the same event at the semantic level.
- **Cultural Translator** — frame-preserving content adaptation (NOT translation) that produces 2-3 culturally-resonant variants per market.
- **Cultural Drift Alerts** — hourly monitoring of CDS spikes on tracked brands and events, delivered via email or Slack.
- **AI Cultural Brief Generator** — one-click 2-page Markdown brief with source citations.
- **Analog Retrieval** — semantic search over a curated library of historical campaign-launch divergence patterns.
- **MCP Server** — expose Nuance as a cultural-context tool any enterprise AI agent can call.

Built natively on Snowflake. The app installs into your Snowflake account; your data never leaves your boundary. Compute runs on your warehouse. No DPA renegotiations, no SOC2 questionnaires.

## Key features (bullet list, Snowflake Marketplace surface)

- Native-language multilingual analysis (no translate-first pipeline)
- Pre-launch cultural risk scoring (PLCS)
- Cultural Divergence Score (CDS) — proprietary metric
- Cultural Translator (frame-preserving content adaptation)
- Cultural Drift Alerts via Cortex Alerts
- AI Cultural Intelligence Briefs (2-page Markdown, source-cited)
- 100+ analog historical cases pre-loaded
- Cortex Analyst NL queries
- Cortex Search hybrid retrieval
- MCP server for enterprise AI agents

## Use cases (bullet list)

- Pre-launch cultural QA for AI-generated marketing content
- Cross-cultural post-launch monitoring
- Always-on drift detection on brand or product
- Cultural intelligence briefings for executive teams
- Cultural context substrate for internal AI agents

## Industries

- Consumer goods (apparel, beauty, electronics, CPG)
- Automotive
- Gaming and entertainment
- Travel and hospitality
- International PR / agencies
- Hedge funds (geopolitical risk)

## Required data inputs

- A table or view of multilingual content with these columns:
  - `post_id` (VARCHAR)
  - `post_text` (VARCHAR)
  - `detected_language` (VARCHAR ISO 639-1)
  - `post_timestamp` (TIMESTAMP)
  - `event_tag` (VARCHAR, optional but recommended)
  - `source_platform` (VARCHAR, optional)

The app provides a setup wizard that helps you bind any existing customer-content table to this schema.

## Pricing

- **Pulse**: Free. Limited to 1 event, 3 languages, 5 PLCS scores/month.
- **Studio**: $349/month. 10 events, 8 languages, 50 PLCS, 5 AI briefs, 20 Cultural Translator runs.
- **Brand**: $1,290/month. Unlimited events, 20+ languages, unlimited usage, MCP server, 5 users.
- **Enterprise**: Custom pricing. Native App + SSO + SLA + dedicated CSM + custom frame taxonomies.

Plus usage-based overages: $1/PLCS, $10/AI brief, $2/Cultural Translator run.

## Compute consumption

Nuance runs on the customer's warehouse. Typical monthly compute on 100K-post corpus:
- Embedding refresh: 5-10 Snowflake credits
- Frame classification: 10-15 credits
- PLCS / Translator / Brief workloads: variable (usage-based)

The Native App ships with a Resource Monitor preset capping the Nuance warehouse at 50 credits/day; customers can raise this freely.

## Security & privacy

- Runs entirely inside the customer's Snowflake account.
- No data egress.
- All LLM inference happens via Snowflake Cortex (no external API calls by default).
- Customer controls grants via Snowflake RBAC.
- Full audit trail of inferences in `app_data.inference_logs`.
- Optional: customer can revoke the app's grants at any time without losing their derived data.

## Support

- Documentation: in-app and at `nuance.ai/docs` (replace with your domain).
- Email support: `support@nuance.ai` (replace with your address).
- Brand-tier and above: Slack shared channel.
- Enterprise: dedicated CSM, 24-hour SLA.

## Provider info

- Provider name: Nuance, Inc. (or your legal entity)
- Website: nuance.ai (replace with your domain)
- Contact: hello@nuance.ai

## Categories (pick 2-3 in Marketplace tagging)

- AI & Machine Learning
- Marketing & Advertising
- Analytics
