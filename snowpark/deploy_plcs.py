"""
Deploys the Pre-Launch Cultural Risk Score (PLCS) Snowflake stored procedure.

Run after `deploy.py`:
    python snowpark/deploy_plcs.py
"""
from __future__ import annotations

import json
import sys
import uuid
from typing import Optional

from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, VariantType

from deploy import get_session


# ---------------------------------------------------------------------------
# The handler — runs server-side in Snowflake.
# ---------------------------------------------------------------------------
def score_content(
    session: Session,
    draft_content: str,
    source_language: str,
    target_market: str,
    requested_by: Optional[str] = None,
) -> dict:
    """
    Pre-Launch Cultural Risk Score for a (content, market) pair.

    Returns dict with: plcs_id, plcs_score (0-100), confidence (0-1),
    top_frames (list[str]), nearest_analogs (list[post_id]), risk_narrative.
    """
    PROMPT_VERSION = "plcs-v1"

    # 1. Load runtime config (model names).
    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM NUANCE_DB.INTERNAL.CONFIG"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")
    embedding_model = cfg.get("embedding_model", "snowflake-arctic-embed-l-v2.0")

    truncated = (draft_content or "")[:8000]

    # 2. Cortex Search over enriched corpus filtered by target market language.
    #    Cortex Search hybrid (lexical + semantic) gives better recall than pure
    #    vector kNN for short marketing copy. Falls back to UDF-based cosine
    #    distance with a server-side embed (no Python→VECTOR binding!) if the
    #    search service isn't built yet.
    neighbors = []
    try:
        search_query = {
            "query": truncated[:1000],
            "columns": [
                "post_id", "post_text", "cultural_frame",
                "emotional_tone", "sentiment_score", "frame_confidence",
                "detected_language",
            ],
            "filter": {"@eq": {"detected_language": target_market}},
            "limit": 15,
        }
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW("
            "'NUANCE_DB.ENRICHED.NUANCE_POST_SEARCH', ?) AS r",
            params=[json.dumps(search_query)],
        ).collect()
        raw = result[0]["R"] if result else None
        parsed = json.loads(raw) if isinstance(raw, str) else (raw or {})
        neighbors = parsed.get("results", []) if isinstance(parsed, dict) else []
    except Exception:
        # Fallback: direct cosine via UDF.
        # CRITICAL: do NOT bind a Python list as a VECTOR parameter. Inline the
        # EMBED_TEXT_1024(?, ?) so the VECTOR is constructed server-side.
        rows = session.sql(
            "SELECT cf.post_id, cf.cultural_frame, cf.sentiment_score, "
            "       cf.emotional_tone, cf.frame_confidence, "
            "       NUANCE_DB.OUTPUTS.COSINE_DISTANCE("
            "           pe.embedding, "
            "           SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?)"
            "       ) AS dist "
            "FROM NUANCE_DB.ENRICHED.POST_EMBEDDINGS pe "
            "JOIN NUANCE_DB.ENRICHED.CULTURAL_FRAMES cf USING (post_id) "
            "WHERE cf.detected_language = ? "
            "ORDER BY dist ASC LIMIT 15",
            params=[embedding_model, truncated, target_market],
        ).collect()
        neighbors = [
            {
                "post_id": r["POST_ID"],
                "cultural_frame": r["CULTURAL_FRAME"],
                "sentiment_score": r["SENTIMENT_SCORE"],
                "emotional_tone": r["EMOTIONAL_TONE"],
                "frame_confidence": r["FRAME_CONFIDENCE"],
                "dist": r["DIST"],
            }
            for r in rows
        ]

    # 3. Aggregate neighbor signals.
    if not neighbors:
        plcs_score = 50
        plcs_confidence = 0.1
        top_frames = ["ambiguous"]
        nearest_post_ids = []
        risk_narrative = (
            "Insufficient historical data in target market to score with confidence. "
            "Recommend manual review by a market-native reviewer."
        )
    else:
        # Top 3 frames by frequency
        from collections import Counter
        frame_counts = Counter(
            (n.get("cultural_frame") or "ambiguous") for n in neighbors
        )
        top_frames = [f for f, _ in frame_counts.most_common(3)]
        nearest_post_ids = [n.get("post_id") for n in neighbors if n.get("post_id")]

        # Proportion of neighbors with negative sentiment
        def _safe_float(x, default=0.0):
            try:
                return float(x) if x is not None else default
            except (TypeError, ValueError):
                return default
        neg = sum(
            1 for n in neighbors
            if _safe_float(n.get("sentiment_score"), 0.0) < -0.2
        )
        pct_neg = round(100.0 * neg / len(neighbors))

        # LLM synthesis (bind via params — do NOT string-interpolate).
        synth_prompt = (
            "You are a cultural intelligence analyst evaluating cultural risk of a "
            f"marketing draft for the target market with language code \"{target_market}\".\n\n"
            f"DRAFT CONTENT (source language {source_language}):\n"
            f"\"\"\"\n{draft_content[:1500]}\n\"\"\"\n\n"
            f"HISTORICAL ANALOG DATA (top frames in {target_market} similar content): "
            f"{', '.join(top_frames)}.\n"
            f"Proportion of similar historical content with negative sentiment: {pct_neg}%.\n\n"
            "Score cultural risk on a 0-100 scale (higher = more risk). Consider:\n"
            "- Frame mismatch between draft intent and dominant frames in target market\n"
            "- Historical sentiment of similar content\n"
            "- Common cultural pitfalls (religion, history, in-group/out-group cues)\n\n"
            "Return JSON ONLY with no other text:\n"
            "{\"plcs\":<integer_0_100>,\"confidence\":<float_0_1>,"
            "\"narrative\":\"<one paragraph under 150 words explaining the score "
            "and citing which frames matter>\"}"
        )

        resp_rows = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
            params=[model_large, synth_prompt],
        ).collect()
        raw = resp_rows[0]["R"] if resp_rows else ""

        # Robust JSON extraction
        plcs_score = 50
        plcs_confidence = 0.5
        risk_narrative = raw
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
            plcs_score = int(parsed.get("plcs", 50))
            plcs_confidence = float(parsed.get("confidence", 0.5))
            risk_narrative = str(parsed.get("narrative", raw))
        except Exception:
            # Regex fallback
            import re
            m = re.search(r'"plcs"\s*:\s*(\d+)', raw)
            if m:
                plcs_score = int(m.group(1))
            m = re.search(r'"confidence"\s*:\s*([0-9.]+)', raw)
            if m:
                plcs_confidence = float(m.group(1))

        plcs_score = max(0, min(100, plcs_score))
        plcs_confidence = max(0.0, min(1.0, plcs_confidence))

    # 4. Persist.
    plcs_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO NUANCE_DB.OUTPUTS.PRE_LAUNCH_RISK_SCORES ("
        "  plcs_id, requested_by, draft_content, source_language, target_market,"
        "  plcs_score, plcs_confidence, top_frames, nearest_analogs,"
        "  risk_narrative, model_used, prompt_version, inputs_json"
        ") SELECT ?,?,?,?,?,?,?, PARSE_JSON(?), PARSE_JSON(?),?,?,?, PARSE_JSON(?)",
        params=[
            plcs_id, requested_by, draft_content, source_language, target_market,
            plcs_score, plcs_confidence,
            json.dumps(top_frames),
            json.dumps(nearest_post_ids),
            risk_narrative, model_large, PROMPT_VERSION,
            json.dumps({"source_language": source_language,
                        "target_market": target_market,
                        "n_neighbors": len(neighbors)}),
        ],
    ).collect()

    return {
        "plcs_id": plcs_id,
        "plcs_score": plcs_score,
        "confidence": plcs_confidence,
        "top_frames": top_frames,
        "nearest_analogs": nearest_post_ids,
        "risk_narrative": risk_narrative,
        "target_market": target_market,
        "model": model_large,
    }


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------
def main() -> int:
    session = get_session()
    try:
        session.sql(
            "CREATE STAGE IF NOT EXISTS NUANCE_DB.INTERNAL.SPROC_STAGE"
        ).collect()

        session.sproc.register(
            func=score_content,
            name="NUANCE_DB.OUTPUTS.SCORE_CONTENT",
            replace=True,
            is_permanent=True,
            stage_location="@NUANCE_DB.INTERNAL.SPROC_STAGE",
            packages=["snowflake-snowpark-python"],
            input_types=[StringType(), StringType(), StringType(), StringType()],
            return_type=VariantType(),
        )
        print("[OK] Deployed NUANCE_DB.OUTPUTS.SCORE_CONTENT")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
