# real_exports — real Cortex outputs captured from the live account

These JSON files are **verbatim outputs from the live Snowflake account**, captured on
**2026-06-03** just before the free trial lapsed. They back the public demo's fixtures
(`_harness/fixtures.py`), so `comprenda.streamlit.app` shows genuine Cortex results — not
hand-invented sample data — even though the live account is gone. `docs/13_native_app_live_verification.md`
is the human-readable companion (a curated subset of the same run).

## Provenance

| Field | Value |
|---|---|
| Account | `REB37163` (org locator `BKGUVJA-ASB96470`) |
| Region | `AWS_US_WEST_2` |
| Database | `NUANCE_DB` |
| Captured | 2026-06-03 |
| Captured by | `MIKEBOOZER` / role `ACCOUNTADMIN` |
| Models | `claude-4-sonnet` (COMPLETE), `snowflake-arctic-embed-*` (search) |

Corpus: **8 events × 12 languages × 1,440 posts** (`iPhone_17_launch`, `Tesla_robotaxi_debut`,
`Olympics_2026_opening`, `World_Cup_2026_final`, `K-pop_global_tour`, `BrandX_rebrand`,
`EU_AI_act_enforcement`, `Climate_Summit_2026`).

## How they were captured

- **Aggregate / table data** (free read-only `SELECT … --format json`): `kpi`, `event_tags`,
  `languages`, `corpus_freshness`, `event_summary` (per event×lang), `cds_matrix` (latest
  divergence batch, per event), `frame_distribution` (per event), `drift_events`,
  `tracked_entities`, `analog_corpus` (39 historical cases), `narrative_pool` (one real post
  per language×frame, for the search surface).
- **Persisted proc outputs** (harvested from the output tables): `ai_briefs` (latest generated
  brief per event — all 8 events), `translator_runs`, `plcs_runs`, `recent_plcs_scores`.
- **Fresh Cortex calls** made today, tagged `requested_by = 'demo-export'`:
  - `SCORE_CONTENT` on one canonical individualist draft ("…Tesla Robotaxi puts YOU in
    control… leave the crowd behind.") across **all 12 markets** → `plcs_runs.json`
    (en = 25 safe; the 11 non-English markets = 72–75 elevated).
  - `GENERATE_BRIEF` for the 6 events that lacked a brief → folded into `ai_briefs.json`.
  - `TRANSLATE_CULTURE` en→ja (threat-framing reframe) → `translator_runs.json`.
  - `FIND_ANALOGS` (not persisted by the proc) captured directly →
    `analogs_canonical.json` / `analogs_broad.json` (Levi's 501 in India, WeWork, P&G
    Whisper, Toyota Prius, …).

## Notes / honesty

- Snowpark `ARRAY`/`VARIANT` columns serialize as JSON **strings** here (e.g. `TOP_FRAMES`,
  `ADAPTED_VARIANTS`, the `FIND_ANALOGS` wrapper); `fixtures.py` parses them on load.
- `narrative_pool` reads somewhat templated — the bundled demo corpus is synthetic and
  template-thin (noted in `docs/13`). It still shows real per-language/frame variety.
- Regenerate the demo from these files with no Snowflake needed; verify with
  `_harness/.venv/Scripts/python.exe _harness/_smoke.py` and `_smoke2.py`.
