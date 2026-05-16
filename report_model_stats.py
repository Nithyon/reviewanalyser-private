#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def pct(count: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def classify_run(path: Path) -> str:
    name = path.stem.lower()
    if "test" in name:
        return "test"
    return "full"


def friendly_model_name(summary_name: str, sentiment_model: str | None) -> str:
    if sentiment_model:
        return sentiment_model
    lower = summary_name.lower()
    if "apr2025_mar2026_sentiment" in lower:
        return "unspecified-model"
    if "mbert" in lower:
        return "nlptown/bert-base-multilingual-uncased-sentiment"
    if "deberta" in lower:
        return "mrm8488/deberta-v3-small-finetuned-sst2"
    if "bert" in lower:
        return "bert (legacy output)"
    return "unknown"


def infer_model_key(name: str, model_name: str) -> str:
    lower = f"{name} {model_name}".lower()
    if "unspecified-model" in lower:
        return "unspecified"
    if "deberta" in lower:
        return "deberta"
    if "mbert" in lower or "multilingual" in lower:
        return "mbert"
    if "bert" in lower:
        return "bert"
    return Path(name).stem


def load_summary_records(output_dir: Path) -> list[dict]:
    records = []
    for path in sorted(output_dir.glob("*summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        sentiment_counts = data.get("sentiment_counts", {})
        rows_total = int(data.get("rows_total", 0) or 0)
        rows_scored = int(data.get("rows_scored", 0) or 0)
        rows_skipped = int(data.get("rows_skipped_too_short", 0) or 0)
        rows_failed = int(data.get("rows_model_failed", 0) or 0)
        model_name = friendly_model_name(path.name, data.get("sentiment_model"))
        records.append(
            {
                "source": path.name,
                "model_key": infer_model_key(path.name, model_name),
                "model_name": model_name,
                "run_type": classify_run(path),
                "rows_total": rows_total,
                "rows_scored": rows_scored,
                "rows_skipped_too_short": rows_skipped,
                "rows_model_failed": rows_failed,
                "avg_rating": data.get("avg_rating"),
                "sentiment_counts": {
                    "negative": int(sentiment_counts.get("negative", 0) or 0),
                    "neutral": int(sentiment_counts.get("neutral", 0) or 0),
                    "positive": int(sentiment_counts.get("positive", 0) or 0),
                },
                "theme_counts": data.get("theme_counts", {}),
                "output_csv": data.get("output_csv"),
                "output_tsv": data.get("output_tsv"),
                "input_file": data.get("input_file"),
                "has_summary_json": True,
            }
        )
    return records


def load_tsv_legacy_record(tsv_path: Path) -> dict | None:
    if not tsv_path.exists():
        return None

    with tsv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return None

        sentiment_column = None
        confidence_column = None
        stars_column = None
        for field in reader.fieldnames:
            field_l = field.lower()
            if field_l.endswith("_sentiment"):
                sentiment_column = field
            elif field_l.endswith("_confidence"):
                confidence_column = field
            elif field_l.endswith("_stars"):
                stars_column = field

        if not sentiment_column:
            return None

        rows_total = 0
        rows_scored = 0
        counts: Counter[str] = Counter()
        confidence_sum = 0.0
        confidence_count = 0

        for row in reader:
            rows_total += 1
            sentiment = (row.get(sentiment_column, "") or "").strip().lower()
            if sentiment:
                counts[sentiment] += 1
                rows_scored += 1

            if confidence_column:
                try:
                    confidence_sum += float(row.get(confidence_column, "") or 0.0)
                    confidence_count += 1
                except ValueError:
                    pass

        record = {
            "source": tsv_path.name,
            "model_key": "bert",
            "model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
            "run_type": classify_run(tsv_path),
            "rows_total": rows_total,
            "rows_scored": rows_scored,
            "rows_skipped_too_short": max(rows_total - rows_scored, 0),
            "rows_model_failed": 0,
            "avg_rating": None,
            "sentiment_counts": {
                "negative": int(counts.get("negative", 0)),
                "neutral": int(counts.get("neutral", 0)),
                "positive": int(counts.get("positive", 0)),
            },
            "theme_counts": {},
            "output_csv": None,
            "output_tsv": str(tsv_path),
            "input_file": None,
            "has_summary_json": False,
        }
        if confidence_count:
            record["avg_confidence"] = round(confidence_sum / confidence_count, 4)
        if stars_column:
            record["stars_column"] = stars_column
        return record

    return None


def build_records(output_dir: Path) -> list[dict]:
    records = load_summary_records(output_dir)
    summary_keys = {(r["model_key"], r["run_type"]) for r in records}

    legacy_candidates = [
        output_dir / "zepto_reviews_bert_sentiment.tsv",
    ]
    for tsv_path in legacy_candidates:
        record = load_tsv_legacy_record(tsv_path)
        if not record:
            continue
        key = (record["model_key"], record["run_type"])
        if key not in summary_keys:
            records.append(record)

    records.sort(key=lambda item: (item["run_type"], item["model_key"], item["source"]))
    return records


def make_table(records: list[dict]) -> str:
    header = (
        "| Model | Run | Rows | Scored | Neg | Neu | Pos | Neg % | Neu % | Pos % | Summary |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    )
    rows = []
    for record in records:
        counts = record["sentiment_counts"]
        total = int(record["rows_total"])
        rows.append(
            "| {model} | {run} | {rows_total} | {rows_scored} | {negative} | {neutral} | {positive} | {neg_pct} | {neu_pct} | {pos_pct} | {summary} |".format(
                model=record["model_key"],
                run=record["run_type"],
                rows_total=record["rows_total"],
                rows_scored=record["rows_scored"],
                negative=counts["negative"],
                neutral=counts["neutral"],
                positive=counts["positive"],
                neg_pct=pct(counts["negative"], total),
                neu_pct=pct(counts["neutral"], total),
                pos_pct=pct(counts["positive"], total),
                summary="yes" if record["has_summary_json"] else "no",
            )
        )
    return "\n".join([header, *rows])


def make_run_section(records: list[dict]) -> str:
    lines = ["## Model Runs", ""]
    for record in records:
        counts = record["sentiment_counts"]
        lines.append(f"### {record['model_key']} ({record['run_type']})")
        lines.append(f"- Source: `{record['source']}`")
        lines.append(f"- Model: `{record['model_name']}`")
        lines.append(f"- Rows total: `{record['rows_total']}`")
        lines.append(f"- Rows scored: `{record['rows_scored']}`")
        lines.append(f"- Rows skipped too short: `{record['rows_skipped_too_short']}`")
        lines.append(f"- Negative / Neutral / Positive: `{counts['negative']}` / `{counts['neutral']}` / `{counts['positive']}`")
        lines.append(
            f"- Class distribution: `{pct(counts['negative'], record['rows_total'])}` negative, "
            f"`{pct(counts['neutral'], record['rows_total'])}` neutral, "
            f"`{pct(counts['positive'], record['rows_total'])}` positive"
        )
        if record.get("avg_rating") is not None:
            lines.append(f"- Average source rating: `{record['avg_rating']}`")
        if record.get("avg_confidence") is not None:
            lines.append(f"- Average confidence: `{record['avg_confidence']}`")
        if record.get("output_tsv"):
            lines.append(f"- Output TSV: `{record['output_tsv']}`")
        if record.get("output_csv"):
            lines.append(f"- Output CSV: `{record['output_csv']}`")
        theme_counts = record.get("theme_counts") or {}
        if theme_counts:
            top_themes = list(theme_counts.items())[:5]
            lines.append(
                "- Top themes: "
                + ", ".join(f"`{name}={count}`" for name, count in top_themes)
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def build_payload(records: list[dict]) -> dict:
    return {
        "records": records,
        "table_markdown": make_table(records),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize BERT-family model runs from the output directory")
    parser.add_argument("--output-dir", default="output", help="Directory containing summary JSON and model outputs")
    parser.add_argument("--json-out", help="Optional path to save the aggregated JSON report")
    parser.add_argument("--md-out", help="Optional path to save a Markdown report")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    records = build_records(output_dir)
    if not records:
        raise FileNotFoundError(f"No model summary files or compatible TSV outputs found in {output_dir}")

    payload = build_payload(records)
    markdown = "# Model Stats Report\n\n" + payload["table_markdown"] + "\n\n" + make_run_section(records) + "\n"

    print(payload["table_markdown"])

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.md_out:
        md_path = Path(args.md_out)
        md_path.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
