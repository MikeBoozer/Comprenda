# Nuance Native App — Packaging & Deployment

This directory packages Nuance as a Snowflake Native App for Marketplace distribution.

## Prerequisites

- Snowflake CLI installed: `pip install snowflake-cli-labs` then `snow --version`.
- A Snowflake user with `ACCOUNTADMIN` role for the publisher account.
- A working Nuance dev environment (the dev `nuance_db` already populated).

## Project structure for the Native App

```
native_app/
├── manifest.yml          # App metadata, references, privileges
├── setup_script.sql      # Runs in consumer account on install
├── README.md             # This file (also displayed in Marketplace)
└── streamlit/            # Copied from ../streamlit before packaging
    ├── nuance_app.py
    ├── pages/
    ├── lib/
    └── environment.yml
```

## Packaging steps

```bash
# 1. From the project root, stage the Streamlit code into native_app/streamlit/
cp -r streamlit native_app/streamlit

# 2. Initialize Snowflake CLI project config (one-time)
cd native_app
snow app init --template nuance --no-template

# 3. Deploy the application package + version to your account
snow app deploy

# 4. Test as the consumer
snow app run                  # installs into your account as an APPLICATION
# open Snowflake UI → Apps → Nuance → Streamlit

# 5. Publish to Snowflake Marketplace via the Provider Studio
#    (Snowflake UI → Data Products → Provider Studio → Listings → New)
#    Reference the application package created above.
```

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

1. Consumer installs Nuance from Marketplace.
2. They bind their multilingual content table as `consumer_raw_data`.
3. (Optional) They bind an email notification integration.
4. They run the Nuance Streamlit and seed embeddings via a one-click pipeline button on the Home page.
5. All compute runs in their warehouse; data never leaves their account.
