"""
Generate native_app/scripts/seed_analog_corpus.sql from the curated analog cases
in data/seed_analog_library.py.

This keeps the Native App's bundled analog library deterministic and in sync with
the dev seeder, WITHOUT shipping embeddings (Cortex Search re-indexes from the
`description` text at install). Re-run after editing the case list:

    python native_app/scripts/_gen_analog_seed.py

Provenance only — not part of the app package (excluded by snowflake.yml's
explicit allow-list). The generated .sql IS bundled.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "seed_analog_library.py"
OUT = Path(__file__).resolve().parent / "seed_analog_corpus.sql"


def _extract_cases() -> list[dict]:
    """ast.literal_eval the ANALOG_CASES list literal (no imports/side effects)."""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "ANALOG_CASES" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise SystemExit("ANALOG_CASES not found in seed_analog_library.py")


def _sql_str(s: str) -> str:
    """Single-quoted SQL literal with embedded quotes doubled."""
    return "'" + str(s).replace("'", "''") + "'"


def _json_array(values) -> str:
    """PARSE_JSON('[...]') for an ARRAY column."""
    return "PARSE_JSON(" + _sql_str(json.dumps(list(values))) + ")"


def main() -> None:
    cases = _extract_cases()
    lines = [
        "-- =============================================================================",
        "-- Comprenda Native App — bundled analog corpus seed (GENERATED)",
        "-- =============================================================================",
        "-- Source of truth: data/seed_analog_library.py (ANALOG_CASES).",
        "-- Regenerate with: python native_app/scripts/_gen_analog_seed.py",
        "-- Embeddings are intentionally omitted; the analog Cortex Search service",
        "-- indexes the `description` text at install. Idempotent: clears + reseeds.",
        "-- =============================================================================",
        "",
        "DELETE FROM app_data.analog_corpus;",
        "",
        "INSERT INTO app_data.analog_corpus",
        "    (analog_id, case_name, company, year, description,",
        "     affected_markets, failure_frames, outcome_summary, source_url)",
        "SELECT column1, column2, column3, column4, column5,",
        "       PARSE_JSON(column6), PARSE_JSON(column7), column8, column9",
        "FROM VALUES",
    ]

    rows = []
    for i, c in enumerate(cases, 1):
        rows.append(
            "    ("
            + ", ".join(
                [
                    _sql_str(f"analog_{i:03d}"),
                    _sql_str(c["case_name"]),
                    _sql_str(c["company"]),
                    str(int(c["year"])),
                    _sql_str(c["description"]),
                    _sql_str(json.dumps(list(c["affected_markets"]))),
                    _sql_str(json.dumps(list(c["failure_frames"]))),
                    _sql_str(c["outcome_summary"]),
                    _sql_str(c["source_url"]),
                ]
            )
            + ")"
        )
    # VALUES rows are comma-separated; PARSE_JSON is applied in the SELECT above
    # (column6/column7 arrive as JSON strings).
    body = ",\n".join(rows) + ";\n"
    text = "\n".join(lines) + "\n" + body

    OUT.write_text(text, encoding="utf-8")
    print(f"[OK] wrote {OUT} ({len(cases)} cases)")


if __name__ == "__main__":
    main()
