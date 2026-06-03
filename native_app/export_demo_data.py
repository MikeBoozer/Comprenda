"""
Export the Comprenda demo data the Native App bundles.

Run this ONCE on the live dev account, BEFORE packaging the app:

    python native_app/export_demo_data.py

It writes Parquet files into native_app/data/ for the three GENERATED demo tables
(all scalar columns — clean Parquet round-trip):

    social_posts.parquet
    cultural_frames.parquet
    cultural_divergence_scores.parquet

setup_script.sql then COPY INTOs these into app_data.* on install. The two
LIBRARY tables (analog_corpus, frame_taxonomy) are NOT exported here — they're
small static seeds shipped as SQL in the package (scripts/seed_analog_corpus.sql
+ the frame_taxonomy MERGE in setup_script), so they don't need the live DB.

We deliberately DROP the 1024-dim `embedding` / VARIANT columns: Cortex Search
re-indexes from text at install, and Parquet vector/variant round-trips are
fiddly. (If you later ship the bring-your-own-data pipeline, embeddings are
recomputed in-account anyway.)

Connection: reuses ~/.snowflake/config.toml [default] (same as snowpark/deploy.py),
or SNOWFLAKE_* env vars.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from snowflake.snowpark import Session

# Bundled output dir (sits next to manifest.yml; snowflake.yml stages it as /data).
OUT_DIR = Path(__file__).resolve().parent / "data"

# Source table -> explicit scalar column list -> output parquet basename.
# Column lists match the app_data.* DDL in setup_script.sql (MATCH_BY_COLUMN_NAME
# on COPY INTO is case-insensitive, so casing here is cosmetic).
EXPORTS = {
    "social_posts": {
        "source": "NUANCE_DB.RAW_DATA.SOCIAL_POSTS",
        "columns": [
            "post_id", "post_text", "detected_language", "source_platform",
            "post_timestamp", "event_tag", "country_hint", "ingested_at",
        ],
    },
    "cultural_frames": {
        "source": "NUANCE_DB.ENRICHED.CULTURAL_FRAMES",
        "columns": [
            "post_id", "post_text", "detected_language", "event_tag",
            "cultural_frame", "frame_confidence", "sentiment_score",
            "emotional_tone", "model_used", "prompt_version", "inference_timestamp",
        ],
    },
    "cultural_divergence_scores": {
        "source": "NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES",
        "columns": [
            "cds_id", "event_tag", "language_a", "language_b",
            "posts_lang_a", "posts_lang_b", "cds_score", "cds_confidence",
            "topical_overlap", "frame_divergence", "sentiment_divergence",
            "headline_score", "situation_label", "computed_at",
        ],
    },
}


def get_session() -> Session:
    """Same connection logic as snowpark/deploy.py."""
    if os.path.exists(os.path.expanduser("~/.snowflake/config.toml")):
        return Session.builder.config("connection_name", "default").create()
    cfg = {
        "account":   os.environ["SNOWFLAKE_ACCOUNT"],
        "user":      os.environ["SNOWFLAKE_USER"],
        "password":  os.environ.get("SNOWFLAKE_PASSWORD"),
        "private_key_path": os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"),
        "role":      os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "NUANCE_DEV_WH"),
        "database":  os.environ.get("SNOWFLAKE_DATABASE", "NUANCE_DB"),
        "schema":    os.environ.get("SNOWFLAKE_SCHEMA", "OUTPUTS"),
    }
    cfg = {k: v for k, v in cfg.items() if v is not None}
    return Session.builder.configs(cfg).create()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = get_session()
    try:
        for name, spec in EXPORTS.items():
            cols = ", ".join(spec["columns"])
            df = session.sql(f"SELECT {cols} FROM {spec['source']}").to_pandas()
            out = OUT_DIR / f"{name}.parquet"
            # index=False so COPY INTO doesn't see a spurious __index_level_0__ column.
            df.to_parquet(out, index=False)
            print(f"[OK] {name}: {len(df):>6} rows -> {out}")
        print(
            "\nDone. Next: copy ../streamlit into native_app/ (minus _harness), "
            "then `snow app validate` / `snow app run`. See native_app/README.md."
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - surface any export failure verbatim
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
