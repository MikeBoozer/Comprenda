# 09 — Streamlit-in-Snowflake Ops Runbook

**Purpose.** How to inspect, edit, and **deploy** the live Nuance Streamlit app from the command line. Read this before changing anything about the running app. It exists because the deployment model is non-obvious and has cost real debugging time.

**Validity note (updated 2026-05-29 — cutover done).** Per [ADR-0004](decisions/0004-repo-canonical-deploy-cutover.md)
(supersedes 0002), the repo→stage **cutover is complete**: the **git repo is now canonical**,
the app serves the Comprenda redesign (`main_file = comprenda_app.py`, `VERSION$2`) deployed
straight from `streamlit/` via the CLI sequence in §3, and the **Snowsight workspace has been
decommissioned** (its `nuance_app` folder emptied). The old "three diverged trees / edit the
workspace + Deploy" model below is retained for context but **no longer how we deploy** — see
the Deploy-button warning in §5. Git-backed deploy remains deferred to Marketplace-prep.

---

## 1. The mental model: THREE separate file trees

This is the single most important thing to understand. There are **three** copies of the app's files, and they are *not* automatically kept in sync:

| Tree | Location | Role |
|------|----------|------|
| **Local git repo** | `streamlit/` in this repo | **Canonical source (since ADR-0004).** Home file `comprenda_app.py` includes the SPCS warehouse fix; deployed wholesale via §3. Editing it still does not change the live app until you run the §3 CLI deploy. |
| **Snowsight workspace** | `snow://workspace/"USER$"."PUBLIC"."DEFAULT$"/versions/live/nuance_app/` | **DECOMMISSIONED (emptied 2026-05-29).** Do not edit or restore — its Deploy button republishes over the cutover (see §5). |
| **The Streamlit object's own stage** | `snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/version$N/` (committed) and `.../versions/live/` (editable) | **This is what the running app actually serves.** |

The deployed app serves its **`default_version`** (= the last *committed* version, e.g. `VERSION$6`) — a frozen snapshot. It never reflects live workspace edits until a new version is committed.

Historically, the Snowsight **Deploy button** was the bridge that copied *workspace → app stage* and committed a new version. **That button breaks if you rename the app's main file** (the app's `comment` metadata still points at the old filename), which is why we deploy via the CLI instead.

---

## 2. CLI access

- Tool: Snowflake CLI (`snow`), connection name **`default`** (account `BKGUVJA-ASB96470`, user `MIKEBOOZER`, role `ACCOUNTADMIN`).
- Command form: `snow sql -q "<SQL>" -c default --format json`
- **Bash escaping:** inside the double-quoted `-q` string, escape `$` as `\$` and inner quotes as `\"`. Stage URIs contain both, e.g.
  `'snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/version\$6/'`.
- The app object is **`NUANCE_DB.OUTPUTS.NUANCE_APP`** (title "nuance"), `main_file = nuance.py`, `run_mode = SpcsOnly`, `compute_pool = SYSTEM_COMPUTE_POOL_CPU`, `query_warehouse = NUANCE_DEV_WH`, `execute_as = OWNER` (owner role = ACCOUNTADMIN, so `snow` as ACCOUNTADMIN runs in the same context the app does).

---

## 3. Deploy a change (the canonical sequence)

This replicates what the Deploy button did. Use it for any change to the live app.

```sql
-- 0. (only if the entry/main file was renamed)
ALTER STREAMLIT NUANCE_DB.OUTPUTS.NUANCE_APP SET MAIN_FILE = 'nuance.py';

-- 1. A fresh "live" version auto-reappears after each COMMIT, so clear it first.
--    (Skip if DESCRIBE shows live_version_location_uri is null.)
ALTER STREAMLIT NUANCE_DB.OUTPUTS.NUANCE_APP ABORT;

-- 2. Open a writable live stage seeded from the last committed version.
ALTER STREAMLIT NUANCE_DB.OUTPUTS.NUANCE_APP ADD LIVE VERSION FROM LAST;
```

```bash
# 3. Push the changed files into the app's OWN stage (not the workspace).
#    Mirror the folder: pages -> /versions/live/pages/, lib -> /versions/live/lib/, root -> /versions/live/
snow sql -q "PUT 'file://C:/Users/micha/Nuance/streamlit/pages/9_Narrative_Search.py' 'snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/live/pages/' AUTO_COMPRESS=FALSE OVERWRITE=TRUE;" -c default --format json

# 4. Remove any orphans left by a rename (e.g. old underscore page name, old main file).
snow sql -q "REMOVE 'snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/live/streamlit_app.py';" -c default --format json
```

```sql
-- 5. Verify the live stage looks right, then commit -> creates VERSION$N+1, which becomes the served version.
LIST 'snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/live/';
ALTER STREAMLIT NUANCE_DB.OUTPUTS.NUANCE_APP COMMIT;
```

**Do NOT use `ALTER STREAMLIT ... PULL`** — it is for git-sourced apps only; this app is workspace-backed and PULL errors with "not created from a git source."

**Avoid `snow streamlit deploy --replace`** for now — it does a CREATE OR REPLACE, which mints a **new app URL** and re-provisions the SPCS container. The PUT-into-stage + COMMIT path above preserves the URL and the app object.

---

## 4. Verify

```sql
DESCRIBE STREAMLIT NUANCE_DB.OUTPUTS.NUANCE_APP;   -- check default_version_name + main_file
LIST 'snow://streamlit/NUANCE_DB.OUTPUTS.NUANCE_APP/versions/version$N/';  -- confirm files/sizes
```

`snow streamlit get-url NUANCE_DB.OUTPUTS.NUANCE_APP -c default` returns the viewable URL.

---

## 5. Gotchas (these cost time before — check them first)

- **"There is already a live version. Please commit it first."** — A live version is open. Run `ABORT` then `ADD LIVE VERSION FROM LAST` (a live version auto-reappears after each COMMIT).
- **⚠️ NEVER use the Snowsight "Deploy" button (and don't restore the workspace).** The Deploy button republishes the **workspace** tree → app stage and commits. On 2026-05-29, pressing Deploy on the workspace `nuance.py` right after a successful CLI cutover **republished the stale pre-redesign app, reset the version history to `VERSION$1`, and reverted `main_file` to `nuance.py`** — the live app silently reverted to the old UI. The workspace `nuance_app` folder was emptied to remove this footgun (ADR-0004). Deploy only via the §3 CLI sequence; view the app via its **URL only** (`snow streamlit get-url …`), never "Projects → Streamlit → edit → Deploy."
- **Deploy button missing in Snowsight.** Expected after a main-file rename (and now moot — see above). Use the CLI sequence above. Reloading/viewing the app is just the **browser** (refresh / reopen the URL) — it never needed the Deploy button.
- **STALE CONTAINER — a deployed fix appears not to work.** The running **SPCS container caches Python modules**; a browser refresh reconnects to the same warm container and may keep running old `lib/`/page code. Symptom: you deploy a verified fix, the SQL works when run directly via `snow sql` (as the app's owner role), but the app still shows old behavior. **It is the container, not the code.** To force a fresh container: commit another version and have the operator fully reopen the app. A temporary `st.expander("debug")` panel in a page (printing the raw query + response) is a reliable way to confirm which version the container is actually running.
  - **Page vs `lib/` asymmetry (important):** Streamlit **re-executes page files every run**, so edits to `pages/*.py` propagate on the next reopen even on a warm container. But `from lib... import ...` hits Python's module cache, so **a `lib/` change can stay stale until the container cold-starts** — the app shows the new page running the *old* lib function (symptom: new UI, but a `KeyError`/missing columns from an out-of-date helper). Fix options: (a) **inline the query into the page** (done for the Divergence Matrix's CDS query — pages always re-exec), or (b) force a genuine container cold-start. Editing `lib/` alone and redeploying is not enough.
- **`ModuleNotFoundError: plotly`.** The deployed package set is `default_packages` only (`python==3.11.*, snowflake-snowpark-python, streamlit`); there is no `user_packages` / `environment.yml` in the workspace. **`altair` ships inside `streamlit` and works without being declared; `plotly` is not installed.** Use Altair for charts.
- **SPCS warehouse/DB context.** The container's default warehouse/DB is wrong, so the home file (`nuance.py`) must run `session.sql("USE WAREHOUSE nuance_dev_wh").collect()` and `USE DATABASE nuance_db` at startup. This is present in the deployed/workspace home file but **not** in the repo's `nuance_app.py` — preserve it in any copy.
- **`GET` "local path is not a directory".** The local target dir must exist first (`mkdir -p`), and use a **Windows** path for the Windows `snow` CLI (`file://C:/...`), not a Git-Bash `/tmp/...` path.

---

## 6. Cost notes

DDL (`ALTER STREAMLIT ...`), `PUT`, `GET`, `LIST`, and `SEARCH_PREVIEW` test queries are cheap (no/minimal warehouse compute). The real cost is the **SPCS container** running while the app is loaded, and **Cortex inference** during enrichment. Batch edits and deploy once; avoid deploy-test-deploy loops. See [docs/05_credit_budget.md](05_credit_budget.md).
