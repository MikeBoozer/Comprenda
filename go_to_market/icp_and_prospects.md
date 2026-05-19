# Nuance — ICP and Prospect Research

The wedge ICP at launch is **VP/Director of Global Marketing or Head of Brand at mid-market consumer companies that sell in 5+ countries**. This document gives you the exact research workflow to build a 50-name outreach list in ~90 minutes using Perplexity Pro.

---

## ICP scorecard (give a prospect 0/1 per criterion, target ≥7/10)

| Criterion | Why it matters |
|---|---|
| 200–5,000 headcount | Sprinklr-too-small, Buffer-too-big sweet spot |
| Sells in 5+ countries | Multilingual analysis has actual value |
| Has dedicated international marketing team | Buyer exists in the org |
| Active marketing budget $2M–$50M/yr | Can pay $349-$1,290/mo without committee |
| Has had a public cultural-marketing miss in the last 5 years | Pain is alive |
| Uses Snowflake (any tier) | Native App buys are 3× faster |
| Brand is consumer-visible | Cultural risk is existential, not academic |
| Has launched in APAC or LATAM | Cross-cultural pain is acute |
| AI/MarTech budget line exists | Procurement path defined |
| Posts about "global" or "international" marketing on LinkedIn | Buyer is reachable |

---

## Perplexity Pro research prompts

Run these one at a time. Copy results into a spreadsheet. Aim for 50 named prospects.

### Prompt 1 — Generate the long list

> "List 30 mid-market (200-5000 employees) consumer brands that have expanded into Asian, Latin American, or Middle Eastern markets in the last 2 years. For each, give me: company name, HQ country, primary product category, number of countries they currently sell in, approximate annual revenue."

### Prompt 2 — Get the named buyer

For each top-30 company, run:

> "Who is the VP or Director of Global Marketing, Head of International Marketing, or Head of Brand at [Company]? Include LinkedIn URL if possible."

### Prompt 3 — Find the personalization hook

For each:

> "In the last 90 days, what global market move (launch, campaign, expansion, controversy, leadership change) has [Company] made? Give me 1-2 specific facts I can cite in a sales email."

### Prompt 4 — Verify Snowflake usage (optional but high-leverage)

> "Does [Company] publicly use Snowflake as part of its data infrastructure? Check engineering blogs, job postings, conference talks, and case studies."

---

## Spreadsheet template

Create a spreadsheet (`prospects.csv`) with these columns:

```
company,
hq_country,
employees,
countries_sold_in,
revenue_estimate,
buyer_name,
buyer_title,
linkedin_url,
email_guess,
personalization_hook,
uses_snowflake,
icp_score,
priority,
outreach_status,
last_touched_at,
notes
```

For `email_guess`, use Hunter.io free tier (50/mo) or just guess `firstname.lastname@company.com` (60% hit rate at mid-market).

For `priority`, sort by `icp_score DESC` then `uses_snowflake DESC`. Send the top 20 first.

---

## Industries worth biasing toward (best fit for Nuance)

1. **Consumer electronics** — frequent global launches, AI-content-heavy marketing, high cultural risk visibility.
2. **Beauty / personal care** — extreme cultural sensitivity, especially Korean/Japanese/MENA markets.
3. **Apparel / fashion** — recent high-profile failures (Dolce&Gabbana, Balenciaga, H&M) → buyer is paranoid.
4. **Automotive (mid-market EV)** — global launches, AI-generated configurators.
5. **CPG (food/beverage)** — high translation risk, frequent regional adaptations.
6. **Gaming / entertainment** — international audiences are the whole business.
7. **Travel / hospitality** — multi-language customer comms by definition.

## Industries to deprioritize

- B2B SaaS (don't have global marketing pain at the same intensity).
- Defense / regulated industries (procurement cycle too long for self-serve).
- Pure-play DTC US brands (no multilingual surface area).

---

## Tier-2 ICPs (open after initial 50)

- Boutique international PR agencies (5-50 employees) — channel partners.
- In-house brand teams at multinationals (Fortune 500) — Enterprise tier only.
- Hedge fund geopolitical analysts — separate pricing, separate motion.
- NGO communications leads — discount tier; great case studies.

---

## Pacing

Send **10 cold emails per business day**. That's 50/week.

- Monday: 10 personalized cold emails.
- Tuesday: 10 cold emails + reply to Monday's responses.
- Wednesday: 10 cold emails + reply to Mon/Tue.
- Thursday: 10 cold emails + 5 follow-ups to Day +3.
- Friday: 10 cold emails + LinkedIn outreach to anyone who opened but didn't reply.

Expected funnel (mid-market consumer): 50 sent → 18 opened → 6 replied → 3 demo-booked → 1 trial → 1 paid Studio at month-end. Doubles when one good case study lands.
