# Project Nuance — UI/UX Design Brief

**Status:** Direction locked, pending mockups (2026-05-27).
**Scope:** The Streamlit-in-Snowflake (SiS) app under `streamlit/`.
**Companion:** The full question-by-question rationale lives in the Notion page *"Project Nuance — Claude Design UI/UX Redesign Briefing (2026-05-27)"* (human-readable journal). **This doc is the canonical, version-controlled record of the locked decisions.** When the direction changes (e.g. after mockups land), update this file rather than relying on the Notion snapshot.

The goal: move the app from a generic default-Streamlit look to a credibly premium, enterprise-grade product that reduces perceived risk for a senior marketing buyer and makes Nuance's intelligence legible and decision-ready.

---

## 1. Division of labor

- **Claude Design (claude.ai)** — produces the aesthetic: hi-fi HTML mockups of the priority screens + a handoff spec with explicit design tokens (hex values, type scale, spacing scale, per-component specs, palette mapped to SiS theme slots).
- **Claude Code** — translates the approved spec into correct SiS code and runs the iteration loop.
- **Rejected:** a multi-agent supervisory "org chart" (manager/liaison/QA/etc.). It adds coordination overhead and quota risk with no added judgment. Replaced with: **1 implementer (Claude Code) + 1 critic subagent + 2 documents (this brief + a critique rubric derived from the spec).**

---

## 2. Aesthetic direction — Editorial / intelligence-report

Serif headlines, generous whitespace, a "reading a Bloomberg/Stratechery brief" feel.

**Why:** Competitors (Brandwatch, Sprout, Meltwater) all look like generic social dashboards. Editorial is the anti-dashboard positioning move and maps to what the product *is* — risk narratives, analog storytelling, source-cited briefs, defensibility. It signals premium judgment, not another metrics widget.

**Rejected alternatives:** Bloomberg Terminal (too data-dense for a CMO buyer); Linear/Vercel (reads as developer SaaS); Stripe/Snowflake-native (safest to execute but surrenders differentiation).

**Fidelity caveat:** Editorial leans on serif type and fine typographic control, which SiS limits. Expect some tradeoffs at translation. Harmonize with Snowsight's surrounding chrome — don't clash, don't imitate Snowflake's blue.

---

## 3. Primary persona — CMO / Brand VP

Wants summary, risk, defensibility; low patience for raw data tables. The product doc's literal buyer is "VP/Director of Global Marketing or Head of Brand," and the why-they-buy is pure CMO language ("one viral cultural misstep is a career event").

**Design implication:** summary-first, decisive "so-what" copy. Serve the strategist's market-comparison needs and the analyst's density/sources/exports through **progressive disclosure** (drill-downs, expanders, "view sources", export buttons) — never as default clutter. Confidence intervals and source citations are first-class trust signals, surfaced via disclosure.

---

## 4. Priority screens

Designed in depth (chosen as distinct UI archetypes that cascade to the other pages):

1. **Home dashboard** — overview/landing pattern (KPI cards, activity feeds, navigation). First impression.
2. **Pre-Launch Risk** — input→results pattern. The killer feature; most important to nail.
3. **Divergence Matrix** — data-viz pattern. Forces chart/color styling into the spec.
4. **AI Brief** *(optional 4th)* — the CMO-facing deliverable where the editorial aesthetic pays off most.

---

## 5. Value-add gaps to fix

Core:
- **Results feel like raw data** — no clear "so what?" / recommendation (Home dumps raw dataframes).
- **Scores are numbers without context** — e.g. PLCS shows "72/100" against nothing.
- **No clear next-action** — for a risk-mitigation product, the next step *is* the value.
- **Flat visual hierarchy** — the main reason it looks generic.

Cheap win:
- **Onboarding / empty states feel cheap** — the product is trial-driven; these states drive conversion. Design real first-run states, not "no data yet."

**Constraint on "context":** Build it from risk bands, confidence intervals, and historical analogs — **not** invented peer/industry benchmarks. There is no benchmark data to populate those.

Deprioritized (already partially built; elevate rather than rebuild): AI reasoning/confidence display, side-by-side market comparison, polished export.

---

## 6. Boldness — mostly conventional, one hero moment

The CMO buyer trusts legible, familiar patterns; bold/unexpected reads as gimmicky and undercuts credibility — and most bold SiS interactions won't survive the deployment environment anyway.

**The one signature moment:** the Pre-Launch Risk **score visualization** (e.g. a styled gauge / risk-band). Keep it buildable in pure Streamlit + CSS or Altair, not a JS widget. Second candidate if budget allows: the Divergence Matrix heatmap.

---

## 7. Brand

No brand exists yet (a globe emoji stands in for a logo, no theme). Claude Design to **propose a wordmark and palette for "Nuance."**

- **Typographic wordmark** (set in text), not an image logo — image hosting in SiS is fiddly.
- Palette must map onto SiS theme slots (primary, background, secondaryBackground, text + a couple of accents) and stay legible inside Snowsight's frame. Distinctive but not clashing; do not just copy Snowflake's blue.

---

## 8. SiS implementation constraints (engineering guardrails)

These are the hard limits that keep the design implementable. They are the reason designs must be reality-checked at translation time.

- **Pure Streamlit + CSS injection via `st.markdown(unsafe_allow_html=True)` only.** No `streamlit-extras` (PyPI-only; not in Snowflake's curated Anaconda channel — won't install) and no bidirectional custom JS components (unsupported/limited in SiS).
- **Charts in Altair** (the available lib). Design the heatmap and any data viz within Altair's capabilities, not D3/JS.
- **Robust CSS only:** prefer the native `[theme]` config + structural CSS (spacing, type scale, bordered containers). Do **not** target Streamlit's internal class-name hashes (`.st-emotion-cache-*`) — they change between versions and break on SiS upgrades.
- **Fonts:** custom web fonts may not load in the SiS sandbox. Use a system/available font or a clean fallback stack.
- **Layout:** full-width desktop (`layout="wide"`); B2B web, mobile negligible.
- **Deploy reality:** the running app serves from the Streamlit object's own stage and the Deploy action costs trial credits — see `docs/09_streamlit_ops_runbook.md`. Iterate locally; deploy in batches.

---

## 9. Iteration approach

The critique→improve loop runs on the Claude Code side, where the code and rendered output live:

1. **Local mock-data preview harness** — stub `get_active_session()` and `lib/nuance_queries` to return fixture data so the app renders locally with no Snowflake credits and no Norton TLS issue. Additive only; production keeps the real session.
2. **Screenshots** via browser automation (Playwright) of each page.
3. **Critic subagent** grades screenshots against the rubric. The rubric is *derived from* the spec (conformance to tokens/components) but is **not identical to it** — it also covers what the spec underspecifies: visual hierarchy and legibility as actually rendered, **SiS-fidelity** (the spec is aspirational HTML; judge the rendered SiS result, not the mockup), cross-page consistency, contrast, empty/loading states, and whether the "so-what" copy lands. Assembled on the Claude Code side (the only side that sees rendered SiS). Any critique-loop Claude Design suggests in its handoff is a useful draft input — merge it, don't adopt it verbatim. Build the concrete rubric once the real spec is in hand, not in advance.
4. **Implement → repeat.**
5. **Final fidelity deploy** to real SiS at the end (one credit cycle) — local Streamlit differs slightly from the SiS-pinned version.

The one required human checkpoint: Mike approves the aesthetic direction (the mockups), which is subjective brand judgment the loop can't make.

---

## 10. Open items / next steps

- [ ] Claude Design delivers hi-fi mockups + handoff spec (with design tokens).
- [ ] Mike approves the aesthetic direction.
- [ ] Claude Code builds the local mock-data preview harness.
- [ ] Claude Code implements the redesign; critic subagent runs critique passes against the rubric.
- [ ] Final fidelity deploy to SiS.
- [ ] Update this brief if the direction shifts after mockups (this is a living decision record).
