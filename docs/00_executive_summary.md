# Project Nuance — Executive Summary

## In one sentence

Nuance is the cultural intelligence platform for global brands in the AI era: it scores how marketing content, product launches, and brand events land *differently* across language communities in native embedding space — and flags risks before launch.

## In one paragraph

Every multinational marketing team now relies on AI agents to draft and translate content for non-English markets. Those agents are bad at cultural nuance, and existing social-listening incumbents are equally bad — they translate to English first and then run English sentiment models, destroying the cultural signal. Nuance is a Snowflake-native SaaS that keeps content in its native language space using multilingual embeddings (`snowflake-arctic-embed-l-v2.0`), classifies it on a 12-category cultural frame taxonomy, and exposes a proprietary Cultural Divergence Score (CDS) plus a Pre-Launch Cultural Risk Score (PLCS) that marketers can act on. Buyers get self-serve access at $349–$1,290/month vs. Brandwatch and Sprinklr's $800–$200K/year sales-led contracts. The MVP is buildable on Snowflake's $400 / 29-day trial.

## What changed from the original CulturePulse plan

| | CulturePulse v0 | Project Nuance v1 |
|---|---|---|
| Positioning | "Cross-lingual social listening" | "Cultural QA layer for AI-era marketing" |
| Buyer focus | Three verticals at once | Wedge: global brand/marketing teams |
| Killer feature | Retrospective Cultural Divergence Score | **Pre-Launch Cultural Risk Score** (predictive) + CDS (retrospective) |
| Workflow value | Read-only analytics | + Cultural Translator (rewrites content per cultural frame) + Drift Alerts |
| Defensibility | CDS + native-language embeddings | + Analog Retrieval (semantic search over historical campaign-launch divergence patterns) + Cultural Frame Marketplace (network effect) |
| Distribution | Marketplace as Native App | Marketplace + MCP server (cultural-context layer that any enterprise AI agent can call — critical 2026 positioning) |
| Pricing | $299/$799/Enterprise | $349/$1,290/Enterprise with usage-based overages (PLCS scores, AI briefs, translator runs) — better expansion economics |
| Trust layer | Implicit | Confidence intervals on every score, source-cited briefs, auditable trail in customer's own Snowflake instance |

## The killer features in plain English

**1. Pre-Launch Cultural Risk Score (PLCS).** A marketer pastes a draft tagline, ad copy, or product name plus target markets. Nuance returns a 0–100 risk score per market plus a structured "what could go wrong" report, grounded in semantically-similar historical content and cultural frame analysis. This is the feature that closes the deal — every CMO has heard the Mercedes "rush to die" / HSBC "Do Nothing" stories and is terrified of being the next one.

**2. Cultural Divergence Score (CDS).** After a campaign launches, Nuance shows how different language communities reacted at the *semantic* level — not just sentiment polarity. Proprietary, defensible, citable.

**3. Cultural Translator.** Given source content, produces culturally-adapted variants per target market that preserve intent but shift the *frame* (e.g., individualist → collectivist, opportunity → security). Directly drop-in for the marketing team's workflow — this is where Nuance becomes a daily-use product.

**4. Cultural Drift Alerts.** Real-time Cortex Alerts on tracked brands/topics: when CDS spikes between any pair of language communities, push to Slack/email. Transforms Nuance from "tool you log into" to "intelligence feed you can't live without."

**5. Analog Retrieval.** Semantic vector search over a curated library of past campaign-launch divergence patterns. "This launch's CDS profile matches HSBC 2009 in China. Here is what went wrong then." Pattern-matching as competitive moat.

**6. Nuance MCP Server.** Cultural context as a tool any enterprise AI agent can call. Aligns with the 2026 reality that every enterprise has internal agents that need governed context. Massive upsell vector for the Brand and Enterprise tiers.

## Business model headline

| Tier | Price | Target | Anchor unit economics |
|---|---|---|---|
| Pulse (free) | $0 | Trialers, students | Lead-gen funnel |
| Studio | $349/mo | Solo marketers, boutique PR | 1 user, 10 events, 50 PLCS/mo, 8 languages |
| Brand | $1,290/mo | Mid-market global brands | 5 users, unlimited events, Cultural Translator, Drift Alerts, MCP access |
| Enterprise | $30K–$120K ACV | Multinationals, hedge funds, NGOs | Native App in customer's Snowflake, SSO, SLA |

Usage-based overages: $1/PLCS beyond plan, $10/AI brief, $2/Cultural Translator run.

**Conservative ARR target at month 12**: ~$250K — 40 Studio + 8 Brand + 1 Enterprise. Single-founder achievable.

## What "minimal effort on Mike's part" actually means

Mike needs to do exactly these things, in order, after this session:

1. **(10 min)** Sign up for Snowflake free trial at `signup.snowflake.com`.
2. **(2 min)** Open a SQL worksheet, paste `snowflake/00_bootstrap.sql`, click Run All.
3. **(5 min)** Run `python data/generate_demo_data.py` + `python data/load_to_snowflake.py` locally (one-time auth via SnowSQL or the Snowflake Python connector — config file template provided).
4. **(20 min)** Run the four enrichment SQL files in sequence (each is one click). Total credit cost ~$15.
5. **(5 min)** Upload the Streamlit app via Snowflake's UI.
6. **(optional, 1 hr)** Polish the demo with the launch kit assets, record a Loom, post to LinkedIn/Product Hunt.

Everything else — the architecture, the SQL, the Python, the prompts, the GTM copy, the pricing logic — is already written in this repo.
