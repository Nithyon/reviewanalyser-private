#!/usr/bin/env python3
import argparse
import csv
from datetime import datetime
from pathlib import Path

TARGET_HEADERS = [
    "Review_ID",
    "Author",
    "Rating",
    "Date",
    "Review_Content",
    "Thumbs_Up",
    "Official_Reply",
    "Reply_Date",
    "App_Version",
]

SOURCE_HEADER_FALLBACK = [
    "reviewId",
    "userName",
    "score",
    "at",
    "content",
    "thumbsUpCount",
    "replyContent",
    "repliedAt",
    "appVersion",
]

HEADER_MAP = {
    "reviewid": "Review_ID",
    "username": "Author",
    "score": "Rating",
    "at": "Date",
    "content": "Review_Content",
    "thumbsupcount": "Thumbs_Up",
    "replycontent": "Official_Reply",
    "repliedat": "Reply_Date",
    "appversion": "App_Version",
    "review_id": "Review_ID",
    "author": "Author",
    "rating": "Rating",
    "date": "Date",
    "review_content": "Review_Content",
    "thumbs_up": "Thumbs_Up",
    "official_reply": "Official_Reply",
    "reply_date": "Reply_Date",
    "app_version": "App_Version",
}


def norm_key(name: str) -> str:
    return "".join(ch for ch in (name or "").strip().lower() if ch.isalnum() or ch == "_")


def normalize_timestamp(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    candidates = [text, text.replace("Z", "+00:00")]
    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue

    return text


def repair_extra_columns(row: list[str], expected_cols: int) -> list[str] | None:
    if len(row) == expected_cols:
        return row
    if len(row) < expected_cols:
        return None

    # Keep first 6 columns fixed, keep last two as Reply_Date and App_Version,
    # merge everything between into Official_Reply.
    if expected_cols >= 9:
        return row[:6] + ["\n".join(row[6:-2])] + row[-2:]
    return None


def map_row(source_header: list[str], row: list[str], index: int) -> dict[str, str]:
    source = {}
    for i, key in enumerate(source_header):
        source[key] = row[i] if i < len(row) else ""

    out = {key: "" for key in TARGET_HEADERS}
    for src_key, value in source.items():
        mapped = HEADER_MAP.get(norm_key(src_key))
        if mapped:
            out[mapped] = value

    if not out["Review_ID"]:
        out["Review_ID"] = f"AUTO_{index}"

    out["Date"] = normalize_timestamp(out["Date"])
    out["Reply_Date"] = normalize_timestamp(out["Reply_Date"])
    return out


def prepare_nvivo_tsv(input_path: Path, output_path: Path) -> None:
    total_data_rows = 0
    written_rows = 0
    skipped: list[tuple[int, str]] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile, output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as outfile:
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.DictWriter(outfile, fieldnames=TARGET_HEADERS, delimiter="\t", quoting=csv.QUOTE_MINIMAL)

        try:
            header = next(reader)
        except StopIteration:
            writer.writeheader()
            print("Validation Summary")
            print("Total row count: 0")
            print("Rows written: 0")
            print("Rows skipped due to formatting errors: 0")
            return

        if not header:
            header = SOURCE_HEADER_FALLBACK

        expected_cols = len(header)
        writer.writeheader()

        pending_row = None
        pending_row_num = None

        for line_num, row in enumerate(reader, start=2):
            total_data_rows += 1

            if pending_row is not None:
                # Repair short row by appending next row's first cell into previous
                # last cell with newline, then extending with remaining cells.
                first_cell = row[0] if row else ""
                pending_row[-1] = f"{pending_row[-1]}\n{first_cell}" if pending_row[-1] else first_cell
                if len(row) > 1:
                    pending_row.extend(row[1:])
                row = pending_row
                line_num = pending_row_num if pending_row_num is not None else line_num
                pending_row = None
                pending_row_num = None

            if len(row) < expected_cols:
                pending_row = row
                pending_row_num = line_num
                continue

            if len(row) > expected_cols:
                repaired = repair_extra_columns(row, expected_cols)
                if repaired is None:
                    skipped.append((line_num, f"column_count={len(row)} expected={expected_cols}"))
                    continue
                row = repaired

            if len(row) != expected_cols:
                skipped.append((line_num, f"column_count={len(row)} expected={expected_cols}"))
                continue

            out_row = map_row(header, row, written_rows + 1)
            writer.writerow(out_row)
            written_rows += 1

        if pending_row is not None:
            skipped.append((pending_row_num or 0, "incomplete trailing row"))

    print("Validation Summary")
    print(f"Total row count: {total_data_rows}")
    print(f"Rows written: {written_rows}")
    print(f"Rows skipped due to formatting errors: {len(skipped)}")
    if skipped:
        print("First 20 skipped rows (line_number: reason):")
        for line, reason in skipped[:20]:
            print(f"{line}: {reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Zepto TSV for NVivo import")
    parser.add_argument("--input", required=True, help="Input TSV path")
    parser.add_argument("--output", required=True, help="Output TSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    prepare_nvivo_tsv(input_path, output_path)


if __name__ == "__main__":
    main()
