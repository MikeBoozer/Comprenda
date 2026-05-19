"""
Load a Nuance CSV dataset into Snowflake's raw_data.social_posts table.

Usage:
    python data/load_to_snowflake.py
    python data/load_to_snowflake.py --file data/nuance_demo.csv --table raw_data.social_posts
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from snowflake.snowpark import Session


def get_session() -> Session:
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
        "schema":    os.environ.get("SNOWFLAKE_SCHEMA", "RAW_DATA"),
    }
    cfg = {k: v for k, v in cfg.items() if v is not None}
    return Session.builder.configs(cfg).create()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/nuance_demo.csv")
    parser.add_argument("--table", default="NUANCE_DB.RAW_DATA.SOCIAL_POSTS")
    parser.add_argument("--mode", default="append", choices=["append", "overwrite"])
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: {path} not found. Run `python data/generate_demo_data.py` first.",
              file=sys.stderr)
        return 1

    print(f"Reading {path}...")
    df = pd.read_csv(path)
    print(f"  {len(df):,} rows")

    # Normalize column names to UPPER for Snowpark
    df.columns = [c.upper() for c in df.columns]

    # Parse timestamps
    if "POST_TIMESTAMP" in df.columns:
        df["POST_TIMESTAMP"] = pd.to_datetime(df["POST_TIMESTAMP"], errors="coerce")

    session = get_session()
    try:
        print(f"Writing to {args.table} (mode={args.mode})...")
        session.write_pandas(
            df,
            table_name=args.table.split(".")[-1],
            database=args.table.split(".")[0] if "." in args.table else None,
            schema=args.table.split(".")[1] if args.table.count(".") >= 2 else None,
            auto_create_table=False,
            overwrite=(args.mode == "overwrite"),
            quote_identifiers=False,
        )
        # Verify
        cnt_row = session.sql(f"SELECT COUNT(*) AS n FROM {args.table}").collect()[0]
        print(f"[OK]Done. {cnt_row['N']:,} rows in {args.table}.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
