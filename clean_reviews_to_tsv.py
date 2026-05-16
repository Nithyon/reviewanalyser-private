import argparse
import csv
import json
from pathlib import Path


def normalize_comment(text: object) -> str:
    if text is None:
        return ""

    # Convert newlines/tabs to spaces so TSV rows stay single-line and easy to analyze.
    cleaned = str(text).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return " ".join(cleaned.split())


def convert_json_to_tsv(input_json: Path, output_tsv: Path) -> int:
    rows = json.loads(input_json.read_text(encoding="utf-8"))

    output_tsv.parent.mkdir(parents=True, exist_ok=True)

    with output_tsv.open("w", encoding="utf-8", newline="") as tsv_file:
        writer = csv.writer(tsv_file, delimiter="\t")
        writer.writerow(["User", "Rating", "Comment"])

        written = 0
        for item in rows:
            user = (item.get("userName") or "").strip()
            score = item.get("score", "")
            comment = normalize_comment(item.get("content"))

            # Skip rows with no review text.
            if not comment:
                continue

            writer.writerow([user, score, comment])
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Zepto review JSON into a clean TSV with User, Rating, Comment columns."
    )
    parser.add_argument(
        "--input-json",
        default="output/zepto_reviews.json",
        help="Input review JSON path (default: output/zepto_reviews.json)",
    )
    parser.add_argument(
        "--output-tsv",
        default="output/zepto_reviews.tsv",
        help="Output TSV path (default: output/zepto_reviews.tsv)",
    )

    args = parser.parse_args()

    input_json = Path(args.input_json)
    output_tsv = Path(args.output_tsv)

    if not input_json.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_json}")

    count = convert_json_to_tsv(input_json, output_tsv)
    print(f"TSV saved to: {output_tsv}")
    print(f"Rows written: {count}")


if __name__ == "__main__":
    main()
