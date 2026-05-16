#!/usr/bin/env python3
"""Deep-dive analytics for Zepto review sentiment outputs.

Generates a high-level + technical report from existing sentiment CSV/TSV files.
Outputs:
- JSON metrics payload
- Markdown narrative report
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ID_CANDIDATES = ["Review_ID", "reviewId", "id", "name"]
RATING_CANDIDATES = ["Rating", "score", "rating"]
DATE_CANDIDATES = ["Date", "at", "created_iso", "date"]
SENTIMENT_CANDIDATES = ["sentiment_label", "BERT_Sentiment", "bert_sentiment"]
CONFIDENCE_CANDIDATES = ["bert_confidence", "BERT_Confidence", "sentiment_confidence"]
THEME_CANDIDATES = ["detected_themes"]


def detect_delimiter(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {c.lower(): c for c in columns}
    for cand in candidates:
        found = lookup.get(cand.lower())
        if found:
            return found
    return None


def parse_month(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) >= 7 and text[4] == "-":
        return text[:7]
    patterns = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"]
    for pattern in patterns:
        try:
            dt = datetime.strptime(text, pattern)
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    return None


def parse_rating(value: str) -> int | None:
    try:
        rating = int(float((value or "").strip()))
    except (ValueError, TypeError):
        return None
    if 1 <= rating <= 5:
        return rating
    return None


def normalize_sentiment(value: str) -> str | None:
    text = (value or "").strip().lower()
    if text in {"positive", "neutral", "negative"}:
        return text
    return None


def rating_to_proxy_sentiment(rating: int | None) -> str | None:
    if rating is None:
        return None
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def parse_themes(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def safe_float(value: str) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_model_file(path: Path) -> dict:
    delimiter = detect_delimiter(path)
    rows_by_id: dict[str, dict] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"No header found in {path}")

        columns = list(reader.fieldnames)
        id_col = pick_column(columns, ID_CANDIDATES)
        rating_col = pick_column(columns, RATING_CANDIDATES)
        date_col = pick_column(columns, DATE_CANDIDATES)
        sentiment_col = pick_column(columns, SENTIMENT_CANDIDATES)
        confidence_col = pick_column(columns, CONFIDENCE_CANDIDATES)
        themes_col = pick_column(columns, THEME_CANDIDATES)

        if not id_col or not sentiment_col:
            raise ValueError(
                f"Required columns missing in {path}. Found headers: {', '.join(columns)}"
            )

        for idx, row in enumerate(reader, start=1):
            row_id = (row.get(id_col) or "").strip() or f"__row_{idx}"
            rating = parse_rating(row.get(rating_col, "") if rating_col else "")
            date_text = row.get(date_col, "") if date_col else ""
            sentiment = normalize_sentiment(row.get(sentiment_col, ""))
            confidence = safe_float(row.get(confidence_col, "") if confidence_col else "")
            themes = parse_themes(row.get(themes_col, "") if themes_col else "")

            if not sentiment:
                continue

            rows_by_id[row_id] = {
                "sentiment": sentiment,
                "rating": rating,
                "month": parse_month(date_text),
                "confidence": confidence,
                "themes": themes,
            }

    return {
        "path": str(path),
        "row_count": len(rows_by_id),
        "rows": rows_by_id,
    }


def monthly_sentiment_trends(rows: dict[str, dict]) -> dict:
    month_counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows.values():
        month = row.get("month")
        sentiment = row.get("sentiment")
        if month and sentiment:
            month_counts[month][sentiment] += 1

    trends = {}
    for month in sorted(month_counts.keys()):
        counts = month_counts[month]
        total = sum(counts.values())
        trends[month] = {
            "total": total,
            "negative": counts.get("negative", 0),
            "neutral": counts.get("neutral", 0),
            "positive": counts.get("positive", 0),
            "negative_pct": round(100.0 * counts.get("negative", 0) / total, 2) if total else 0.0,
            "neutral_pct": round(100.0 * counts.get("neutral", 0) / total, 2) if total else 0.0,
            "positive_pct": round(100.0 * counts.get("positive", 0) / total, 2) if total else 0.0,
        }
    return trends


def theme_prevalence_by_rating_bucket(rows: dict[str, dict], top_n: int = 10) -> dict:
    reviews_per_bucket: Counter[int] = Counter()
    theme_review_counts: dict[int, Counter] = defaultdict(Counter)

    for row in rows.values():
        rating = row.get("rating")
        if rating is None:
            continue
        reviews_per_bucket[rating] += 1
        unique_themes = set(row.get("themes") or [])
        for theme in unique_themes:
            theme_review_counts[rating][theme] += 1

    out = {}
    for rating in sorted(reviews_per_bucket.keys()):
        total = reviews_per_bucket[rating]
        ranked = []
        for theme, count in theme_review_counts[rating].most_common(top_n):
            ranked.append(
                {
                    "theme": theme,
                    "review_count": count,
                    "prevalence_pct": round(100.0 * count / total, 2) if total else 0.0,
                }
            )
        out[str(rating)] = {"reviews": total, "top_themes": ranked}
    return out


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b) or not labels_a:
        return 0.0
    classes = sorted({*labels_a, *labels_b})
    n = len(labels_a)
    observed = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    a_counts = Counter(labels_a)
    b_counts = Counter(labels_b)
    expected = 0.0
    for cls in classes:
        expected += (a_counts.get(cls, 0) / n) * (b_counts.get(cls, 0) / n)

    if math.isclose(1.0 - expected, 0.0):
        return 0.0
    return (observed - expected) / (1.0 - expected)


def pairwise_model_agreement(model_rows: dict[str, dict[str, dict]]) -> dict:
    model_names = sorted(model_rows.keys())
    result = {}

    for i in range(len(model_names)):
        for j in range(i + 1, len(model_names)):
            left = model_names[i]
            right = model_names[j]
            ids = sorted(set(model_rows[left]).intersection(model_rows[right]))
            labels_left = [model_rows[left][rid]["sentiment"] for rid in ids]
            labels_right = [model_rows[right][rid]["sentiment"] for rid in ids]
            matches = sum(1 for a, b in zip(labels_left, labels_right) if a == b)
            total = len(ids)

            confusion = {
                "negative": {"negative": 0, "neutral": 0, "positive": 0},
                "neutral": {"negative": 0, "neutral": 0, "positive": 0},
                "positive": {"negative": 0, "neutral": 0, "positive": 0},
            }
            for la, lb in zip(labels_left, labels_right):
                confusion[la][lb] += 1

            key = f"{left}_vs_{right}"
            result[key] = {
                "overlap_rows": total,
                "agreement_rate": round(matches / total, 4) if total else 0.0,
                "cohen_kappa": round(cohen_kappa(labels_left, labels_right), 4),
                "confusion_matrix": confusion,
            }

    return result


def multi_model_disagreement(model_rows: dict[str, dict[str, dict]]) -> dict:
    names = sorted(model_rows.keys())
    if len(names) < 3:
        return {"message": "Need at least 3 models for multi-model disagreement."}

    shared_ids = set(model_rows[names[0]])
    for name in names[1:]:
        shared_ids &= set(model_rows[name])

    unanimous = 0
    two_vs_one = 0
    all_different = 0
    examples = []

    for rid in sorted(shared_ids):
        labels = [model_rows[n][rid]["sentiment"] for n in names]
        unique = set(labels)
        if len(unique) == 1:
            unanimous += 1
        elif len(unique) == 2:
            two_vs_one += 1
            if len(examples) < 5:
                examples.append({"id": rid, **{n: model_rows[n][rid]["sentiment"] for n in names}})
        else:
            all_different += 1

    total = len(shared_ids)
    return {
        "shared_rows": total,
        "unanimous": unanimous,
        "two_vs_one": two_vs_one,
        "all_different": all_different,
        "unanimous_pct": round(100.0 * unanimous / total, 2) if total else 0.0,
        "two_vs_one_pct": round(100.0 * two_vs_one / total, 2) if total else 0.0,
        "all_different_pct": round(100.0 * all_different / total, 2) if total else 0.0,
        "sample_disagreements": examples,
    }


def confidence_calibration(rows: dict[str, dict], bins: int = 10) -> dict:
    scored = []
    for row in rows.values():
        conf = row.get("confidence")
        proxy = rating_to_proxy_sentiment(row.get("rating"))
        pred = row.get("sentiment")
        if conf is None or proxy is None or pred is None:
            continue
        scored.append((conf, pred == proxy))

    if not scored:
        return {"samples": 0, "message": "No confidence + rating proxy overlap."}

    bucket_stats = []
    total = len(scored)
    ece = 0.0

    for idx in range(bins):
        lo = idx / bins
        hi = (idx + 1) / bins
        current = [item for item in scored if (item[0] >= lo and (item[0] < hi or (idx == bins - 1 and item[0] <= hi)))]
        if not current:
            continue
        avg_conf = sum(c for c, _ in current) / len(current)
        acc = sum(1 for _, ok in current if ok) / len(current)
        bucket_weight = len(current) / total
        ece += bucket_weight * abs(acc - avg_conf)
        bucket_stats.append(
            {
                "range": f"{lo:.1f}-{hi:.1f}",
                "samples": len(current),
                "avg_confidence": round(avg_conf, 4),
                "proxy_accuracy": round(acc, 4),
                "gap": round(abs(acc - avg_conf), 4),
            }
        )

    overall_acc = sum(1 for _, ok in scored if ok) / total
    overall_conf = sum(c for c, _ in scored) / total

    return {
        "samples": total,
        "proxy_accuracy": round(overall_acc, 4),
        "avg_confidence": round(overall_conf, 4),
        "ece": round(ece, 4),
        "bins": bucket_stats,
    }


def cramers_v_from_rating_sentiment(rows: dict[str, dict]) -> dict:
    sentiments = ["negative", "neutral", "positive"]
    ratings = [1, 2, 3, 4, 5]

    table = {r: {s: 0 for s in sentiments} for r in ratings}
    used = 0
    sentiment_rating_values: dict[str, list[int]] = defaultdict(list)

    for row in rows.values():
        rating = row.get("rating")
        sentiment = row.get("sentiment")
        if rating in table and sentiment in sentiments:
            table[rating][sentiment] += 1
            sentiment_rating_values[sentiment].append(rating)
            used += 1

    if used == 0:
        return {"samples": 0, "message": "No rating/sentiment overlap."}

    row_totals = {r: sum(table[r].values()) for r in ratings}
    col_totals = {s: sum(table[r][s] for r in ratings) for s in sentiments}

    chi2 = 0.0
    for r in ratings:
        for s in sentiments:
            expected = row_totals[r] * col_totals[s] / used if used else 0.0
            observed = table[r][s]
            if expected > 0:
                chi2 += ((observed - expected) ** 2) / expected

    k = min(len(ratings), len(sentiments))
    cramers_v = math.sqrt(chi2 / (used * (k - 1))) if k > 1 else 0.0

    avg_rating_by_sentiment = {
        s: round(sum(vals) / len(vals), 4) if vals else None
        for s, vals in sentiment_rating_values.items()
    }

    return {
        "samples": used,
        "chi_square": round(chi2, 4),
        "cramers_v": round(cramers_v, 4),
        "contingency": {str(r): table[r] for r in ratings},
        "avg_rating_by_sentiment": avg_rating_by_sentiment,
    }


def top_findings(payload: dict) -> list[str]:
    findings: list[str] = []

    base_model = payload["analysis_model"]
    rating_assoc = payload["rating_sentiment_association"]
    disagreement = payload["multi_model_disagreement"]

    findings.append(
        f"Base analysis model: {base_model}. Rows analyzed: {payload['analysis_row_count']}."
    )

    if rating_assoc.get("samples", 0) > 0:
        findings.append(
            "Rating-sentiment association (Cramer's V): "
            f"{rating_assoc.get('cramers_v', 0.0)} over {rating_assoc['samples']} rows."
        )

    if disagreement.get("shared_rows"):
        findings.append(
            "Model consensus on shared rows: "
            f"{disagreement['unanimous_pct']}% unanimous, "
            f"{disagreement['two_vs_one_pct']}% two-vs-one, "
            f"{disagreement['all_different_pct']}% all-different."
        )

    pairwise = payload.get("pairwise_agreement", {})
    if pairwise:
        strongest = max(pairwise.items(), key=lambda item: item[1].get("cohen_kappa", 0.0))
        weakest = min(pairwise.items(), key=lambda item: item[1].get("cohen_kappa", 0.0))
        findings.append(
            f"Strongest pairwise agreement: {strongest[0]} (kappa={strongest[1]['cohen_kappa']})."
        )
        findings.append(
            f"Weakest pairwise agreement: {weakest[0]} (kappa={weakest[1]['cohen_kappa']})."
        )

    calib = payload.get("calibration", {})
    if calib.get("samples", 0) > 0:
        findings.append(
            f"Calibration proxy on {calib['samples']} rows: accuracy={calib['proxy_accuracy']}, "
            f"avg_confidence={calib['avg_confidence']}, ECE={calib['ece']}."
        )

    trends = payload.get("monthly_trends", {})
    if trends:
        best_month = max(trends.items(), key=lambda kv: kv[1].get("positive_pct", 0.0))
        worst_month = max(trends.items(), key=lambda kv: kv[1].get("negative_pct", 0.0))
        findings.append(
            f"Highest positive-share month: {best_month[0]} ({best_month[1].get('positive_pct', 0.0)}%)."
        )
        findings.append(
            f"Highest negative-share month: {worst_month[0]} ({worst_month[1].get('negative_pct', 0.0)}%)."
        )

    themes = payload.get("theme_by_rating_bucket", {})
    low = themes.get("1", {}).get("top_themes", [])
    high = themes.get("5", {}).get("top_themes", [])
    if low:
        findings.append(
            f"Top theme at 1-star: {low[0]['theme']} ({low[0]['prevalence_pct']}% prevalence)."
        )
    if high:
        findings.append(
            f"Top theme at 5-star: {high[0]['theme']} ({high[0]['prevalence_pct']}% prevalence)."
        )

    return findings[:10]


def write_markdown_report(payload: dict, md_path: Path) -> None:
    lines = [
        "# Deep Technical Report",
        "",
        f"- Analysis model: `{payload['analysis_model']}`",
        f"- Rows analyzed: `{payload['analysis_row_count']}`",
        f"- Models compared: `{', '.join(payload['compared_models'])}`",
        "",
        "## Executive Findings",
        "",
    ]
    for finding in payload.get("top_findings", []):
        lines.append(f"- {finding}")

    lines += ["", "## Pairwise Model Agreement", ""]
    lines.append("| Pair | Overlap Rows | Agreement | Kappa |")
    lines.append("|---|---:|---:|---:|")
    for pair, metrics in payload.get("pairwise_agreement", {}).items():
        lines.append(
            f"| {pair} | {metrics['overlap_rows']} | {metrics['agreement_rate']:.4f} | {metrics['cohen_kappa']:.4f} |"
        )

    lines += ["", "## Calibration (Rating Proxy)", ""]
    calib = payload.get("calibration", {})
    if calib.get("samples", 0) > 0:
        lines.append(
            f"- Samples: `{calib['samples']}` | Accuracy: `{calib['proxy_accuracy']}` | "
            f"Avg confidence: `{calib['avg_confidence']}` | ECE: `{calib['ece']}`"
        )
        lines.append("")
        lines.append("| Confidence Bin | Samples | Avg Confidence | Proxy Accuracy | Gap |")
        lines.append("|---|---:|---:|---:|---:|")
        for item in calib.get("bins", []):
            lines.append(
                f"| {item['range']} | {item['samples']} | {item['avg_confidence']:.4f} | {item['proxy_accuracy']:.4f} | {item['gap']:.4f} |"
            )
    else:
        lines.append("- Calibration was not computed due to missing confidence/rating overlap.")

    lines += ["", "## Rating vs Sentiment Association", ""]
    assoc = payload.get("rating_sentiment_association", {})
    if assoc.get("samples", 0) > 0:
        lines.append(
            f"- Samples: `{assoc['samples']}` | Chi-square: `{assoc['chi_square']}` | Cramer's V: `{assoc['cramers_v']}`"
        )
        lines.append("")
        lines.append("| Rating | Negative | Neutral | Positive |")
        lines.append("|---|---:|---:|---:|")
        for rating, vals in assoc.get("contingency", {}).items():
            lines.append(
                f"| {rating} | {vals.get('negative', 0)} | {vals.get('neutral', 0)} | {vals.get('positive', 0)} |"
            )
    else:
        lines.append("- Association was not computed due to missing rating/sentiment overlap.")

    lines += ["", "## Theme Prevalence by Rating Bucket", ""]
    lines.append("| Rating | Reviews | Top Themes (theme: pct) |")
    lines.append("|---|---:|---|")
    for rating in ["1", "2", "3", "4", "5"]:
        bucket = payload.get("theme_by_rating_bucket", {}).get(rating, {"reviews": 0, "top_themes": []})
        top = ", ".join(
            f"{item['theme']}: {item['prevalence_pct']}%" for item in bucket.get("top_themes", [])[:5]
        )
        lines.append(f"| {rating} | {bucket.get('reviews', 0)} | {top or '-'} |")

    lines += ["", "## Monthly Trend Snapshot", ""]
    lines.append("| Month | Total | Neg % | Neu % | Pos % |")
    lines.append("|---|---:|---:|---:|---:|")
    for month, vals in payload.get("monthly_trends", {}).items():
        lines.append(
            f"| {month} | {vals['total']} | {vals['negative_pct']:.2f} | {vals['neutral_pct']:.2f} | {vals['positive_pct']:.2f} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deep technical review analytics.")
    parser.add_argument(
        "--mbert",
        default="output/zepto_reviews_mbert_sentiment.csv",
        help="Path to mBERT sentiment output.",
    )
    parser.add_argument(
        "--deberta",
        default="output/zepto_reviews_deberta_sentiment.csv",
        help="Path to DeBERTa sentiment output.",
    )
    parser.add_argument(
        "--baseline",
        default="output/zepto_reviews_apr2025_mar2026_sentiment.csv",
        help="Path to baseline/unspecified sentiment output.",
    )
    parser.add_argument(
        "--analysis-model",
        default="mbert",
        choices=["mbert", "deberta", "baseline"],
        help="Model used for trend/theme/association sections.",
    )
    parser.add_argument(
        "--json-out",
        default="output/deep_dive_report.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--md-out",
        default="output/deep_dive_report.md",
        help="Output Markdown path.",
    )
    args = parser.parse_args()

    model_files = {
        "mbert": Path(args.mbert),
        "deberta": Path(args.deberta),
        "baseline": Path(args.baseline),
    }

    for name, path in model_files.items():
        if not path.exists():
            raise FileNotFoundError(f"Input file for {name} not found: {path}")

    loaded = {name: load_model_file(path) for name, path in model_files.items()}
    model_rows = {name: data["rows"] for name, data in loaded.items()}

    analysis_rows = model_rows[args.analysis_model]

    payload = {
        "analysis_model": args.analysis_model,
        "analysis_row_count": len(analysis_rows),
        "compared_models": sorted(model_files.keys()),
        "input_files": {name: str(path) for name, path in model_files.items()},
        "monthly_trends": monthly_sentiment_trends(analysis_rows),
        "theme_by_rating_bucket": theme_prevalence_by_rating_bucket(analysis_rows, top_n=10),
        "pairwise_agreement": pairwise_model_agreement(model_rows),
        "multi_model_disagreement": multi_model_disagreement(model_rows),
        "calibration": confidence_calibration(analysis_rows, bins=10),
        "rating_sentiment_association": cramers_v_from_rating_sentiment(analysis_rows),
    }
    payload["top_findings"] = top_findings(payload)

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(payload, md_out)

    print(f"Wrote JSON report: {json_out}")
    print(f"Wrote Markdown report: {md_out}")


if __name__ == "__main__":
    main()
