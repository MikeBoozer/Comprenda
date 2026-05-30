# 12 — Post-rebuild render checklist (operator visual QA)

A human-with-a-browser checklist for confirming the **live Streamlit-in-Snowflake
app reflects a corpus rebuild**. Contract-level verification (running the app's
queries via `snow sql`) confirms the *data*; this checklist confirms the *render* —
the things only a browser can show (charts draw, no tracebacks, numbers look right
on the page).

Run it after any data rebuild / reload (the dedup rebuild on **2026‑05‑30** is the
baseline; the expected values below are from that rebuild — **re-derive them after a
future rebuild**, since corpus size and confidence spread will change).

> Why this is the operator's job: Claude Code drives Snowflake headlessly (SQL
> connector only, no browser), so it verifies every query the app issues but cannot
> *see* the rendered page. The interactive Snowsight pass is yours.

---

## Expected values (2026‑05‑30 dedup rebuild)

| Metric | Expected | Old / stale (red flag) |
|---|---|---|
| Overview · Posts | **1,440** | ~24,960 |
| Overview · Events / Languages | 8 / 12 | — |
| Per (event, language) post count | ~10–20 (en/ja/zh 20, mid 15, pt/hi/it 10) | hundreds |
| Divergence Matrix · Confidence | **0.40 / 0.60 / 0.80** (varies by pair) | flat **1.00** |
| Divergence Matrix · Frame divergence | varies, top pairs ~0.40–0.48 | all ~equal |
| AI Brief · Confidence Notes | varied, names thin langs (hi/it ~0.4) | "1.0 across all pairs", "English (562)" |

---

## 0 · Open the app
- [ ] Log in to Snowsight.
- [ ] Left nav → **Projects → Streamlit** → open **Comprenda**.
- [ ] If it was open *during* the rebuild, **⋮ → Rerun** (or reload the tab) so you're not viewing a pre-rebuild session.
- [ ] **Pre-flight:** editorial theme loads; grouped sidebar (**Workbench / Analysis / Synthesis**) renders with glyphs; **no red error / traceback / `ModuleNotFoundError`**. A stale layout or import error is a deploy/container issue → `docs/09_streamlit_ops_runbook.md`, not a data issue.

## 1 · Overview / Home — the headline numbers
- [ ] KPI row reads **Events 8 · Languages 12 · Posts 1,440**. The **Posts** value is the tell — must be **1,440**, not ~25K.
- [ ] Sidebar diagnostics popover → corpus freshness timestamp is **today / the reload time**.

## 2 · Narrative Search — the "duplicate rows" symptom
- [ ] Run a search (e.g. *"product launch reaction"*).
- [ ] **No two result rows show identical text** (the old bug repeated the same sentence).
- [ ] Apply a **language** filter and a **frame** filter → results narrow sensibly and stay non-duplicated.

## 3 · Divergence Matrix — confidence + heatmap
- [ ] Pick an event (start with **iPhone 17 launch**).
- [ ] Heatmap renders as a full square (12 languages), cells colored, hover tooltips work; uncomputed cells read "Not computed" (not "0.00").
- [ ] Aside **Confidence** row varies by pair — **0.40 / 0.60 / 0.80, NOT a flat 1.00**. Pairs with **hi / it / pt** read **0.40**.
- [ ] **Frame divergence** varies across pairs (top ~0.40–0.48); **situation labels** vary, not all identical.
- [ ] Switch events → the grid pattern changes (not identical every event).

## 4 · AI Brief — the false-confidence narration
- [ ] Generate a brief for **iPhone 17 launch**, languages **en, ja, zh, de**.
- [ ] **Confidence Notes** says confidence **varies**, naming thin languages (**Hindi/Italian ~0.4, "supplement with research"**) and **modest sample sizes (~10–20)**.
- [ ] **Red flags = stale data:** "confidence 1.0 across all pairs" or inflated counts like "English (562)". If present, regenerate the brief.

## 5 · Event Explorer / Frame Distribution
- [ ] Event Explorer: per-language **post counts modest (~10–20)**, each language shows a **dominant frame**; nothing in the hundreds.
- [ ] Frame Distribution: bars render per language; multiple frames per language (not a single spike).

## 6 · Smoke-check the tools the rebuild didn't target (just confirm they render)
- [ ] **Pre-Launch Risk (PLCS):** draft + source/target **language codes** (e.g. `en` → `ja`, not country names) → score + narrative render, no traceback.
- [ ] **Cultural Translator:** one translation → output renders.
- [ ] **Analogs:** a query → analog cards render; frames/markets show as proper pills (not one letter per pill).
- [ ] **Drift Alerts:** page loads (may be empty — fine).

## If something looks wrong
- **Old numbers / stale layout** → app **⋮ → Rerun**, then hard-refresh the tab. Still stale → likely an SPCS container issue → `docs/09_streamlit_ops_runbook.md`.
- **A page errors out** → note the page + error text; check `docs/07_audit_and_fixes.md` (residual risks) first.
- **Data genuinely wrong (not stale)** → capture the page + what you saw and trace it at the query level (the app's queries live in `streamlit/lib/comprenda_queries.py`).

---

## Fast 2-minute pass
**Overview (1,440 posts) → Divergence Matrix (confidence 0.4/0.6/0.8, not 1.0) → AI Brief (no "1.0 across all pairs").** Those three are exactly what the dedup rebuild changed.
