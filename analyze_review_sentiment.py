#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import torch
from transformers import pipeline


TEXT_COLUMN_CANDIDATES = [
    "Review_Content",
    "content",
    "review",
    "comment",
    "text",
]

RATING_COLUMN_CANDIDATES = [
    "Rating",
    "score",
    "rating",
]

THEME_RULES = {
    "free_cash_issue": [
        "free cash",
        "cash disabled",
        "wallet",
        "coupon",
        "offer",
        "discount",
        "promo",
    ],
    "delivery_delay": [
        "late",
        "delay",
        "delayed",
        "delivery time",
        "not delivered",
        "cancelled",
        "canceled",
    ],
    "product_quality": [
        "stale",
        "spoiled",
        "rotten",
        "expired",
        "fake",
        "damaged",
        "quality",
        "bad product",
    ],
    "refund_payment": [
        "refund",
        "double payment",
        "charged",
        "extra payment",
        "debited",
        "money back",
    ],
    "support_service": [
        "customer support",
        "customer care",
        "help option",
        "support team",
        "no response",
        "service",
    ],
    "out_of_stock": [
        "out of stock",
        "not available",
        "unavailable",
        "missing item",
    ],
    "pricing_charges": [
        "handling charge",
        "delivery charge",
        "high price",
        "expensive",
        "overcharge",
        "mrp",
        "price",
    ],
    "app_bugs": [
        "bug",
        "glitch",
        "crash",
        "stuck",
        "not working",
        "error",
        "otp",
    ],
    "location_unavailable": [
        "not in your area",
        "location",
        "serviceable",
        "area",
    ],
}


def detect_delimiter(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def pick_column(columns: list[str], candidates: list[str]) -> str:
    column_lookup = {c.lower(): c for c in columns}
    for name in candidates:
        key = name.lower()
        if key in column_lookup:
            return column_lookup[key]
    raise ValueError(f"Could not find any of these columns: {candidates}")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def stars_to_label(stars: int) -> str:
    if stars >= 4:
        return "positive"
    if stars <= 2:
        return "negative"
    return "neutral"


def parse_stars(label: str) -> int | None:
    text = (label or "").strip().lower()
    match = re.search(r"[1-5]", text)
    if match:
        return int(match.group(0))
    return None


def parse_model_label(label: str, label_map: dict[str, str]) -> str:
    text = (label or "").strip()
    text_l = text.lower()

    mapped = label_map.get(text) or label_map.get(text_l)
    if mapped in {"positive", "neutral", "negative"}:
        return mapped

    stars = parse_stars(text)
    if stars is not None:
        return stars_to_label(stars)

    if "positive" in text_l:
        return "positive"
    if "negative" in text_l:
        return "negative"
    if "neutral" in text_l:
        return "neutral"

    return "neutral"


def extract_themes(text: str) -> list[str]:
    text_l = f" {text.lower()} "
    matched = []
    for theme, patterns in THEME_RULES.items():
        for pattern in patterns:
            if pattern in text_l:
                matched.append(theme)
                break
    return matched


def parse_rating(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def analyze_reviews(
    input_path: Path,
    output_prefix: Path,
    min_chars: int,
    model_name: str,
    batch_size: int,
    max_rows: int | None,
    label_map: dict[str, str],
) -> None:
    input_delimiter = detect_delimiter(input_path)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    output_csv = output_prefix.with_suffix(".csv")
    output_tsv = output_prefix.with_suffix(".tsv")
    output_summary = output_prefix.with_name(f"{output_prefix.name}_summary.json")

    device = 0 if torch.cuda.is_available() else -1
    classifier = pipeline(
        "text-classification",
        model=model_name,
        device=device,
    )

    sentiment_counts: Counter[str] = Counter()
    theme_counts: Counter[str] = Counter()
    rows_total = 0
    rows_scored = 0
    rows_skipped_short = 0
    rows_model_failed = 0
    rating_sum = 0.0
    rating_count = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile, delimiter=input_delimiter)
        if not reader.fieldnames:
            raise ValueError("Input file has no header row")

        text_column = pick_column(reader.fieldnames, TEXT_COLUMN_CANDIDATES)
        rating_column = pick_column(reader.fieldnames, RATING_COLUMN_CANDIDATES)

        out_fields = list(reader.fieldnames) + [
            "sentiment_label",
            "bert_stars",
            "bert_confidence",
            "detected_themes",
        ]

        with output_csv.open("w", encoding="utf-8-sig", newline="") as csv_out, output_tsv.open(
            "w", encoding="utf-8-sig", newline=""
        ) as tsv_out:
            csv_writer = csv.DictWriter(csv_out, fieldnames=out_fields)
            tsv_writer = csv.DictWriter(tsv_out, fieldnames=out_fields, delimiter="\t")
            csv_writer.writeheader()
            tsv_writer.writeheader()

            pending_rows: list[dict[str, str]] = []
            pending_texts: list[str] = []

            def flush_pending() -> None:
                nonlocal rows_scored, rows_model_failed
                if not pending_rows:
                    return

                try:
                    results = classifier(
                        pending_texts,
                        truncation=True,
                        max_length=512,
                    )
                except Exception:
                    rows_model_failed += len(pending_rows)
                    results = [{"label": "3 stars", "score": 0.0}] * len(pending_rows)

                for base_row, text, result in zip(pending_rows, pending_texts, results):
                    model_label = str(result.get("label", "neutral"))
                    stars = parse_stars(model_label)
                    confidence = float(result.get("score", 0.0) or 0.0)
                    sentiment_label = parse_model_label(model_label, label_map)
                    themes = extract_themes(text)

                    rows_scored += 1
                    sentiment_counts[sentiment_label] += 1
                    for theme in themes:
                        theme_counts[theme] += 1

                    enriched = dict(base_row)
                    enriched["sentiment_label"] = sentiment_label
                    enriched["bert_stars"] = "" if stars is None else str(stars)
                    enriched["bert_confidence"] = f"{confidence:.4f}"
                    enriched["detected_themes"] = ";".join(themes)

                    csv_writer.writerow(enriched)
                    tsv_writer.writerow(enriched)

                pending_rows.clear()
                pending_texts.clear()

            for row in reader:
                rows_total += 1
                text = normalize_text(row.get(text_column, ""))

                if len(text) < min_chars:
                    rows_skipped_short += 1
                    sentiment_label = "neutral"
                    themes = []

                    sentiment_counts[sentiment_label] += 1
                    enriched = dict(row)
                    enriched["sentiment_label"] = sentiment_label
                    enriched["bert_stars"] = ""
                    enriched["bert_confidence"] = "0.0000"
                    enriched["detected_themes"] = ""

                    csv_writer.writerow(enriched)
                    tsv_writer.writerow(enriched)
                else:
                    pending_rows.append(row)
                    pending_texts.append(text)

                    if len(pending_rows) >= max(batch_size, 1):
                        flush_pending()

                rating_val = parse_rating(row.get(rating_column, ""))
                if rating_val is not None:
                    rating_sum += rating_val
                    rating_count += 1

                if rows_total % 10000 == 0:
                    print(f"Processed {rows_total} rows...")

                if max_rows is not None and rows_total >= max_rows:
                    break

            flush_pending()

    summary = {
        "input_file": str(input_path),
        "rows_total": rows_total,
        "rows_scored": rows_scored,
        "rows_skipped_too_short": rows_skipped_short,
        "rows_model_failed": rows_model_failed,
        "sentiment_model": model_name,
        "avg_rating": round((rating_sum / rating_count), 4) if rating_count else None,
        "sentiment_counts": dict(sentiment_counts),
        "theme_counts": dict(theme_counts.most_common()),
        "output_csv": str(output_csv),
        "output_tsv": str(output_tsv),
    }

    with output_summary.open("w", encoding="utf-8") as sf:
        json.dump(summary, sf, ensure_ascii=False, indent=2)

    print("Sentiment analysis complete")
    print(f"Input: {input_path}")
    print(f"Rows total: {rows_total}")
    print(f"Rows scored: {rows_scored}")
    print(f"Rows skipped (short text): {rows_skipped_short}")
    print(f"Sentiment counts: {dict(sentiment_counts)}")
    print(f"Top themes: {theme_counts.most_common(8)}")
    print(f"CSV output: {output_csv}")
    print(f"TSV output: {output_tsv}")
    print(f"Summary JSON: {output_summary}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multilingual BERT sentiment and theme analysis")
    parser.add_argument("--input", required=True, help="Path to input CSV/TSV file")
    parser.add_argument(
        "--output-prefix",
        default="output/zepto_reviews_sentiment",
        help="Output file prefix (without extension)",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=3,
        help="Minimum text length required for scoring (default: 3)",
    )
    parser.add_argument(
        "--model-name",
        default="mrm8488/deberta-v3-small-finetuned-sst2",
        help="Hugging Face model name for sentiment scoring",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for model inference (default: 32)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap for rows to process (useful for quick validation)",
    )
    parser.add_argument(
        "--label-map-json",
        default='{"label_0":"negative","label_1":"positive"}',
        help=(
            "Optional JSON map from model labels to sentiment labels. "
            "Example: {\"LABEL_0\":\"negative\",\"LABEL_1\":\"neutral\",\"LABEL_2\":\"positive\"}"
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    try:
        label_map_raw = json.loads(args.label_map_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --label-map-json: {exc}") from exc

    label_map = {str(k): str(v).lower() for k, v in dict(label_map_raw).items()}

    analyze_reviews(
        input_path,
        Path(args.output_prefix),
        min_chars=max(args.min_chars, 0),
        model_name=args.model_name,
        batch_size=max(args.batch_size, 1),
        max_rows=max(args.max_rows, 1) if args.max_rows is not None else None,
        label_map=label_map,
    )


if __name__ == "__main__":
    main()
