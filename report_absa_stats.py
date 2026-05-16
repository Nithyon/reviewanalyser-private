#!/usr/bin/env python3
"""Generate ABSA statistics and hypothesis report.

Reads Jina AI ABSA output and produces:
- JSON summary with all metrics
- Markdown report covering H1-H6 hypotheses

Can also compare ABSA results against rule-based detected_themes.
"""

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def detect_delimiter(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def load_rows(path: Path, max_rows: int | None = None) -> list[dict]:
    delimiter = detect_delimiter(path)
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)
            if max_rows and len(rows) >= max_rows:
                break
    return rows


def safe_float(val: str) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def generate_report(
    input_path: Path,
    output_prefix: Path,
) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_json = output_prefix.with_suffix(".json")
    output_md = output_prefix.with_name(f"{output_prefix.name}.md")

    rows = load_rows(input_path)
    total = len(rows)
    if total == 0:
        print("No data rows found.")
        return

    columns = list(rows[0].keys())
    has_sentiment = "sentiment_label" in columns
    has_themes = "detected_themes" in columns
    has_aspect = "jina_aspect" in columns
    has_confidence = "jina_aspect_confidence" in columns
    has_rating = any(c.lower() in ("rating", "score") for c in columns)
    has_date = any(c.lower() in ("date", "created_iso", "at") for c in columns)

    rating_col = next((c for c in columns if c.lower() in ("rating", "score")), None)
    date_col = next((c for c in columns if c.lower() in ("date", "created_iso", "at")), None)

    # ── 1. Aspect distribution ───────────────────────────────────────────
    aspect_counts = Counter()
    aspect_sentiment: dict[str, Counter] = {}
    aspect_ratings: dict[str, list[float]] = {}
    monthly_aspects: dict[str, Counter] = {}
    confidence_values: list[float] = []
    theme_aspect_overlap: dict[str, dict[str, int]] = {}

    for row in rows:
        aspect = row.get("jina_aspect", "Unknown")
        sentiment = row.get("sentiment_label", "unknown")
        confidence = safe_float(row.get("jina_aspect_confidence", "0"))
        rating = safe_float(row.get(rating_col, "")) if rating_col else None
        themes = [t.strip() for t in (row.get("detected_themes", "") or "").split(";") if t.strip()]

        aspect_counts[aspect] += 1

        if aspect not in aspect_sentiment:
            aspect_sentiment[aspect] = Counter()
        aspect_sentiment[aspect][sentiment] += 1

        if confidence is not None:
            confidence_values.append(confidence)

        if rating is not None:
            if aspect not in aspect_ratings:
                aspect_ratings[aspect] = []
            aspect_ratings[aspect].append(rating)

        # Monthly trends
        if date_col:
            date_str = row.get(date_col, "")
            month = (date_str or "")[:7]  # YYYY-MM
            if month and len(month) >= 7:
                if month not in monthly_aspects:
                    monthly_aspects[month] = Counter()
                monthly_aspects[month][aspect] += 1

        # Theme vs aspect comparison
        if has_themes and themes:
            for theme in themes:
                if theme not in theme_aspect_overlap:
                    theme_aspect_overlap[theme] = {}
                theme_aspect_overlap[theme][aspect] = theme_aspect_overlap[theme].get(aspect, 0) + 1

    # ── 2. Compute hypothesis metrics ─────────────────────────────────────
    hypotheses = {}

    # H1: ABSA vs overall sentiment — aspect-level granularity improvement
    if has_aspect:
        classified = sum(1 for r in rows if r.get("jina_aspect", "Unknown") != "Unknown")
        multi_aspect_reviews = sum(
            1 for r in rows
            if r.get("jina_aspect", "Unknown") != "Unknown"
            and len([t for t in (r.get("detected_themes", "") or "").split(";") if t.strip()]) > 1
        )
        hypotheses["H1_ABSA_improvement"] = {
            "description": "ABSA provides aspect-level granularity vs overall sentiment",
            "total_reviews": total,
            "reviews_with_aspect": classified,
            "classification_rate": round(classified / total * 100, 2),
            "reviews_with_multiple_themes": multi_aspect_reviews,
            "granularity_gain_pct": round(multi_aspect_reviews / max(classified, 1) * 100, 2),
        }

    # H2: Delivery speed → customer sentiment
    delivery_aspects = [r for r in rows if "delivery" in (r.get("jina_aspect", "") or "").lower()]
    if delivery_aspects:
        delivery_pos = sum(1 for r in delivery_aspects if r.get("sentiment_label") == "positive")
        delivery_neg = sum(1 for r in delivery_aspects if r.get("sentiment_label") == "negative")
        delivery_ratings = [safe_float(r.get(rating_col, "")) for r in delivery_aspects if rating_col]
        delivery_ratings = [r for r in delivery_ratings if r is not None]
        hypotheses["H2_delivery_speed_impact"] = {
            "description": "Delivery speed has significant positive impact on customer sentiment",
            "total_delivery_reviews": len(delivery_aspects),
            "positive_pct": round(delivery_pos / len(delivery_aspects) * 100, 2),
            "negative_pct": round(delivery_neg / len(delivery_aspects) * 100, 2),
            "avg_rating": round(sum(delivery_ratings) / max(len(delivery_ratings), 1), 2),
            "sentiment_ratio": round(delivery_pos / max(delivery_neg, 1), 4),
        }

    # H3: Pricing → negative sentiment
    pricing_aspects = [r for r in rows if "pricing" in (r.get("jina_aspect", "") or "").lower()]
    if pricing_aspects:
        pricing_neg = sum(1 for r in pricing_aspects if r.get("sentiment_label") == "negative")
        pricing_pos = sum(1 for r in pricing_aspects if r.get("sentiment_label") == "positive")
        hypotheses["H3_pricing_negative_sentiment"] = {
            "description": "Pricing perception significantly influences negative sentiment",
            "total_pricing_reviews": len(pricing_aspects),
            "negative_pct": round(pricing_neg / len(pricing_aspects) * 100, 2),
            "positive_pct": round(pricing_pos / len(pricing_aspects) * 100, 2),
            "negative_dominance": pricing_neg > pricing_pos,
        }

    # H4: Customer service → brand sentiment
    service_aspects = [r for r in rows if "service" in (r.get("jina_aspect", "") or "").lower() or "support" in (r.get("jina_aspect", "") or "").lower()]
    if service_aspects:
        service_pos = sum(1 for r in service_aspects if r.get("sentiment_label") == "positive")
        service_neg = sum(1 for r in service_aspects if r.get("sentiment_label") == "negative")
        service_ratings = [safe_float(r.get(rating_col, "")) for r in service_aspects if rating_col]
        service_ratings = [r for r in service_ratings if r is not None]
        hypotheses["H4_customer_service_quality"] = {
            "description": "Customer service quality positively affects brand sentiment",
            "total_service_reviews": len(service_aspects),
            "positive_pct": round(service_pos / len(service_aspects) * 100, 2),
            "negative_pct": round(service_neg / len(service_aspects) * 100, 2),
            "avg_rating": round(sum(service_ratings) / max(len(service_ratings), 1), 2),
        }

    # H5: Social media sentiment → customer satisfaction proxy
    if has_rating and rating_col:
        all_ratings = [safe_float(r.get(rating_col, "")) for r in rows]
        all_ratings = [r for r in all_ratings if r is not None]
        sentiments = Counter(r.get("sentiment_label", "unknown") for r in rows)
        hypotheses["H5_social_media_sentiment_satisfaction"] = {
            "description": "Social media sentiment predicts customer satisfaction levels",
            "avg_rating": round(sum(all_ratings) / max(len(all_ratings), 1), 2) if all_ratings else None,
            "sentiment_distribution": dict(sentiments),
            "correlation_direction": "positive" if sentiments.get("positive", 0) > sentiments.get("negative", 0) else "negative",
        }

    # H6: AI-driven social listening → marketing decision effectiveness
    if has_aspect and has_themes:
        reviews_with_themes = sum(1 for r in rows if (r.get("detected_themes", "") or "").strip())
        reviews_with_aspects = sum(1 for r in rows if (r.get("jina_aspect", "Unknown")) != "Unknown")
        hypotheses["H6_ai_social_listening"] = {
            "description": "AI-driven social listening improves insight generation vs rule-based",
            "rule_based_coverage": round(reviews_with_themes / total * 100, 2),
            "absa_coverage": round(reviews_with_aspects / total * 100, 2),
            "coverage_improvement_pct": round(
                (reviews_with_aspects - reviews_with_themes) / max(reviews_with_themes, 1) * 100, 2
            ),
            "unique_aspects_identified": len(aspect_counts),
        }

    # ── 3. Build report ──────────────────────────────────────────────────
    report = {
        "input_file": str(input_path),
        "total_rows": total,
        "aspect_distribution": dict(aspect_counts.most_common()),
        "aspect_sentiment_crosstab": {
            k: dict(v) for k, v in aspect_sentiment.items()
        },
        "aspect_avg_ratings": {
            k: round(sum(v) / len(v), 2) for k, v in aspect_ratings.items()
        } if aspect_ratings else {},
        "confidence_stats": {
            "mean": round(sum(confidence_values) / max(len(confidence_values), 1), 4),
            "min": round(min(confidence_values), 4) if confidence_values else 0,
            "max": round(max(confidence_values), 4) if confidence_values else 0,
        },
        "theme_aspect_overlap": theme_aspect_overlap,
        "monthly_trends": {m: dict(v) for m, v in sorted(monthly_aspects.items())},
        "hypotheses": hypotheses,
    }

    with output_json.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── 4. Markdown report ────────────────────────────────────────────────
    md_lines = [
        "# ABSA Statistics Report",
        f"**Source**: `{input_path.name}`  ",
        f"**Total Reviews**: {total}  ",
        "",
        "---",
        "",
        "## 1. Aspect Distribution",
        "",
        "| Aspect | Count | % |",
        "|--------|------:|--:|",
    ]
    for aspect, count in aspect_counts.most_common():
        pct = count / total * 100
        md_lines.append(f"| {aspect} | {count} | {pct:.1f}% |")

    md_lines += ["", "## 2. Aspect × Sentiment Cross-tabulation", ""]
    md_lines.append("| Aspect | Positive | Neutral | Negative |")
    md_lines.append("|--------|--------:|--------:|---------:|")
    for aspect in sorted(aspect_sentiment.keys()):
        sc = aspect_sentiment[aspect]
        md_lines.append(
            f"| {aspect} | {sc.get('positive', 0)} | {sc.get('neutral', 0)} | {sc.get('negative', 0)} |"
        )

    if aspect_ratings:
        md_lines += ["", "## 3. Aspect Average Ratings", ""]
        md_lines.append("| Aspect | Avg Rating | # Reviews |")
        md_lines.append("|--------|----------:|---------:|")
        for aspect, ratings in sorted(aspect_ratings.items(), key=lambda x: sum(x[1])/len(x[1])):
            md_lines.append(f"| {aspect} | {sum(ratings)/len(ratings):.2f} | {len(ratings)} |")

    md_lines += ["", "## 4. Hypothesis Testing Results", ""]
    for h_key, h_data in hypotheses.items():
        md_lines.append(f"### {h_key}")
        md_lines.append(f"**{h_data['description']}**")
        md_lines.append("")
        for k, v in h_data.items():
            if k != "description":
                md_lines.append(f"- **{k}**: {v}")
        md_lines.append("")

    if confidence_values:
        md_lines += [
            "## 5. Model Confidence",
            "",
            f"- **Mean confidence**: {report['confidence_stats']['mean']:.4f}",
            f"- **Min confidence**: {report['confidence_stats']['min']:.4f}",
            f"- **Max confidence**: {report['confidence_stats']['max']:.4f}",
            "",
        ]

    if monthly_aspects:
        md_lines += ["## 6. Monthly Aspect Trends", ""]
        months = sorted(monthly_aspects.keys())
        all_aspects_list = sorted(set(a for mc in monthly_aspects.values() for a in mc))
        header = "| Month | " + " | ".join(all_aspects_list) + " |"
        sep = "|-------|" + "|".join(["------:" for _ in all_aspects_list]) + "|"
        md_lines.append(header)
        md_lines.append(sep)
        for month in months:
            mc = monthly_aspects[month]
            vals = " | ".join(str(mc.get(a, 0)) for a in all_aspects_list)
            md_lines.append(f"| {month} | {vals} |")
        md_lines.append("")

    if theme_aspect_overlap:
        md_lines += ["## 7. Rule-Based Themes vs ABSA Aspects", ""]
        md_lines.append("| Rule-Based Theme | Top ABSA Aspect | Agreement Count |")
        md_lines.append("|-----------------|----------------|---------------:|")
        for theme, aspects in sorted(theme_aspect_overlap.items()):
            top_aspect = max(aspects, key=aspects.get)
            md_lines.append(f"| {theme} | {top_aspect} | {aspects[top_aspect]} |")
        md_lines.append("")

    with output_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Stats JSON: {output_json}")
    print(f"Stats Report: {output_md}")
    print(f"Hypotheses covered: {list(hypotheses.keys())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ABSA statistics and hypothesis report")
    parser.add_argument("--input", required=True, help="ABSA-enriched CSV/TSV file")
    parser.add_argument(
        "--output-prefix",
        default="output/absa_stats_report",
        help="Output file prefix",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    generate_report(input_path, Path(args.output_prefix))


if __name__ == "__main__":
    main()
