# Comprenda Native App — Packaging & Deployment

This directory packages Comprenda as a Snowflake Native App for Marketplace distribution.
(Internal database/codename plumbing remains `nuance_db` — see the repo README.)

## Prerequisites

- Snowflake CLI installed: `pip install snowflake-cli-labs` then `snow --version`.
- A Snowflake user with `ACCOUNTADMIN` role for the publisher account.
- A working Nuance dev environment (the dev `nuance_db` already populated).

## Project structure for the Native App

```
native_app/
├── snowflake.yml         # snowflake-cli project def + EXPLICIT artifacts allow-list (no globs)
├── manifest.yml          # App metadata, references, privileges
├── setup_script.sql      # Runs in consumer account on install
├── README.md             # This file (also displayed in Marketplace)
├── streamlit/            # Copied from ../streamlit at packaging time (git-ignored)
│   ├── comprenda_app.py  # MAIN_FILE (post-redesign entry; NOT the old nuance_app.py)
│   ├── views/            # the 10 pages: 0_Overview … 9_Narrative_Search (NOT pages/)
│   ├── lib/              # comprenda_theme.py / comprenda_components.py / comprenda_queries.py
│   └── environment.yml
├── data/                 # Parquet demo corpus — PROVIDER-SIDE source, NOT shipped to consumers
└── scripts/              # _gen_table_seeds.py + generated seed_package_data.sql (post-deploy hook)
```

The bundled demo corpus ships as native-app **data content**: `seed_package_data.sql`
(generated from `data/*.parquet` by `scripts/_gen_table_seeds.py`) runs as a provider-side
post-deploy hook that populates the package's `shared_data` schema and GRANTs it
`TO SHARE`. `setup_script.sql` exposes it through versioned `app_instance.src_*` proxy
views, and `provision_app()` materializes it into the app's working tables. Regenerate the
seed after refreshing the Parquet: `python native_app/scripts/_gen_table_seeds.py`.

## Packaging steps

Run these from inside `native_app/` (that's the snowflake-cli project root — see `snowflake.yml`).

```bash
# 1. Copy the live Streamlit app in (git-ignored), and DROP the local preview harness
#    so it never ships. PowerShell:
#      Copy-Item -Recurse -Force ..\streamlit .\streamlit
#      Remove-Item -Recurse -Force .\streamlit\_harness
#    bash:
cp -r ../streamlit ./streamlit && rm -rf ./streamlit/_harness

# 2. Validate the project definition + manifest before uploading anything
snow app validate

# 3. Build the application package, upload the allow-listed artifacts, and install
#    it into your account as an APPLICATION (deploy + create-app in one step)
snow app run

# 3b. `snow app run` also runs the post-deploy hook (scripts/seed_package_data.sql),
#     which populates the package's shared_data corpus and GRANTs it TO SHARE.
#     One-time consumer provisioning then materializes that corpus + builds the two
#     Cortex Search services in app_instance.provision_app() (a setup script has no
#     warehouse). See "After install" below for the two grants + the CALL.
# open Snowflake UI → Data Products → Apps → (the installed app) → the Streamlit object

# 4. Publish to Snowflake Marketplace via the Provider Studio
#    (Snowflake UI → Data Products → Provider Studio → Listings → New)
#    Reference the application package (comprenda_pkg) created above.
```

> Note: `snowflake.yml` defines the package (`comprenda_pkg`) and app (`comprenda_app`)
> entities, so `snow app init` is **not** needed. The `artifacts:` list is an explicit
> allow-list — keep it that way (never glob the root) so secrets/data can't be bundled.

## Marketplace listing copy

Use `go_to_market/marketplace_listing.md` for the listing description, key features, and screenshots prompt.

## Pricing

Configure in Provider Studio:
- **Subscription tiers**: Studio $349/mo, Brand $1,290/mo.
- **Custom Event Billing**: PLCS overage $1/score, AI Brief $10/brief, Translator $2/run.

See `docs/04_business_model.md` for the full pricing rationale.

## Versioning

`manifest.yml` declares `version.name`. Bump it for each release (`v1_1`, `v2_0`, ...).
Consumers can pin or auto-upgrade per their preference.

## After install (consumer side)

This MVP ships a **self-contained demo on bundled synthetic data** — no data binding
required. Because a native-app setup script runs without a warehouse (and so can't
materialize the shared corpus or build a Cortex Search service at install time), there is
one provisioning step. After installing Comprenda from Marketplace, grant the app the
privileges its provisioner needs, then call it:

```sql
-- Substitute your installed application name for `comprenda_app` if you chose another.
USE ROLE ACCOUNTADMIN;  -- the account-level grants below require it
GRANT CREATE WAREHOUSE ON ACCOUNT TO APPLICATION comprenda_app;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO APPLICATION comprenda_app;  -- Cortex COMPLETE/EMBED/Search
-- provision_app() is granted to the app_admin application role, so grant it to your
-- role before calling it:
GRANT APPLICATION ROLE comprenda_app.app_admin TO ROLE ACCOUNTADMIN;
-- The proc can't run USE WAREHOUSE, so its materialize step runs on the caller's
-- warehouse — set any warehouse you own active first:
USE WAREHOUSE nuance_dev_wh;
CALL comprenda_app.app_instance.provision_app();
```

`provision_app()` creates an XS warehouse (`comprenda_wh`), materializes the bundled demo
corpus (shipped as native-app *data content* in the package and shared in — it copies from
the `app_instance.src_*` proxy views into the app's working tables, including the analog
library), and builds the two Cortex Search services. It is **idempotent** — safe to re-run.
Then open the Comprenda
Streamlit (Snowflake UI → Data Products → Apps → Comprenda) and every hero feature works
on the bundled data. All compute runs in the consumer's account; nothing leaves it.

**Phase 2 (bring-your-own-data — not in this build):** bind a multilingual content table
as `consumer_raw_data` (plus an optional email notification integration) and run the
embed → classify → CDS enrichment pipeline over it. That reference is declared optional in
`manifest.yml`, so the demo installs and provisions without it.
