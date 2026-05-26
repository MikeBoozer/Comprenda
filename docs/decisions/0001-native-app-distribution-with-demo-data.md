# ADR-0001: Distribute Nuance as a self-contained Snowflake Native App with bundled synthetic demo data

- **Status:** Accepted
- **Date:** 2026-05-25
- **Deciders:** Mike (operator)

## Context

Nuance's strategy (see `docs/00_executive_summary.md`, `docs/06_architecture.md`) is
distribution via the **Snowflake Marketplace** as a **Native App**. A Native App
installs into each customer's own Snowflake account and runs there — there is no
provider-hosted instance — which is the basis of the "data never leaves the customer's
boundary" positioning.

At the time of this decision the app works only as a single Streamlit-in-Snowflake
instance in the developer account, hardwired to the dev layout
(`NUANCE_DB.RAW_DATA/ENRICHED/OUTPUTS/INTERNAL/LIBRARY.*`). The four differentiator
procedures (`SCORE_CONTENT`, `TRANSLATE_CULTURE`, `GENERATE_BRIEF`, `FIND_ANALOGS`)
exist only as Python Snowpark sprocs and are not yet packaged. The `native_app/` folder
is a skeleton (manifest + empty-table `setup_script.sql` + reference callbacks). Making
it a functional Native App requires re-targeting the whole application to the app layout
(`app_data.*` + a bound `consumer_raw_data` reference), and deciding how a freshly
installed app obtains data to operate on.

## Decision

Ship v1 as a **self-contained Native App that bundles synthetic demo data** (plus the
analog corpus), pre-enriched, so the app is demoable immediately on install. (Referred
to in planning as "Option A.")

## Alternatives considered

- **Consumer brings their own data (Option B):** the long-term product — the customer
  binds their own content table and runs enrichment on it. Rejected for v1 because it
  requires porting the full enrichment pipeline into the app and handling arbitrary
  customer schemas. Deferred to a later milestone, after the listing is validated.
- **Hosted single-instance SaaS:** the operator hosts one instance and customers connect
  to it. Rejected — it forfeits the "data stays in the customer's account" positioning
  and the Marketplace channel, and adds hosting/auth/multi-tenancy burden.

## Consequences

**Positive**

- Fastest path to a demoable, submittable Marketplace listing (Day 24).
- Preserves the data-residency selling point; no provider-hosted attack surface.
- A reviewer or first customer sees a working product on install.

**Negative / follow-up**

- Requires a full re-target of the procedures + Streamlit from `NUANCE_DB.*` to
  `app_data.*` (procedures re-pointed; Streamlit schema references parameterized so a
  single codebase serves both the dev instance and the app).
- Consumer-BYO-data (Option B) remains unbuilt and is a known future milestone.

**Security / data-privacy guardrails (binding for the build)**

- Bundle ONLY synthetic posts + their enrichment (embeddings/frames/CDS) + the analog
  corpus. The demo corpus is 100% synthetic; no GDELT/HuggingFace real data is bundled.
- EXCLUDE from any bundled export: `tracked_entities` (contains a real owner email),
  `pre_launch_risk_scores`, `cultural_translator_runs`, `ai_briefs`, `drift_events` —
  these ship empty.
- `snowflake.yml` `artifacts` must be a tight allow-list (`manifest.yml`,
  `setup_script.sql`, `README.md`, `streamlit/**`, the demo-seed file). Never glob the
  project root (would bundle `.mcp.json`, `~/.snowflake/config.toml`, `.venv`, scratch
  scripts).
- Audit the staged package contents before publishing.
- Least-privilege manifest: drop privileges v1 doesn't use (e.g. `BIND SERVICE ENDPOINT`,
  `EXECUTE TASK`) until the corresponding features ship.
- Disclose Cortex AI usage in the Marketplace listing.

## Notes

A human-readable session record of this decision and its security review also exists in
Notion ("Project Nuance — Day 23 Planning & Security Review", 2026-05-25). This ADR is
the canonical source; the Notion page is a convenience copy.
