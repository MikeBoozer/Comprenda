# Comprenda Redesign — Implementation Notes

> Living log of the UI/UX redesign implementation (the `Claude-Code-Handoff.md`
> build). Records what was **changed or omitted** versus the spec and **why**,
> plus things a future session must know before continuing. Update this as you
> go. Last updated: **2026-05-28**.

The companion design source is `design/Claude-Code-Handoff.md` (the spec) and
`design/index.html` + `design/screens.jsx` (the artboards). Section references
below (§) point into the handoff.

---

## 1 · Status — where the build is

Following the §8 master prompt, one step at a time, committing between each and
waiting for the operator's "go". Commits land on `main` (per the master-prompt
workflow + this repo's existing direct-to-main pattern).

| Step | Scope | State |
|------|-------|-------|
| 0 | File renames `nuance_* → comprenda_*` + imports | ✅ done |
| 1 | `lib/comprenda_theme.py` (`inject_css`) | ✅ done |
| 2 | `.streamlit/config.toml` theme | ✅ done |
| 3 | `lib/comprenda_components.py` helpers | ✅ done |
| — | Local preview harness (`streamlit/_harness/`) | ✅ done (extra) |
| 4 | Home `comprenda_app.py` → §6.1 (+ empty state) | ✅ done |
| 5 | `pages/1_Pre_Launch_Risk.py` → §6.2 (+ empty state) | ✅ done |
| 6 | `pages/4_Divergence_Matrix.py` → §6.3 (Altair) | ✅ done |
| 7 | `pages/8_AI_Brief.py` → §6.4 | ✅ done |
| 8 | Other 6 pages: `inject_css()` + `page_header()` only | ✅ done |
| 9 | `pages/2_Cultural_Translator.py` → full `ScreenTranslator` artboard | ✅ done |
| 10 | Consistency pass: bodies of the 5 artboard-less pages | ✅ done |
| 11 | Sidebar re-arch: `st.navigation` router + grouped glyph nav | ✅ done |

**Step 11 — the sidebar re-architecture (operator-requested).** The grouped
nav (Workbench / Analysis / Synthesis), glyph sigils, and wordmark-above-nav
from the `screens.jsx` "Sidebar treatments · A" artboard are only reachable via
the `st.navigation` API, so the app moved off Streamlit's filename auto-router:
- `comprenda_app.py` is now a **router** — it declares every page with
  `st.Page(...)`, calls `st.navigation(ordered_pages, position="hidden")`, then
  renders the whole sidebar itself via `render_sidebar()` and `pg.run()`.
- The page files moved from `pages/` to **`views/`** (folder renamed, filenames
  unchanged). **This is load-bearing:** Streamlit auto-discovers a folder named
  literally `pages/` and builds its own multipage nav from it — which ran
  *alongside* `st.navigation` and served each file directly at its old URL
  **without the router's chrome** (symptom: a lone page, no sidebar, no wide
  layout). Renaming the folder disables that auto-MPA so `st.navigation` is the
  only router. ⚠️ Do not recreate a `pages/` folder. (AppTest did **not** catch
  this — it runs one file at a time; only the real server double-routes.)
- The home/Overview content moved to **`views/0_Overview.py`** (the `default`
  page). Order/grouping/labels come from `_NAV_SPEC` in the router.
- Every page **dropped `st.set_page_config` and `sidebar_brand()`** — the router
  owns global config and the sidebar (a page calling `set_page_config` under the
  router would error). Pages still call `inject_css()` (idempotent).
- Glyphs ride in the `st.page_link` **label** (`st.Page(icon=…)` rejects
  arbitrary Unicode sigils); active highlight is `a[aria-current="page"]`.
- This **resolves deferred-polish #1 and #2** below (wordmark position, Overview
  label).
- ⚠️ **DEPLOY RISK:** `st.navigation` needs the SiS Streamlit runtime ≥ 1.36.
  The harness is 1.58 (verified: `AppTest` runs the router clean), but the
  *deployed* SiS version is unverifiable until push — an older runtime will
  fail to start. Confirm at deploy time. (See §6.)
- ✅ **Cortex omnibar (done).** `omnibar()` renders once in the router (above
  every page) as an `st.popover` command bar wired to the existing **Cortex
  Search** (`narrative_search`). A `st.form` gates the query so a Cortex call
  only fires on submit (not every rerun); results persist in `session_state`.
  Styling is scoped to `[data-testid="stPopover"]` (unique to the omnibar).
  - `/` and `⌘K` shortcuts **dropped — not feasible** under the no-JS rule
    (Streamlit has no keyboard API and strips injected `<script>`); the bar
    opens on click.
  - The artboard's synthesized **answer + generated-SQL** view is **Cortex
    Analyst**, a **deferred follow-up**: no Python backend exists, it needs the
    `semantic_model/` deployed, and it can't be validated in the harness. The
    shipped omnibar returns matching posts (search), not an NL answer.
- ✅ **Session diagnostics (done).** `session_diagnostics()` renders a small,
  quiet **"Session & environment"** popover at the **bottom of the sidebar**
  (utility chrome belongs with the nav, reachable without scrolling a long
  page; the floating panel stays readable despite the narrow sidebar). For
  support / buyer-side devs. **Click-gated** (a "Load details" button) so the
  metadata queries fire only on demand, not on every navigation. Shows only the user's own non-sensitive context — role,
  warehouse, database, schema, region, Snowflake + Streamlit version, session ID,
  last query ID — plus corpus counts and `MAX(ingested_at)` freshness, and a
  copy-paste block. Deliberately **omits** `CURRENT_USER` / `CURRENT_ACCOUNT`
  (identity/locator) — nothing cross-tenant or secret. New read-only helpers
  `get_session_context` / `get_corpus_freshness` in `comprenda_queries` (+ harness
  fixtures). Distinct from the per-run "About this run" panels on PLCS /
  Translator / AI Brief, which stay (they describe an actual inference run).

Step 8 gave all six remaining pages the shared chrome (theme + `page_header`)
but left their **bodies** as raw Streamlit. Step 9 promoted Translator out of
that set — it has a full `ScreenTranslator` artboard (variant cards, risk
comparison, CTA) and was mis-bucketed into the header-only group. Step 10 did
the **consistency pass** on the other five (Event Explorer, Frame Distribution,
Drift Alerts, Analog Retrieval, Narrative Search): they have **no artboard**, so
rather than a §9 fidelity loop their bodies were restyled by extrapolating the
established design language — `section_head` (now shared in
`comprenda_components`), KPI strips, editorial cards, frame/market pills,
`frame_share_bar`, and result-persistence in `session_state`. No SQL/proc/query
changes; raw tables and the original facet chart are preserved inside expanders.
Because these are extrapolation (no pixel target), they need an operator eyeball
more than the artboard pages did — the §9 critic loop can't score them.

---

## 2 · Deliberate deviations from the spec (with rationale)

These are intentional. Don't "fix" them back without reading the reasoning.

1. **Wordmark is serif ROMAN 700, not italic.** §2.2 says "roman (not italic),
   700"; the §8 constraint summary says "italic". The two conflict; the detailed
   type spec (§2.2) wins. *Open question for the operator — flip to italic is a
   one-line change in `sidebar_brand()`.*
2. **Empty-state brand letter is "C"** (Comprenda), per the artboard. The §6.1
   prose still says "N" — stale from the Nuance→Comprenda rename.
3. **`nu-` CSS class prefix kept as-is.** Per operator instruction: internal,
   non-user-facing; renaming would touch every component for no user benefit.
4. **Infra identifiers kept as Nuance.** `nuance_db`, `nuance_dev_wh`,
   `nuance_app_role`, the deployed `STREAMLIT app_instance.nuance_app` object,
   and all SQL — these are non-user-facing deployment/DB names, out of scope for
   the "user-facing strings" rename. Only Python module names + in-app strings
   moved to Comprenda.
5. **Step-0 rename scope.** Only `comprenda_app.py` + `lib/comprenda_queries.py`
   and their imports were renamed. SQL/query logic untouched (hard constraint).
6. **§5.3 PLCS card CSS fix.** `font:var(--mono)` (malformed shorthand, silently
   dropped) → `font-family:var(--mono)` so the confidence number renders in mono.
7. **risk_band marker nudging** (the §5.4 *text* asks for it; its sample code omitted it).
   ⚠️ The original implementation was a **silent no-op** — the pill was nested inside its own
   2px marker line, so its nudged `left` % resolved against 2px and never moved; tied markets
   drew on top of each other and one was invisible (found in the 2026-05-29 deploy-QA render
   check). **Fixed (`VERSION$4`/`$6`):** pills are direct children of the band (band-relative
   `left`), reserve 48px headroom, and crowding pills (within 8 pts) **stack onto a second row**
   directly above each other rather than being shoved sideways. Used by PLCS + Translator re-score.
8. **frame_share_bar** built from prose only (§5.8 gives no code); added an
   optional `risk_frame` arg for the oxblood "absorbing frame" segment.

---

## 3 · Real-data gaps — artboard wants data the procs don't return

The artboards show values the live stored procs / queries do **not** provide.
Per the handoff's own honesty rule ("nothing is invented; everything is
sourced") and §10.3, these were implemented truthfully rather than faked. Each
is a **round-trip candidate**: either change a query (out of scope for the
redesign steps) or revise the design.

| # | Where | Artboard wants | Proc/query actually returns | What we did |
|---|-------|----------------|------------------------------|-------------|
| A | Home KPI strip (§6.1) | 6 metrics **with** week-over-week deltas | `get_kpi_summary` → 4 counts, no deltas | Render 4 metrics, no deltas. Noted inline in `comprenda_app.py`. |
| B | PLCS deep narrative (§6.2) | Contributor bars: frame / lexicon / analogs / sentiment **weights** | `call_plcs` → no per-axis weights | Show the model's `risk_narrative` prose + frame pills instead. |
| C | PLCS risk band (§5.4/§6.2) | Historical analogs as **ticks behind markers** (need 0–100 positions) | `call_plcs` → analog **post_ids**, not scores | Render market markers only; no analog ticks. |
| D | PLCS rec band (§5.6) | "Export as PDF" / "Share with team" | no implementation | Omitted (no dead buttons). Primary Translator handoff is real. |

The PLCS **three-analogs column IS real** (from `call_find_analogs`:
case_name / company / year / outcome_summary / distance→gap).

| E | AI Brief (§6.4) | Structured sections + inline frame bars + dot-chart | `call_generate_brief` → one `brief_markdown` blob + `source_post_ids` | Parse the markdown into title + sections (TOC, §-numbered article). Editorial per-section h2 sentence isn't separable, so the section heading is the h2. Figures drawn from **existing** query helpers instead of the blob: frame bars from `get_frame_distribution`, divergence dot-chart from `get_cds_matrix` — placed after the article (markdown is opaque to inline injection). Title falls back to a derived "Reading the room: {event}." when the blob has no leading `# H1`. Meta shows sources-cited count + language count (no total post count — not returned). PDF/Share omitted; Download Markdown + raw-markdown copy are real. |
| F | Translator (`ScreenTranslator`) | Per-variant **re-scored risk** (0–100) + confidence + "original vs. adapted" comparison + "Adapt for Korea (61)" handoff + Export PDF / Share | `call_translator` → `text` / `frame_shift` / `rationale` per variant only — no risk, no confidence | Re-scoring made **real** by composing the existing `call_plcs` proc (no signature change), but **opt-in** behind a button so the default generate spends no extra trial credits. When invoked it scores the original (source→target, as PLCS did) + each variant (target→target, since variants are written in-market) and renders them on the signature `risk_band`. Cross-market "Adapt for Korea (61)" CTA dropped (needs the original PLCS run's per-market scores, not carried into this page) — replaced by the in-page market selector. Export PDF / Share omitted (no dead buttons, per item D). Per-variant "Copy text" → a real `st.code` block in a "Copy variants" expander (native copy button) rather than a fake button. |

**Round-trip / QA flags for item F:** (1) the re-score adds *N+1* Cortex
inferences per click on the live app — bounded and opt-in, but worth watching
against the 300-credit cap. (2) The re-score *semantics* (original scored
source→target; variants scored target→target) is a deliberate modeling choice,
not from the spec — confirm it reads correctly against real `SCORE_CONTENT`
output in the manual deploy QA. One-line knobs: make re-scoring always-on by
calling it inside the `generate` block; or remove it entirely and drop the
comparison section.

---

## 4 · Deferred polish list (cosmetic / structural, batch at the end)

Working agreement with the operator: small visual/microcopy discrepancies are
**batched into a final polish pass** (that's what the §9 critique loop is for),
*except* shared-component fixes (in `comprenda_theme.py` / `comprenda_components.py`),
which are done on the spot because they propagate everywhere.

1. ✅ **RESOLVED (step 11).** Sidebar wordmark now sits above the nav —
   `render_sidebar()` draws the entire sidebar on top of
   `st.navigation(position="hidden")`, so order is fully under our control.
2. ✅ **RESOLVED (step 11).** Nav labels now come from `st.Page(title=…)` in the
   router (`_NAV_SPEC`), not from filenames — "Overview" reads correctly. This
   took the `st.navigation` re-architecture, done deliberately at operator
   request (not a hack).
3. Items A–D in §3 above (real-data gaps) also surface in any final pass.
4. **Divergence Matrix cell-click selection** (§6.3 "clicking a cell rerenders
   the aside") replaced with a **selectbox** for the pair. Altair cell-click via
   `st.altair_chart(on_select=...)` varies across Streamlit/SiS versions; the
   selectbox achieves the same outcome reliably. Revisit if SiS Streamlit is
   confirmed to support `on_select`.
5. **Matrix empty-state "three events"** lists real event tags but with a
   generic one-line description (no per-event post/lang counts — that data needs
   a query the redesign step doesn't add). Artboard shows specific counts.
6. **DONE in-stream** (kept here for the record): sidebar subtitle →
   "Don't translate. Understand." in sentence case.

---

## 5 · The local preview harness (`streamlit/_harness/`)

Renders the app in a browser with **fixture data — no Snowflake, no trial
credits**, and it sidesteps the machine's Norton TLS interception entirely
(nothing talks to `snowflakecomputing.com`). This realizes the local-preview
open item from `docs/11`.

- **Run:** `powershell -ExecutionPolicy Bypass -File streamlit\_harness\run.ps1`
  then open `http://localhost:8501`. First run builds a venv
  (`_harness/.venv`, gitignored) with `streamlit` + `altair`; snowpark + pandas
  come from system Python via `--system-site-packages`.
- **How:** `sitecustomize.py` is auto-imported at interpreter startup (the
  launcher puts `_harness/` on `PYTHONPATH`). It patches
  `get_active_session` → `FakeSession` and pre-seeds
  `sys.modules['lib.comprenda_queries']` with fixture stubs **before** any app
  code runs. Inert outside the harness.
- **Fixtures** (`fixtures.py`) are grounded in the **real** contracts
  (`snowpark/deploy_plcs.py`, `deploy_ai_brief.py`, `comprenda_queries.py`
  column names) so screens reflect real output shapes, not invented values.
  Snowpark `.to_pandas()` upper-cases columns, so DataFrame fixtures use UPPER.
- **Empty states:** set `HARNESS_EMPTY=1` before launching to preview first-run
  states (zeros KPIs / empty DataFrames).
- **Smoke checks:**
  - `python _harness/check.py` — runs every page through Streamlit `AppTest`
    in-process; reports uncaught exceptions (no visual check).
  - `python _harness/probe_plcs.py` — exercises the button-gated PLCS scored
    path (fill draft → click Score → render results).
  - `python _harness/probe_translator.py` — exercises the Translator path
    (sample callback → Generate → opt-in Re-score → risk comparison).
  - `python _harness/probe_search.py` — exercises the button-gated result
    paths on Analog Retrieval (sample → Find → cards) and Narrative Search
    (query → Search → cards), where card-rendering reads real fields.
  - `python _harness/probe_omnibar.py` — drives the router: opens the Cortex
    omnibar, submits a query through the form, renders search results.
  - `python _harness/probe_diag.py` — drives the router: clicks the diagnostics
    footer's "Load details" and renders session context + corpus freshness.

### Harness gotchas worth knowing
- The `_harness/check.py` import order matters: it puts the app dir on
  `sys.path` and imports the **real** `lib` package *before* overriding only the
  `comprenda_queries` submodule — otherwise pre-seeding the fake short-circuits
  the parent import and the real `lib.comprenda_theme`/`components` won't resolve.
- `run.ps1` must stay **pure ASCII** — Windows PowerShell 5.1 reads `.ps1` as
  ANSI, so em-dashes/ellipses become mojibake and break parsing. (`.py` files are
  read as UTF-8 by Python, so non-ASCII there is fine.)
- `run.ps1` launches Streamlit with `--server.headless true` to skip the
  first-run email prompt, which otherwise blocks startup on stdin (symptom:
  "localhost refused to connect").

---

## 6 · Verification — what's checked vs. what isn't

- **Automated, every step:** `AppTest` (does it run without exceptions, right
  structure/copy). This is the ~80% proxy from §9.4/§10.3.
- **NOT automated:** visual fidelity vs. the artboards — the agent environment
  can't screenshot. The operator reviews in the browser via the harness.
- **NOT coverable locally at all (needs one real Snowflake deploy at the end):**
  whether real `SCORE_CONTENT`/`GENERATE_BRIEF` JSON fits the layout, whether
  the trial role's permissions allow the SQL, whether SiS falls back past the
  serif to Georgia on a Windows VDI, and Snowsight chrome conflicts. Plan that
  manual QA pass before declaring done.

---

## 7 · Hard rules for any future session (don't break these)

- **Do not change SQL or proc signatures** (hard constraint). Data gaps go to the
  round-trip (§3), not into edited queries — unless the operator explicitly opens
  that scope.
- **CSS via `[data-testid]` / semantic tags / `nu-*` only.** Never target
  `.st-emotion-cache-*` (rotates per Streamlit version).
- **Altair only** for charts; no Plotly/JS components; no pip packages beyond
  `environment.yml` (the harness venv is local-only and never deployed).
- **Don't upload `_harness/` to Snowflake.** It's dev tooling.
- **Page files live in `views/`, NOT `pages/` (since step 11).** A folder named
  `pages/` triggers Streamlit's auto-multipage discovery, which double-routes
  against `st.navigation` (see step 11). Routing/order/labels are controlled
  entirely by `_NAV_SPEC` in `comprenda_app.py`. To add a page: drop it in
  `views/`, add an `st.Page(...)` + glyph to `_NAV_SPEC`, and a `check.py`
  target. Filenames are still numbered for human ordering only.
- **LF→CRLF git warnings on commit are benign** on this Windows checkout; ignore.
- **Mutating a widget-keyed `session_state` value must happen in an `on_click`
  callback**, never inline after the widget is instantiated (Streamlit raises
  `StreamlitAPIException`). Bit us on the matrix "Open" + PLCS "sample" buttons;
  both now use `on_click=`. The probes click these buttons to guard the path.
- **The Divergence Matrix grid is sparse** — real CDS data only has the computed
  pairs. The heatmap layers a neutral "not computed" base cell under every
  (a,b) pair so the grid is a full square and hover works everywhere; missing
  pairs are deliberately NOT colored 0.00 (that reads as "aligned", not unknown).

---

## 8 · Deploy-QA checklist (the one real-Snowflake pass)

The harness verifies structure/wiring with fixtures; it can NOT verify these.
Run this once on a real SiS deploy, in order — blockers first. Deploy via the
CLI sequence in `docs/09` (editing the workspace file tree does NOT update the
running app).

> **Cutover done + A.1 PASSED (2026-05-29).** The redesign was deployed to real SiS via the
> ADR-0004 repo→stage cutover (`VERSION$2`, `main_file = comprenda_app.py`); the Snowsight
> workspace was decommissioned (deploy only via the `docs/09` CLI sequence — never the Deploy
> button, which reverted the cutover once). App confirmed starting + rendering on **Streamlit
> 1.57.0**, title set to "Comprenda". **Deploy-QA A+B+C all PASSED (2026-05-29)** through `VERSION$3`; only D13 (legal
> text) is open. The known data issue remains — `cds_confidence` pinned at 1.0 (raw-count formula
> × ~17× duplication; *scores* vary fine; the AI Brief even narrates it as a strength), see
> `docs/07` Finding C. Remaining project work: data rebuild + native-app build. Deploy via `docs/09`.

**A. Blockers (app won't start / core breaks):**
1. ✅ **PASSED.** **`st.navigation` support** — SiS Streamlit runtime is **≥ 1.36** (verified
   live 2026-05-29: app started clean with the `st.navigation` router). Was the top blocker.
2. **Model config resolves** — `nuance_db.internal.config` model names exist in
   `SNOWFLAKE.CORTEX.LIST_MODELS()` (the "claude-4-sonnet not found" gotcha).
3. **App-role privileges** — the trial/app role can run every page's SQL, all
   Cortex functions (COMPLETE / SEARCH_PREVIEW), and the diagnostics
   `CURRENT_*` + `MAX(ingested_at)` query.

**B. CSS that targets version-specific testids — ✅ verified 2026-05-29 (SiS Streamlit 1.57.0):**
4. ✅ Content cap (1280px, centered) good; popover width widened `460→505px` (`VERSION$3`);
   hidden auto-nav good (single grouped nav only). **Exception:** the oxblood active-nav
   (`a[aria-current="page"]`) is **inert on 1.57** — the active `st.page_link` `<a>` does not
   expose `aria-current`, so Streamlit's default **darker-beige** active state shows. Operator
   accepted beige; the `!important` rule is kept (see the note in `lib/comprenda_theme.py`).
5. ✅ **Serif fallback** — wordmark/headings render serif (no Georgia fallback).
6. ✅ **Snowsight chrome** — no overlap, clipping, or double-scrollbars.

**C. Real proc/query output fits the layouts — ✅ verified 2026-05-29 (one CLI call per proc):**
7. ✅ PLCS `SCORE_CONTENT` (rich: en→ja score 85 / conf 0.9 / rich narrative; **+ graceful
   "insufficient data" fallback** — note `target_market` is a **language code**, not a country
   name), Translator `TRANSLATE_CULTURE` (3 variants w/ frame_shift+rationale+adapted text),
   AI Brief `GENERATE_BRIEF` (markdown → title + `##` sections + table), `FIND_ANALOGS` (real
   library cases) — all fit.
8. ✅ **Translator re-score** — mechanism verified (PLCS resolves `ja`; ja→ja valid). PLCS
   `confidence` is dynamic (0.9 vs 0.1) — i.e. NOT the degenerate metric (that's only `cds_confidence`).
9. ✅ **Omnibar** — `SEARCH_PREVIEW` returns the expected lowercase columns (dup-looking results = corpus issue, not wiring).
10. ✅ **Diagnostics** — `CURRENT_*` + freshness resolve.
11. ✅ **Corpus loaded** — 12 languages, 8 events.

⚠️ **Content (not layout) finding:** the AI Brief "Confidence Notes" narrates the degenerate
`cds_confidence=1.0` and the duplicated sample sizes (562/312/250) as a credibility *strength* —
another reason the data rebuild matters (see `docs/07` Finding C). Layouts are unaffected.

**Verification scope:** contract-level via CLI, then an operator browser render click-through
(2026-05-29). **#1 PLCS + #2 Translator confirmed clean** (incl. tied-marker stacking); **#5
omnibar/diagnostics good**. The check surfaced + fixed render bugs across `VERSION$4`–`$7`:
risk_band marker nudge was a silent no-op (tied markets hid each other), pills covered the text
above the band, the re-score button was too tight, AI-Brief figure spacing, and the **analog
per-character pill bug** (`failure_frames`/`affected_markets` come back as JSON *strings* and were
iterated per character). **#3 AI Brief + #4 Analogs fixes deployed in `VERSION$7`, pending final
operator re-confirm.** Item 8 (re-score) is exercised for real. (Caption wrap on the divergence
figure left as-is: one-lining it needs widening the shared section-head or truncating the table
name — both worse than a clean two-line caption.)

**D. Operational:**
12. ✅ **Credit guard** — ~41 credits used of the ~$400 trial ($281 left); the WAREHOUSE resource
    monitor (300) does NOT meter SPCS/Cortex, so the real driver is SPCS container uptime.
13. **Legal footer** — scaffold present; disclaimer + Terms/Privacy **text not yet finalized (open)**.
