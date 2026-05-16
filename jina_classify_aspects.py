#!/usr/bin/env python3
"""Aspect-Based Sentiment Analysis using Jina AI Classifier API.

Zero-shot aspect categorisation of reviews/posts into predefined aspect
categories matching the research independent variables.  Works with both
Google Play review TSVs and Reddit post TSVs.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Aspect labels matching research IVs ──────────────────────────────────────

ASPECT_LABELS = [
    "Delivery Speed and Timeliness",
    "Pricing and Charges",
    "Product Quality and Freshness",
    "Customer Service and Support",
    "Product Availability and Stock",
    "App Usability and Interface",
    "Refund and Payment Issues",
    "Location and Serviceability",
    "Offers and Promotions",
]

# ── Column detection helpers ─────────────────────────────────────────────────

TEXT_CANDIDATES = [
    "Review_Content",
    "content",
    "review",
    "comment",
    "text",
    "selftext",
    "title",
]

RATING_CANDIDATES = [
    "Rating",
    "score",
    "rating",
]

DATE_CANDIDATES = [
    "Date",
    "created_iso",
    "at",
    "date",
]

ID_CANDIDATES = [
    "Review_ID",
    "reviewId",
    "id",
    "name",
]


def _pick(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {c.lower(): c for c in columns}
    for name in candidates:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


# ── Jina AI Classifier API ──────────────────────────────────────────────────

JINA_CLASSIFY_URL = "https://api.jina.ai/v1/classify"
JINA_MODEL = "jina-embeddings-v3"

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def classify_batch(
    texts: list[str],
    api_key: str,
    labels: list[str] | None = None,
) -> list[dict]:
    """Send a batch of texts to Jina Classifier and return results."""

    if labels is None:
        labels = ASPECT_LABELS

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "model": JINA_MODEL,
        "input": [{"text": t[:256]} for t in texts],  # truncate to save tokens
        "labels": labels,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(JINA_CLASSIFY_URL, headers=headers, json=payload)

            if resp.status_code == 429:
                wait = RETRY_DELAY * attempt
                print(f"  Rate-limited, retrying in {wait}s (attempt {attempt})...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

        except httpx.HTTPStatusError as exc:
            print(f"  HTTP error {exc.response.status_code}: {exc.response.text[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            raise
        except httpx.RequestError as exc:
            print(f"  Request error: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            raise

    return []


def parse_classification(result: dict) -> tuple[str, float, str]:
    """Extract top aspect, confidence, and full predictions JSON."""

    predictions = result.get("predictions", [])
    if not predictions:
        return ("Unknown", 0.0, "[]")

    # predictions is a list of {label, score}
    top = max(predictions, key=lambda p: p.get("score", 0))
    top_label = top.get("label", "Unknown")
    top_score = float(top.get("score", 0.0))
    all_json = json.dumps(
        [{"label": p["label"], "score": round(p["score"], 4)} for p in predictions],
        ensure_ascii=False,
    )
    return (top_label, top_score, all_json)


# ── Main pipeline ───────────────────────────────────────────────────────────


def detect_delimiter(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def run_classification(
    input_path: Path,
    output_prefix: Path,
    api_key: str,
    batch_size: int,
    max_rows: int | None,
) -> None:
    delimiter = detect_delimiter(input_path)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    output_csv = output_prefix.with_suffix(".csv")
    output_tsv = output_prefix.with_suffix(".tsv")
    output_summary = output_prefix.with_name(f"{output_prefix.name}_summary.json")

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Input file has no header row")

        columns = list(reader.fieldnames)
        text_col = _pick(columns, TEXT_CANDIDATES)
        # For Reddit: combine title + selftext
        title_col = _pick(columns, ["title"])
        selftext_col = _pick(columns, ["selftext"])
        rating_col = _pick(columns, RATING_CANDIDATES)
        date_col = _pick(columns, DATE_CANDIDATES)
        id_col = _pick(columns, ID_CANDIDATES)

        if not text_col and not title_col:
            raise ValueError(
                f"Cannot find text column. Available: {columns}"
            )

        out_fields = columns + [
            "jina_aspect",
            "jina_aspect_confidence",
            "jina_all_aspects",
        ]

        # If there's already a sentiment_label column, add combined column
        has_sentiment = "sentiment_label" in columns
        if has_sentiment:
            out_fields.append("jina_aspect_sentiment")

        all_rows: list[dict] = []
        for row in reader:
            all_rows.append(row)
            if max_rows and len(all_rows) >= max_rows:
                break

    print(f"Loaded {len(all_rows)} rows from {input_path}")
    print(f"Text column: {text_col or f'{title_col}+{selftext_col}'}")

    # ── Build texts ──────────────────────────────────────────────────────
    texts: list[str] = []
    for row in all_rows:
        if text_col and text_col not in ("title", "selftext"):
            t = _normalize(row.get(text_col, ""))
        else:
            # Reddit-style: title + selftext
            parts = []
            if title_col:
                parts.append(_normalize(row.get(title_col, "")))
            if selftext_col:
                st = _normalize(row.get(selftext_col, ""))
                if st and st.lower() not in ("[removed]", "[deleted]", ""):
                    parts.append(st)
            t = " ".join(parts)
        texts.append(t)

    # ── Classify in batches ──────────────────────────────────────────────
    results: list[tuple[str, float, str]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    skipped = 0

    for i in range(0, len(texts), batch_size):
        batch_num = i // batch_size + 1
        batch_texts = texts[i : i + batch_size]

        # Skip empty texts
        valid_indices = [j for j, t in enumerate(batch_texts) if len(t) >= 3]
        if not valid_indices:
            for _ in batch_texts:
                results.append(("Unknown", 0.0, "[]"))
                skipped += 1
            print(f"  Batch {batch_num}/{total_batches}: skipped (empty texts)")
            continue

        valid_texts = [batch_texts[j] for j in valid_indices]

        print(f"  Batch {batch_num}/{total_batches}: classifying {len(valid_texts)} texts...")
        api_results = classify_batch(valid_texts, api_key)

        # Map results back
        api_idx = 0
        for j in range(len(batch_texts)):
            if j in valid_indices and api_idx < len(api_results):
                results.append(parse_classification(api_results[api_idx]))
                api_idx += 1
            else:
                results.append(("Unknown", 0.0, "[]"))
                skipped += 1

    # ── Write output ─────────────────────────────────────────────────────
    aspect_counts: dict[str, int] = {}
    aspect_sentiment: dict[str, dict[str, int]] = {}

    with output_csv.open("w", encoding="utf-8-sig", newline="") as csv_out, \
         output_tsv.open("w", encoding="utf-8-sig", newline="") as tsv_out:

        csv_writer = csv.DictWriter(csv_out, fieldnames=out_fields)
        tsv_writer = csv.DictWriter(tsv_out, fieldnames=out_fields, delimiter="\t")
        csv_writer.writeheader()
        tsv_writer.writeheader()

        for row, (aspect, confidence, all_aspects) in zip(all_rows, results):
            enriched = dict(row)
            enriched["jina_aspect"] = aspect
            enriched["jina_aspect_confidence"] = f"{confidence:.4f}"
            enriched["jina_all_aspects"] = all_aspects

            if has_sentiment:
                sentiment = row.get("sentiment_label", "neutral")
                enriched["jina_aspect_sentiment"] = f"{aspect}:{sentiment}"

            csv_writer.writerow(enriched)
            tsv_writer.writerow(enriched)

            # Track stats
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
            if has_sentiment:
                sentiment = row.get("sentiment_label", "neutral")
                if aspect not in aspect_sentiment:
                    aspect_sentiment[aspect] = {}
                aspect_sentiment[aspect][sentiment] = (
                    aspect_sentiment[aspect].get(sentiment, 0) + 1
                )

    # ── Summary ──────────────────────────────────────────────────────────
    summary = {
        "input_file": str(input_path),
        "rows_total": len(all_rows),
        "rows_classified": len(all_rows) - skipped,
        "rows_skipped": skipped,
        "model": JINA_MODEL,
        "aspect_labels": ASPECT_LABELS,
        "aspect_counts": dict(
            sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "aspect_sentiment_crosstab": aspect_sentiment,
        "output_csv": str(output_csv),
        "output_tsv": str(output_tsv),
    }

    with output_summary.open("w", encoding="utf-8") as sf:
        json.dump(summary, sf, ensure_ascii=False, indent=2)

    print("\n── Classification Complete ──")
    print(f"Rows total:      {len(all_rows)}")
    print(f"Rows classified: {len(all_rows) - skipped}")
    print(f"Rows skipped:    {skipped}")
    print(f"\nAspect distribution:")
    for aspect, count in sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(all_rows) * 100
        print(f"  {aspect:40s} {count:6d}  ({pct:.1f}%)")
    print(f"\nCSV: {output_csv}")
    print(f"TSV: {output_tsv}")
    print(f"Summary: {output_summary}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aspect-Based Sentiment Analysis via Jina AI Classifier"
    )
    parser.add_argument("--input", required=True, help="Input CSV/TSV file")
    parser.add_argument(
        "--output-prefix",
        default="output/zepto_jina_absa",
        help="Output file prefix (without extension)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for API calls (default: 64, max 1024)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Max rows to process (for testing)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Jina API key (default: read from JINA_API_KEY env var)",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("JINA_API_KEY", "")
    if not api_key or api_key == "your_jina_api_key_here":
        print("ERROR: Set JINA_API_KEY environment variable or use --api-key flag.")
        print("Get a free key at https://jina.ai")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    run_classification(
        input_path,
        Path(args.output_prefix),
        api_key,
        batch_size=min(max(args.batch_size, 1), 1024),
        max_rows=max(args.max_rows, 1) if args.max_rows else None,
    )


if __name__ == "__main__":
    main()
