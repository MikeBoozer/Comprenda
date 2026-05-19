"""
Download a HuggingFace multilingual dataset and shape it into Nuance's
raw_data.social_posts schema.

Default dataset: cardiffnlp/tweet_sentiment_multilingual — 8 languages,
sentiment-labeled.

Usage:
    python data/download_huggingface.py
    python data/download_huggingface.py --dataset cardiffnlp/tweet_sentiment_multilingual
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print(
        "ERROR: the 'datasets' library is required.\n"
        "       pip install datasets",
        file=sys.stderr,
    )
    sys.exit(1)


def stable_id(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="cardiffnlp/tweet_sentiment_multilingual")
    parser.add_argument("--config", default="all",
                        help="Dataset config (subset). 'all' = every language.")
    parser.add_argument("--split", default="train+validation+test")
    parser.add_argument("--event_tag", default="hf_tweets_multilingual")
    parser.add_argument("--out", default="data/nuance_hf.csv")
    parser.add_argument("--limit", type=int, default=50000)
    args = parser.parse_args()

    print(f"Loading {args.dataset} [{args.config}] {args.split}...")
    ds = load_dataset(args.dataset, args.config, split=args.split)
    if args.limit and len(ds) > args.limit:
        ds = ds.shuffle(seed=42).select(range(args.limit))
    print(f"  Loaded {len(ds):,} rows.")

    # Column mapping: text, language code, label.
    # cardiffnlp dataset has: text (str), label (int), lang (str). Check first row.
    sample = ds[0]
    print(f"  Sample columns: {list(sample.keys())}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "post_id", "post_text", "detected_language", "source_platform",
            "source_url", "author_handle", "post_timestamp", "event_tag",
            "country_hint",
        ])
        w.writeheader()
        for i, row in enumerate(ds):
            text = (row.get("text") or "").strip()
            lang = (row.get("lang") or row.get("language") or "en").lower()[:2]
            if not text:
                continue
            w.writerow({
                "post_id": stable_id(args.dataset, str(i)),
                "post_text": text,
                "detected_language": lang,
                "source_platform": "twitter",
                "source_url": "",
                "author_handle": f"hf_user_{i % 10000}",
                "post_timestamp": "2026-01-01T00:00:00",
                "event_tag": args.event_tag,
                "country_hint": lang.upper(),
            })
            rows_written += 1

    print(f"[OK]Wrote {rows_written:,} rows to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
