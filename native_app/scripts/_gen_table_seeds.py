"""
Generate native_app/scripts/seed_package_data.sql — the Native App's bundled demo
corpus, shipped as DATA CONTENT in the application PACKAGE.

Why this exists
---------------
A native-app setup script has no warehouse, and a package's `/data` files are not a
queryable stage, so `COPY INTO` cannot load bundled Parquet at install time. The
robust, canonical fix is native-app *data content*: real tables populated in the
application package (provider-side), shared into the installed app via versioned
proxy views. This script emits the provider-side populate step, run as a
`snow app deploy` post-deploy hook (entities.pkg.meta.post_deploy in snowflake.yml).

What it emits
-------------
`seed_package_data.sql`, an idempotent script that, against the application package:
  * CREATE SCHEMA comprenda_pkg.shared_data
  * CREATE TABLE + TRUNCATE + batched INSERT for the four reference tables
  * GRANT … TO SHARE IN APPLICATION PACKAGE comprenda_pkg
Everything is fully qualified with the package name so it runs regardless of the
hook's current-database context.

Sources
-------
  * native_app/data/{social_posts,cultural_frames,cultural_divergence_scores}.parquet
    (exported from the dev account; local file reads — no Snowflake network here)
  * data/seed_analog_library.py  (ANALOG_CASES — same source as _gen_analog_seed.py)

post_timestamp note (deliberate)
--------------------------------
The dev source column NUANCE_DB.RAW_DATA.SOCIAL_POSTS.post_timestamp is corrupt —
its stored values are out of range and Snowflake itself cannot render them
("seconds_since_epoch=… is not recognized"), so the Parquet copy is garbage too.
For the bundled demo we SYNTHESIZE deterministic, plausible post timestamps spread
across the ~60 days before ingestion (hash of post_id → offset). Every other column
is passed through verbatim. Synthesizing readable timestamps is higher quality for a
demo than shipping unrenderable ones, and it is fully reproducible.

Re-run after refreshing the Parquet or the analog list:
    python native_app/scripts/_gen_table_seeds.py

Provenance only — this generator is NOT shipped in the app package (excluded by
snowflake.yml's explicit allow-list). The generated .sql is a provider-side hook,
also not shipped to consumers.
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                       # repo root
DATA = HERE.parent / "data"                  # native_app/data
ANALOG_SRC = ROOT / "data" / "seed_analog_library.py"
OUT = HERE / "seed_package_data.sql"

PKG = "comprenda_pkg"                         # snowflake.yml entities.pkg.identifier
SCHEMA = f"{PKG}.shared_data"
BATCH = 200                                   # rows per INSERT (well under stmt-size limits)

# Synthesized post_timestamp window: [BASE - WINDOW, BASE].
_TS_BASE = dt.datetime(2026, 5, 29, 0, 0, 0)
_TS_WINDOW_SECONDS = 60 * 24 * 3600


# --------------------------------------------------------------------------- #
# Literal rendering
# --------------------------------------------------------------------------- #
def _str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def _num(v) -> str:
    if v is None or pd.isna(v):
        return "NULL"
    return repr(float(v))


def _int(v) -> str:
    if v is None or pd.isna(v):
        return "NULL"
    return str(int(v))


def _ts(v) -> str:
    if v is None or pd.isna(v):
        return "NULL"
    ts = pd.Timestamp(v).to_pydatetime()
    return "'" + ts.strftime("%Y-%m-%d %H:%M:%S.%f") + "'::TIMESTAMP_NTZ"


def _synth_ts(post_id: str) -> str:
    h = int(hashlib.md5(str(post_id).encode("utf-8")).hexdigest()[:12], 16)
    moment = _TS_BASE - dt.timedelta(seconds=h % _TS_WINDOW_SECONDS)
    return "'" + moment.strftime("%Y-%m-%d %H:%M:%S.%f") + "'::TIMESTAMP_NTZ"


# Per-table spec: (column_name, renderer). "post_timestamp" uses the synth renderer
# keyed off the row's post_id (handled specially in _render_row).
SOCIAL_POSTS = [
    ("post_id", _str), ("post_text", _str), ("detected_language", _str),
    ("source_platform", _str), ("post_timestamp", "synth"), ("event_tag", _str),
    ("country_hint", _str), ("ingested_at", _ts),
]
CULTURAL_FRAMES = [
    ("post_id", _str), ("post_text", _str), ("detected_language", _str),
    ("event_tag", _str), ("cultural_frame", _str), ("frame_confidence", _num),
    ("sentiment_score", _num), ("emotional_tone", _str), ("model_used", _str),
    ("prompt_version", _str), ("inference_timestamp", _ts),
]
CDS = [
    ("cds_id", _str), ("event_tag", _str), ("language_a", _str), ("language_b", _str),
    ("posts_lang_a", _int), ("posts_lang_b", _int), ("cds_score", _num),
    ("cds_confidence", _num), ("topical_overlap", _num), ("frame_divergence", _num),
    ("sentiment_divergence", _num), ("headline_score", _num), ("situation_label", _str),
    ("computed_at", _ts),
]

DDL = {
    "social_posts": """CREATE TABLE IF NOT EXISTS {schema}.social_posts (
    post_id           VARCHAR,
    post_text         VARCHAR,
    detected_language VARCHAR(8),
    source_platform   VARCHAR,
    post_timestamp    TIMESTAMP_NTZ,
    event_tag         VARCHAR,
    country_hint      VARCHAR(8),
    ingested_at       TIMESTAMP_NTZ
);""",
    "cultural_frames": """CREATE TABLE IF NOT EXISTS {schema}.cultural_frames (
    post_id             VARCHAR,
    post_text           VARCHAR,
    detected_language   VARCHAR(8),
    event_tag           VARCHAR,
    cultural_frame      VARCHAR,
    frame_confidence    FLOAT,
    sentiment_score     FLOAT,
    emotional_tone      VARCHAR,
    model_used          VARCHAR,
    prompt_version      VARCHAR,
    inference_timestamp TIMESTAMP_NTZ
);""",
    "cultural_divergence_scores": """CREATE TABLE IF NOT EXISTS {schema}.cultural_divergence_scores (
    cds_id               VARCHAR,
    event_tag            VARCHAR,
    language_a           VARCHAR(8),
    language_b           VARCHAR(8),
    posts_lang_a         INTEGER,
    posts_lang_b         INTEGER,
    cds_score            FLOAT,
    cds_confidence       FLOAT,
    topical_overlap      FLOAT,
    frame_divergence     FLOAT,
    sentiment_divergence FLOAT,
    headline_score       FLOAT,
    situation_label      VARCHAR,
    computed_at          TIMESTAMP_NTZ
);""",
    "analog_corpus": """CREATE TABLE IF NOT EXISTS {schema}.analog_corpus (
    analog_id        VARCHAR,
    case_name        VARCHAR,
    company          VARCHAR,
    year             INTEGER,
    description      VARCHAR,
    affected_markets ARRAY,
    failure_frames   ARRAY,
    outcome_summary  VARCHAR,
    source_url       VARCHAR
);""",
}


def _render_row(rec: dict, spec) -> str:
    cells = []
    for col, renderer in spec:
        if renderer == "synth":
            cells.append(_synth_ts(rec["post_id"]))
        else:
            cells.append(renderer(rec.get(col)))
    return "(" + ", ".join(cells) + ")"


def _emit_scalar_table(name: str, df: pd.DataFrame, spec) -> list[str]:
    """INSERT … VALUES batches for a table with only scalar columns."""
    cols = ", ".join(c for c, _ in spec)
    # NaN -> None so the renderers see real None.
    records = df.where(pd.notnull(df), None).to_dict("records")
    lines = [f"TRUNCATE TABLE {SCHEMA}.{name};", ""]
    for start in range(0, len(records), BATCH):
        chunk = records[start:start + BATCH]
        rows = ",\n".join("    " + _render_row(r, spec) for r in chunk)
        lines.append(f"INSERT INTO {SCHEMA}.{name} ({cols})\nVALUES\n{rows};")
        lines.append("")
    return lines


def _emit_analog_table() -> list[str]:
    """analog_corpus has ARRAY columns -> SELECT … PARSE_JSON(…) FROM VALUES."""
    tree = ast.parse(ANALOG_SRC.read_text(encoding="utf-8"))
    cases = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "ANALOG_CASES" for t in node.targets
        ):
            cases = ast.literal_eval(node.value)
            break
    if cases is None:
        raise SystemExit("ANALOG_CASES not found in seed_analog_library.py")

    cols = ("analog_id, case_name, company, year, description, "
            "affected_markets, failure_frames, outcome_summary, source_url")
    lines = [f"TRUNCATE TABLE {SCHEMA}.analog_corpus;", "",
             f"INSERT INTO {SCHEMA}.analog_corpus\n    ({cols})",
             "SELECT column1, column2, column3, column4, column5,",
             "       PARSE_JSON(column6), PARSE_JSON(column7), column8, column9",
             "FROM VALUES"]
    rows = []
    for i, c in enumerate(cases, 1):
        rows.append("    (" + ", ".join([
            _str(f"analog_{i:03d}"), _str(c["case_name"]), _str(c["company"]),
            str(int(c["year"])), _str(c["description"]),
            _str(json.dumps(list(c["affected_markets"]))),
            _str(json.dumps(list(c["failure_frames"]))),
            _str(c["outcome_summary"]), _str(c["source_url"]),
        ]) + ")")
    lines.append(",\n".join(rows) + ";")
    lines.append("")
    return lines, len(cases)


def main() -> None:
    sp = pd.read_parquet(DATA / "social_posts.parquet")
    cf = pd.read_parquet(DATA / "cultural_frames.parquet")
    cds = pd.read_parquet(DATA / "cultural_divergence_scores.parquet")
    # Normalize column names to lower-case so the spec lookups match.
    for d in (sp, cf, cds):
        d.columns = [c.lower() for c in d.columns]

    out = [
        "-- =============================================================================",
        "-- Comprenda Native App — bundled demo corpus (GENERATED — do not edit by hand)",
        "-- =============================================================================",
        "-- Provider-side data content for the application package. Run as a",
        "-- snow app deploy post-deploy hook (snowflake.yml entities.pkg.meta.post_deploy).",
        "-- Populates comprenda_pkg.shared_data.* and shares it into installed apps.",
        "-- Regenerate: python native_app/scripts/_gen_table_seeds.py",
        "-- Idempotent: CREATE … IF NOT EXISTS + TRUNCATE + INSERT + (re)GRANT.",
        "-- post_timestamp is synthesized (dev source column is corrupt); see generator.",
        "-- =============================================================================",
        "",
        f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};",
        "",
    ]
    for name, df, spec in [
        ("social_posts", sp, SOCIAL_POSTS),
        ("cultural_frames", cf, CULTURAL_FRAMES),
        ("cultural_divergence_scores", cds, CDS),
    ]:
        out.append("-- " + "-" * 73)
        out.append(f"-- {name}  ({len(df)} rows)")
        out.append("-- " + "-" * 73)
        out.append(DDL[name].format(schema=SCHEMA))
        out.append("")
        out.extend(_emit_scalar_table(name, df, spec))

    analog_lines, n_analog = _emit_analog_table()
    out.append("-- " + "-" * 73)
    out.append(f"-- analog_corpus  ({n_analog} curated cases; no embeddings)")
    out.append("-- " + "-" * 73)
    out.append(DDL["analog_corpus"].format(schema=SCHEMA))
    out.append("")
    out.extend(analog_lines)

    out += [
        "-- " + "-" * 73,
        "-- Share the reference corpus into installed apps. The setup script exposes",
        "-- these via versioned proxy views (app_instance.src_*).",
        "-- " + "-" * 73,
        f"GRANT USAGE ON SCHEMA {SCHEMA} TO SHARE IN APPLICATION PACKAGE {PKG};",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO SHARE IN APPLICATION PACKAGE {PKG};",
        "",
    ]

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"[OK] wrote {OUT}")
    print(f"     social_posts={len(sp)}  cultural_frames={len(cf)}  "
          f"cds={len(cds)}  analog={n_analog}")


if __name__ == "__main__":
    main()
