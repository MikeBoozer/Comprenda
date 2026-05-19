"""
Download a slice of GDELT GKG (Global Knowledge Graph) multilingual news data
and shape it into Nuance's raw_data.social_posts schema.

GDELT is the world's largest open-source multilingual news event database,
covering 65+ languages, refreshed every 15 minutes, free.

Use this AFTER the synthetic demo to add real data to your pipeline.

Usage:
    python data/download_gdelt.py --days 7 --out data/nuance_gdelt.csv
    python data/download_gdelt.py --days 30 --languages ja,zh,de,es --event_keyword "iPhone"
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# GDELT GKG v2 master file list URL
GDELT_MASTER = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"


def fetch_master_list() -> list[str]:
    """Fetch the GDELT master file list (every 15-min batch URL)."""
    print("Fetching GDELT master file list...")
    with urllib.request.urlopen(GDELT_MASTER, timeout=60) as r:
        content = r.read().decode("utf-8")
    urls = []
    for line in content.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2].endswith(".gkg.csv.zip"):
            urls.append(parts[2])
    print(f"  Master list has {len(urls):,} GKG file URLs.")
    return urls


def filter_recent(urls: list[str], days: int) -> list[str]:
    """Filter master list to the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    keep = []
    for url in urls:
        # URL has YYYYMMDDHHMMSS in filename
        fname = url.rsplit("/", 1)[-1]
        try:
            ts = datetime.strptime(fname[:14], "%Y%m%d%H%M%S")
            if ts >= cutoff:
                keep.append(url)
        except ValueError:
            continue
    return keep


def download_and_parse(
    url: str,
    languages: set[str] | None,
    keyword: str | None,
    event_tag: str,
) -> list[dict]:
    """Download one GKG zip, parse rows that match filters."""
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
    except Exception as e:
        print(f"  ! skipping {url}: {e}")
        return []

    # GDELT GKG zips contain a single .csv with tab-separated values
    import zipfile
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    if not names:
        return []
    raw = z.read(names[0]).decode("utf-8", errors="replace")

    posts = []
    for line in raw.splitlines():
        cols = line.split("\t")
        if len(cols) < 30:
            continue
        gkg_id = cols[0]
        gkg_date = cols[1]
        source_lang = (cols[20] or "").lower()[:2]  # GKG.v2.1: SourceLanguage at idx ~20
        themes_field = cols[7] or ""
        v2tone = cols[15] or ""           # tone CSV — col 0 is overall tone
        source_url = cols[4] or ""
        # Document title is typically not in GKG; we use the first 240 chars of the
        # extracted SharingImage/DocumentIdentifier text as a proxy. GDELT's
        # GKG is article-metadata, not full text. Combine themes + tone + url.
        # For a richer corpus, hit GDELT DOC v2 with the GKG IDs.
        if languages and source_lang and source_lang not in languages:
            continue
        if keyword and keyword.lower() not in themes_field.lower() and keyword.lower() not in source_url.lower():
            continue
        # Build a synthetic post_text by combining themes (top 5) + the URL slug.
        themes = [t.split(",")[0] for t in themes_field.split(";")[:5] if t]
        post_text = (
            f"News themes: {', '.join(themes)}. Source: {source_url}"
        )
        try:
            ts = datetime.strptime(gkg_date[:14], "%Y%m%d%H%M%S").isoformat()
        except Exception:
            ts = gkg_date

        posts.append({
            "post_id": f"gkg_{gkg_id}",
            "post_text": post_text[:1500],
            "detected_language": source_lang or "en",
            "source_platform": "news",
            "source_url": source_url[:500],
            "author_handle": "gdelt",
            "post_timestamp": ts,
            "event_tag": event_tag,
            "country_hint": "",
        })
    return posts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=2,
                        help="How many days back to pull (default: 2).")
    parser.add_argument("--languages", default="en,ja,zh,de,es,fr,ko,pt,ar,hi,it,ru",
                        help="Comma-separated ISO 639-1 codes.")
    parser.add_argument("--event_keyword", default=None,
                        help="Filter to themes/URLs containing this keyword.")
    parser.add_argument("--event_tag", default="gdelt_news",
                        help="Event tag to assign to all imported rows.")
    parser.add_argument("--max_files", type=int, default=200,
                        help="Cap on number of 15-min batches to download.")
    parser.add_argument("--out", default="data/nuance_gdelt.csv")
    args = parser.parse_args()

    lang_set = {l.strip().lower() for l in args.languages.split(",")} if args.languages else None

    master = fetch_master_list()
    recent = filter_recent(master, args.days)
    recent = recent[: args.max_files]
    print(f"Pulling {len(recent)} batches...")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_total = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "post_id", "post_text", "detected_language", "source_platform",
            "source_url", "author_handle", "post_timestamp", "event_tag",
            "country_hint",
        ])
        w.writeheader()
        for i, url in enumerate(recent, 1):
            posts = download_and_parse(url, lang_set, args.event_keyword, args.event_tag)
            for p in posts:
                w.writerow(p)
            rows_total += len(posts)
            if i % 10 == 0:
                print(f"  {i}/{len(recent)} files, {rows_total:,} rows so far")
            time.sleep(0.1)  # be polite to GDELT

    print(f"[OK]Wrote {rows_total:,} rows to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
