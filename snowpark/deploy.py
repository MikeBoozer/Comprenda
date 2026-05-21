"""
Deploys the core Nuance Snowpark UDFs and stored procedures to Snowflake.

Run once after `00_bootstrap.sql`:
    python snowpark/deploy.py

Reads connection details from ~/.snowflake/config.toml (default connection)
or from environment variables (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, etc.).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snowflake.snowpark import Session
from snowflake.snowpark.functions import udf, sproc
from snowflake.snowpark.types import (
    FloatType, IntegerType, StringType, ArrayType, VectorType,
)


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------
def get_session() -> Session:
    import os
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


# ---------------------------------------------------------------------------
# UDFs
# ---------------------------------------------------------------------------
def register_cosine_distance(session: Session) -> None:
    """Cosine distance between two 1024-dim VECTOR(FLOAT, 1024) values."""

    def cosine_distance(a: list, b: list) -> float:
        # Snowpark passes VECTOR as list of floats
        if a is None or b is None or len(a) == 0 or len(b) == 0:
            return None
        dot = 0.0
        na = 0.0
        nb = 0.0
        for x, y in zip(a, b):
            dot += x * y
            na += x * x
            nb += y * y
        if na == 0 or nb == 0:
            return None
        cos_sim = dot / ((na ** 0.5) * (nb ** 0.5))
        # Clamp for floating-point edge cases
        cos_sim = max(-1.0, min(1.0, cos_sim))
        return 1.0 - cos_sim

    session.udf.register(
        cosine_distance,
        name="NUANCE_DB.OUTPUTS.COSINE_DISTANCE",
        replace=True,
        input_types=[VectorType(float, 1024), VectorType(float, 1024)],
        return_type=FloatType(),
        is_permanent=True,
        stage_location="@NUANCE_DB.INTERNAL.UDF_STAGE",
        packages=[],
    )
    print("[OK]Registered NUANCE_DB.OUTPUTS.COSINE_DISTANCE")


def register_vector_avg(session: Session) -> None:
    """UDAF: average a column of VECTOR(FLOAT, 1024) into a single vector."""

    # Snowflake Snowpark supports Python UDAFs via a class with handler methods.
    from snowflake.snowpark.types import VectorType

    class VectorAvg:
        def __init__(self):
            self._sum = [0.0] * 1024
            self._n = 0

        @property
        def aggregate_state(self):
            return (self._sum, self._n)

        @aggregate_state.setter
        def aggregate_state(self, state):
            # Required by Snowpark Python UDAFs: Snowflake serializes the state
            # across distributed executors and rehydrates it via this setter.
            s, n = state
            self._sum = list(s)
            self._n = int(n)

        def accumulate(self, v):
            if v is None:
                return
            # Length guard: silently skip rows whose dimensions don't match.
            if len(v) != 1024:
                return
            for i in range(1024):
                self._sum[i] += float(v[i])
            self._n += 1

        def merge(self, other_state):
            s, n = other_state
            for i in range(1024):
                self._sum[i] += s[i]
            self._n += n

        def finish(self):
            if self._n == 0:
                return None
            return [s / self._n for s in self._sum]

    # Snowflake Python UDAFs do not support VECTOR type — use ARRAY instead.
    # Callers must cast: embedding::ARRAY going in, result::VECTOR(FLOAT,1024) coming out.
    session.udaf.register(
        VectorAvg,
        name="NUANCE_DB.OUTPUTS.VECTOR_AVG",
        replace=True,
        is_permanent=True,
        stage_location="@NUANCE_DB.INTERNAL.UDF_STAGE",
        input_types=[ArrayType(FloatType())],
        return_type=ArrayType(FloatType()),
        packages=[],
    )
    print("[OK]Registered NUANCE_DB.OUTPUTS.VECTOR_AVG")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["cosine", "avg"], default=None,
                        help="Optional: deploy only a single UDF/UDAF.")
    args = parser.parse_args()

    session = get_session()

    # Ensure stage exists
    session.sql(
        "CREATE STAGE IF NOT EXISTS NUANCE_DB.INTERNAL.UDF_STAGE"
    ).collect()

    try:
        if args.only in (None, "cosine"):
            register_cosine_distance(session)
        if args.only in (None, "avg"):
            register_vector_avg(session)
        print("\nAll Snowpark UDFs deployed.")
        return 0
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
