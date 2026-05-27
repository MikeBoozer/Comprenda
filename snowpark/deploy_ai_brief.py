"""
Deploys the AI Cultural Brief Generator stored procedure to Snowflake.

Run after `deploy.py`:
    python snowpark/deploy_ai_brief.py
"""
from __future__ import annotations

import json
import sys
import uuid
from typing import List, Optional

from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, VariantType

from deploy import get_session


BRIEF_PROMPT_VERSION = "ai-brief-v2"


def generate_brief(
    session: Session,
    event_tag: str,
    target_languages,
    requested_by: Optional[str] = None,
) -> dict:
    """Synthesize a 2-page cultural intelligence brief for an event_tag.

    target_languages may arrive as a Python list (in-process call) or as a
    JSON string (when called via SQL CALL with a VARIANT-typed arg).
    """
    # Normalize target_languages.
    if isinstance(target_languages, str):
        try:
            target_languages = json.loads(target_languages)
        except Exception:
            target_languages = [target_languages]
    if not isinstance(target_languages, list):
        target_languages = list(target_languages or [])

    cfg = {
        r["CONFIG_KEY"]: r["CONFIG_VALUE"]
        for r in session.sql(
            "SELECT config_key, config_value FROM NUANCE_DB.INTERNAL.CONFIG"
        ).collect()
    }
    model_large = cfg.get("model_large", "claude-4-sonnet")

    if not target_languages:
        # Default: all languages with ≥10 posts for this event
        rows = session.sql(
            "SELECT detected_language FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
            "WHERE event_tag = ? "
            "GROUP BY detected_language HAVING COUNT(*) >= 10",
            params=[event_tag],
        ).collect()
        target_languages = [r["DETECTED_LANGUAGE"] for r in rows]

    if not target_languages:
        raise ValueError(f"No language has ≥10 posts for event_tag={event_tag}")

    # 1. Multi-axis divergence profile for this event (latest computed batch).
    cds_rows = session.sql(
        "SELECT language_a, language_b, frame_divergence, sentiment_divergence, "
        "       topical_overlap, situation_label, cds_confidence "
        "FROM NUANCE_DB.OUTPUTS.CULTURAL_DIVERGENCE_SCORES "
        "WHERE event_tag = ? AND frame_divergence IS NOT NULL "
        "  AND (language_a IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "       OR language_b IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?))))) "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY language_a, language_b "
        "                           ORDER BY computed_at DESC) = 1 "
        "ORDER BY frame_divergence DESC",
        params=[event_tag, json.dumps(target_languages), json.dumps(target_languages)],
    ).collect()
    cds_summary = [
        {
            "lang_a": r["LANGUAGE_A"], "lang_b": r["LANGUAGE_B"],
            "situation": r["SITUATION_LABEL"],
            "frame_divergence": round(float(r["FRAME_DIVERGENCE"]), 3),
            "sentiment_divergence": round(float(r["SENTIMENT_DIVERGENCE"]), 3),
            "topical_overlap": round(float(r["TOPICAL_OVERLAP"]), 3),
            "confidence": round(float(r["CDS_CONFIDENCE"]), 2),
        }
        for r in cds_rows[:15]
    ]

    # 2. Frame distribution per language.
    frame_rows = session.sql(
        "SELECT detected_language, cultural_frame, COUNT(*) AS n "
        "FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "GROUP BY detected_language, cultural_frame "
        "ORDER BY detected_language, n DESC",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()

    frames_by_lang = {}
    for r in frame_rows:
        frames_by_lang.setdefault(r["DETECTED_LANGUAGE"], []).append({
            "frame": r["CULTURAL_FRAME"], "count": int(r["N"])
        })

    # 3. Sentiment per language.
    sent_rows = session.sql(
        "SELECT detected_language, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
        "FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "GROUP BY detected_language",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()
    sentiment_by_lang = {
        r["DETECTED_LANGUAGE"]: {
            "avg_sentiment": round(float(r["AVG_SENT"]), 3),
            "n": int(r["N"]),
        }
        for r in sent_rows
    }

    # 4. Sample top post IDs for citation
    sample_rows = session.sql(
        "SELECT post_id, detected_language FROM NUANCE_DB.ENRICHED.CULTURAL_FRAMES "
        "WHERE event_tag = ? "
        "  AND detected_language IN (SELECT value::STRING FROM TABLE(FLATTEN(input => PARSE_JSON(?)))) "
        "  AND frame_confidence > 0.7 "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY detected_language ORDER BY frame_confidence DESC) <= 3",
        params=[event_tag, json.dumps(target_languages)],
    ).collect()
    sample_post_ids = [r["POST_ID"] for r in sample_rows]

    # 5. Synthesis prompt.
    summary_payload = json.dumps({
        "event_tag": event_tag,
        "target_languages": target_languages,
        "cds_top_pairs": cds_summary,
        "frames_by_language": frames_by_lang,
        "sentiment_by_language": sentiment_by_lang,
    }, indent=2).replace("'", "''")

    prompt = (
        "You are a senior cultural intelligence analyst writing a 2-page Cultural "
        "Intelligence Brief for a marketing executive. The data below summarizes how "
        f"the event \"{event_tag}\" was discussed across language communities.\n\n"
        f"DATA:\n{summary_payload}\n\n"
        "Divergence is measured on three axes per language pair: topical_overlap "
        "(how much they discuss the same thing — high across the board), "
        "frame_divergence (how differently they frame it — the headline signal), and "
        "sentiment_divergence (how differently they feel). 'situation' summarizes the "
        "pair: Aligned / Divergent / 'Shared lens, split mood' / "
        "'Same verdict, different reasons'.\n\n"
        "Write the brief in Markdown with exactly these sections:\n"
        "1. **Executive Summary** (2-3 sentences)\n"
        "2. **Key Cultural Divergences** (table: language pair, situation, frame "
        "divergence, sentiment divergence, interpretation). Topical overlap is high "
        "everywhere — focus on how framing and sentiment differ, not whether they "
        "discuss the same event.\n"
        "3. **Dominant Frames by Region** (one line per language)\n"
        "4. **Risk Flags** (3-5 bullet points of specific cultural risks)\n"
        "5. **Messaging Recommendations** (one paragraph per target language)\n"
        "6. **Confidence Notes** (one short paragraph on sample size and certainty)\n\n"
        "Be specific. Quote concrete frame combinations. Do not hedge excessively."
    )

    raw_rows = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS r",
        params=[model_large, prompt],
    ).collect()
    brief_md = raw_rows[0]["R"] if raw_rows else "(no content)"

    # Persist.
    brief_id = str(uuid.uuid4())
    session.sql(
        "INSERT INTO NUANCE_DB.OUTPUTS.AI_BRIEFS ("
        "  brief_id, requested_by, event_tag, target_languages,"
        "  brief_markdown, source_post_ids, model_used, prompt_version"
        ") SELECT ?,?,?,PARSE_JSON(?),?,PARSE_JSON(?),?,?",
        params=[
            brief_id, requested_by, event_tag, json.dumps(target_languages),
            brief_md, json.dumps(sample_post_ids), model_large, BRIEF_PROMPT_VERSION,
        ],
    ).collect()

    return {
        "brief_id": brief_id,
        "event_tag": event_tag,
        "target_languages": target_languages,
        "brief_markdown": brief_md,
        "source_post_ids": sample_post_ids,
        "model": model_large,
    }


def main() -> int:
    session = get_session()
    try:
        session.sql(
            "CREATE STAGE IF NOT EXISTS NUANCE_DB.INTERNAL.SPROC_STAGE"
        ).collect()

        session.sproc.register(
            func=generate_brief,
            name="NUANCE_DB.OUTPUTS.GENERATE_BRIEF",
            replace=True,
            is_permanent=True,
            stage_location="@NUANCE_DB.INTERNAL.SPROC_STAGE",
            packages=["snowflake-snowpark-python"],
            # target_languages passed as VARIANT (JSON-encoded list); the
            # procedure parses it back into a Python list. This avoids
            # implicit ARRAY casts that vary between Snowpark versions.
            input_types=[StringType(), VariantType(), StringType()],
            return_type=VariantType(),
        )
        print("[OK]Deployed NUANCE_DB.OUTPUTS.GENERATE_BRIEF")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
