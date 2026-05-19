"""
Deploys the Analog Retrieval stored procedure to Snowflake.

Run after `deploy.py`:
    python snowpark/deploy_analog_retrieval.py

Given a query (content or current event_tag), retrieves the 5 most similar
historical analog cases from library.analog_corpus.
"""
from __future__ import annotations

import json
import sys
from typing import Optional

from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, VariantType

from deploy import get_session


def find_analogs(
    session: Session,
    query_text: str,
    target_market: Optional[str] = None,
    k: int = 5,
) -> dict:
    """Return k nearest historical analog cases for a query."""

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM NUANCE_DB.INTERNAL.CONFIG"
        ).collect()
    }
    embedding_model = cfg.get("embedding_model", "snowflake-arctic-embed-l-v2.0")

    # Use Cortex Search if available (preferred — hybrid lexical+semantic).
    analogs = []
    try:
        search_query = {
            "query": query_text[:1000],
            "columns": [
                "analog_id", "case_name", "company", "year",
                "description", "affected_markets", "failure_frames",
                "outcome_summary",
            ],
            "limit": k,
        }
        if target_market:
            # Optional filter by affected_markets (array contains target_market)
            search_query["filter"] = {
                "@contains": {"affected_markets": target_market}
            }
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW("
            "'NUANCE_DB.LIBRARY.NUANCE_ANALOG_SEARCH', ?) AS r",
            params=[json.dumps(search_query)],
        ).collect()
        parsed = json.loads(result[0]["R"]) if result else {}
        analogs = parsed.get("results", []) if isinstance(parsed, dict) else []
    except Exception:
        # Fallback: direct cosine against analog_corpus embeddings.
        rows = session.sql(
            "WITH q AS (SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?) AS e) "
            "SELECT analog_id, case_name, company, year, description, "
            "       affected_markets, failure_frames, outcome_summary, "
            "       NUANCE_DB.OUTPUTS.COSINE_DISTANCE(embedding, (SELECT e FROM q)) AS dist "
            "FROM NUANCE_DB.LIBRARY.ANALOG_CORPUS "
            "ORDER BY dist ASC LIMIT ?",
            params=[embedding_model, query_text[:8000], k],
        ).collect()
        analogs = [
            {
                "analog_id": r["ANALOG_ID"],
                "case_name": r["CASE_NAME"],
                "company": r["COMPANY"],
                "year": r["YEAR"],
                "description": r["DESCRIPTION"],
                "affected_markets": r["AFFECTED_MARKETS"],
                "failure_frames": r["FAILURE_FRAMES"],
                "outcome_summary": r["OUTCOME_SUMMARY"],
                "distance": float(r["DIST"]) if r["DIST"] is not None else None,
            }
            for r in rows
        ]

    return {
        "query": query_text,
        "target_market": target_market,
        "analogs": analogs,
        "count": len(analogs),
    }


def main() -> int:
    session = get_session()
    try:
        session.sql(
            "CREATE STAGE IF NOT EXISTS NUANCE_DB.INTERNAL.SPROC_STAGE"
        ).collect()

        from snowflake.snowpark.types import IntegerType
        session.sproc.register(
            func=find_analogs,
            name="NUANCE_DB.OUTPUTS.FIND_ANALOGS",
            replace=True,
            is_permanent=True,
            stage_location="@NUANCE_DB.INTERNAL.SPROC_STAGE",
            packages=["snowflake-snowpark-python"],
            input_types=[StringType(), StringType(), IntegerType()],
            return_type=VariantType(),
        )
        print("[OK]Deployed NUANCE_DB.OUTPUTS.FIND_ANALOGS")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
