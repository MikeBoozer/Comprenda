"""
Deploys the Cultural Translator stored procedure to Snowflake.

Run after `deploy.py`:
    python snowpark/deploy_translator.py

Given source content + target market, produces 2-3 culturally-adapted
variants that preserve intent but shift the cultural frame.
"""
from __future__ import annotations

import json
import sys
import uuid
from typing import Optional

from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, VariantType

from deploy import get_session


def translate_culture(
    session: Session,
    source_content: str,
    source_language: str,
    target_market: str,
    target_frame_hint: Optional[str] = None,
    requested_by: Optional[str] = None,
) -> dict:
    """Adapt content culturally for target_market.

    target_frame_hint: Optional override of the target frame (e.g. 'collectivist').
    If absent, we pick the most common dominant frame for the target market
    from the enriched corpus.
    """
    PROMPT_VERSION = "translator-v1"

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM NUANCE_DB.INTERNAL.CONFIG"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")

    # 1. Determine target frame (if not provided).
    if not target_frame_hint:
        row = session.sql(
            "SELECT cultural_frame, COUNT(*) AS n "
            "FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
            "WHERE detected_language = ? "
            "  AND cultural_frame != 'ambiguous' "
            "GROUP BY cultural_frame ORDER BY n DESC LIMIT 1",
            params=[target_market],
        ).collect()
        target_frame_hint = row[0]["CULTURAL_FRAME"] if row else "pragmatic"

    # 2. LLM call (bind via params — do NOT string-interpolate).
    prompt = (
        "You are a cross-cultural content adaptation specialist. Given source "
        "marketing content, produce 3 culturally-adapted variants for the target "
        "market that preserve INTENT but shift the cultural FRAME appropriately.\n\n"
        f"SOURCE LANGUAGE: {source_language}\n"
        f"TARGET MARKET LANGUAGE: {target_market}\n"
        f"TARGET DOMINANT FRAME: {target_frame_hint}\n\n"
        "SOURCE CONTENT:\n"
        f"\"\"\"\n{source_content[:2000]}\n\"\"\"\n\n"
        "Produce 3 variants. Each should be WRITTEN IN THE TARGET MARKET LANGUAGE, "
        "be the same approximate length as the source, and preserve the underlying "
        "marketing intent. Vary the frame approach across the 3 variants.\n\n"
        "Return JSON ONLY with no other text:\n"
        "{\"variants\":["
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"},"
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"},"
        "{\"text\":\"...\",\"frame_shift\":\"<frame_name>\",\"rationale\":\"<one sentence>\"}"
        "]}"
    )

    raw_rows = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
        params=[model_large, prompt],
    ).collect()
    raw = raw_rows[0]["R"] if raw_rows else ""

    variants = []
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0]
        parsed = json.loads(cleaned)
        variants = parsed.get("variants", []) if isinstance(parsed, dict) else []
    except Exception:
        # Last resort: return the raw text as one variant
        variants = [{
            "text": raw,
            "frame_shift": target_frame_hint or "unknown",
            "rationale": "Auto-fallback: model output did not parse as JSON.",
        }]

    # Persist.
    run_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO NUANCE_DB.OUTPUTS.CULTURAL_TRANSLATOR_RUNS ("
        "  run_id, requested_by, source_content, source_language, target_market,"
        "  target_frame_hint, adapted_variants, model_used, prompt_version"
        ") SELECT ?,?,?,?,?,?,PARSE_JSON(?),?,?",
        params=[
            run_id, requested_by, source_content, source_language, target_market,
            target_frame_hint, json.dumps(variants), model_large, PROMPT_VERSION,
        ],
    ).collect()

    return {
        "run_id": run_id,
        "source_content": source_content,
        "target_market": target_market,
        "target_frame_hint": target_frame_hint,
        "variants": variants,
        "model": model_large,
    }


def main() -> int:
    session = get_session()
    try:
        session.sql(
            "CREATE STAGE IF NOT EXISTS NUANCE_DB.INTERNAL.SPROC_STAGE"
        ).collect()

        session.sproc.register(
            func=translate_culture,
            name="NUANCE_DB.OUTPUTS.TRANSLATE_CULTURE",
            replace=True,
            is_permanent=True,
            stage_location="@NUANCE_DB.INTERNAL.SPROC_STAGE",
            packages=["snowflake-snowpark-python"],
            input_types=[StringType(), StringType(), StringType(), StringType(), StringType()],
            return_type=VariantType(),
        )
        print("[OK]Deployed NUANCE_DB.OUTPUTS.TRANSLATE_CULTURE")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
