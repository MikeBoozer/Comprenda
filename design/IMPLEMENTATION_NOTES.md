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
| 7 | `pages/8_AI_Brief.py` → §6.4 | ⬜ todo |
| 8 | Other 5 pages: `inject_css()` + `page_header()` only | ⬜ todo |

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
7. **risk_band marker nudging** implemented (the §5.4 *text* asks for it; its
   sample code omitted it). Markers within 4 points get their pills pushed apart.
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

Expect more of these in steps 6–7 (Divergence Matrix, AI Brief). Brief note for
step 7: `call_generate_brief` returns a single `brief_markdown` blob +
`source_post_ids` — the §6.4 structured TOC / numbered sections / inline figures
must be derived from that markdown, not from structured fields.

---

## 4 · Deferred polish list (cosmetic / structural, batch at the end)

Working agreement with the operator: small visual/microcopy discrepancies are
**batched into a final polish pass** (that's what the §9 critique loop is for),
*except* shared-component fixes (in `comprenda_theme.py` / `comprenda_components.py`),
which are done on the spot because they propagate everywhere.

1. **Sidebar wordmark position** — should sit **above** the auto page-nav, not
   below. Tried reordering sidebar flex children via
   `[data-testid="stSidebarUserContent"]`/`stSidebarNav`; **did not work** in
   this Streamlit version (wrong flex parent) and was reverted. Needs the real
   rendered sidebar DOM to target. (§10.1 "CSS that leaks under real Streamlit".)
2. **Entry-page nav label** shows "Comprenda App"; should read "Overview".
   Streamlit derives nav labels from filenames; `page_title` only sets the tab.
   Fixing needs either an entry-file rename (spec pins it to `comprenda_app.py`)
   or switching to the `st.navigation` API (re-architects the router). Decide
   deliberately; don't hack.
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
- **Don't upload `_harness/` to Snowflake.** It's dev tooling; leading underscore
  keeps it out of Streamlit's `pages/` auto-router.
- **Don't change page filenames or reorder pages** (auto-router + onboarding
  order depend on them).
- **LF→CRLF git warnings on commit are benign** on this Windows checkout; ignore.
- **Mutating a widget-keyed `session_state` value must happen in an `on_click`
  callback**, never inline after the widget is instantiated (Streamlit raises
  `StreamlitAPIException`). Bit us on the matrix "Open" + PLCS "sample" buttons;
  both now use `on_click=`. The probes click these buttons to guard the path.
- **The Divergence Matrix grid is sparse** — real CDS data only has the computed
  pairs. The heatmap layers a neutral "not computed" base cell under every
  (a,b) pair so the grid is a full square and hover works everywhere; missing
  pairs are deliberately NOT colored 0.00 (that reads as "aligned", not unknown).
