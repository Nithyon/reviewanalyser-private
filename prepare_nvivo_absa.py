#!/usr/bin/env python3
"""Format Jina AI ABSA results for NVivo import.

Reads the enriched CSV/TSV produced by jina_classify_aspects.py and
writes an NVivo-compatible TSV with standardised columns plus aspect
coding columns for qualitative analysis.
"""

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


# NVivo target columns (standard + ABSA additions)
NVIVO_HEADERS = [
    "Review_ID",
    "Author",
    "Rating",
    "Date",
    "Review_Content",
    "Thumbs_Up",
    "Aspect_Category",
    "Aspect_Sentiment",
    "Aspect_Confidence",
    "Overall_Sentiment",
    "Detected_Themes",
    "ABSA_Model",
]

# Source → NVivo column mapping (case-insensitive key → target)
HEADER_MAP = {
    # Google Play review columns
    "review_id": "Review_ID",
    "reviewid": "Review_ID",
    "author": "Author",
    "username": "Author",
    # Reddit columns
    "id": "Review_ID",
    "name": "Review_ID",
    # Shared
    "rating": "Rating",
    "score": "Rating",
    "date": "Date",
    "at": "Date",
    "created_iso": "Date",
    "review_content": "Review_Content",
    "content": "Review_Content",
    "title": "Review_Content",
    "thumbs_up": "Thumbs_Up",
    "thumbsupcount": "Thumbs_Up",
    "upvote_ratio": "Thumbs_Up",
    # ABSA columns
    "jina_aspect": "Aspect_Category",
    "jina_aspect_confidence": "Aspect_Confidence",
    "sentiment_label": "Overall_Sentiment",
    "detected_themes": "Detected_Themes",
    "jina_aspect_sentiment": "Aspect_Sentiment",
}


def _norm_key(name: str) -> str:
    return "".join(ch for ch in (name or "").strip().lower() if ch.isalnum() or ch == "_")


def _normalize_timestamp(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    for candidate in [text, text.replace("Z", "+00:00")]:
        try:
            dt = datetime.fromisoformat(candidate)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return text


def prepare_nvivo_absa(input_path: Path, output_path: Path) -> None:
    delimiter = "\t" if input_path.suffix.lower() == ".tsv" else ","
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile, \
         output_path.open("w", encoding="utf-8-sig", newline="") as outfile:

        reader = csv.DictReader(infile, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Input file has no header row")

        writer = csv.DictWriter(
            outfile,
            fieldnames=NVIVO_HEADERS,
            delimiter="\t",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        source_cols = list(reader.fieldnames)

        for idx, row in enumerate(reader, start=1):
            out = {h: "" for h in NVIVO_HEADERS}

            # Map source columns
            for src_key, value in row.items():
                mapped = HEADER_MAP.get(_norm_key(src_key))
                if mapped and mapped in out:
                    # Don't overwrite if already set (priority order matters)
                    if not out[mapped]:
                        out[mapped] = value

            # For Reddit: combine title + selftext as Review_Content
            if "selftext" in source_cols:
                title = (row.get("title") or "").strip()
                selftext = (row.get("selftext") or "").strip()
                if selftext.lower() not in ("[removed]", "[deleted]", ""):
                    out["Review_Content"] = f"{title}. {selftext}" if title else selftext
                elif title:
                    out["Review_Content"] = title

            # Auto-generate ID if missing
            if not out["Review_ID"]:
                out["Review_ID"] = f"AUTO_{idx}"

            # Normalize timestamps
            out["Date"] = _normalize_timestamp(out["Date"])

            # Set ABSA model label
            out["ABSA_Model"] = "jina-embeddings-v3"

            # Build aspect sentiment from aspect + overall sentiment
            if out["Aspect_Category"] and out["Overall_Sentiment"] and not out["Aspect_Sentiment"]:
                out["Aspect_Sentiment"] = f"{out['Aspect_Category']}:{out['Overall_Sentiment']}"

            # Skip rows with no content
            content = re.sub(r"\s+", " ", (out["Review_Content"] or "").strip())
            if len(content) < 2:
                skipped += 1
                continue

            out["Review_Content"] = content
            writer.writerow(out)
            written += 1

    print("NVivo ABSA Export Complete")
    print(f"Rows written:  {written}")
    print(f"Rows skipped:  {skipped}")
    print(f"Output:        {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ABSA results for NVivo import")
    parser.add_argument("--input", required=True, help="Input ABSA-enriched CSV/TSV")
    parser.add_argument("--output", required=True, help="Output NVivo TSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    prepare_nvivo_absa(input_path, output_path)


if __name__ == "__main__":
    main()
