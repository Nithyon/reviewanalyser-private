#!/usr/bin/env python3
import argparse
from pathlib import Path

def normalize_cell(value: str) -> str:
    """Normalize cell content: remove newlines/tabs and collapse extra spaces."""
    if not value:
        return ""
    text = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return " ".join(text.split()).strip()

def repair_tsv(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_read = 0
    rows_written = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as infile, \
         output_path.open("w", encoding="utf-8-sig", newline="") as outfile:
        
        # 1. Read and write the header
        header_line = infile.readline()
        if not header_line:
            print("Error: Input file is empty.")
            return
        
        outfile.write(header_line)
        fieldnames = header_line.rstrip("\r\n").split("\t")
        expected_cols = len(fieldnames)
        
        # We assume replyContent is at index 6 based on your TSV structure
        # (reviewId, userName, score, at, content, thumbsUpCount, replyContent...)
        reply_idx = 6 

        buffer = ""
        for raw_line in infile:
            if not raw_line.strip() and not buffer:
                continue

            buffer += raw_line
            parts = buffer.rstrip("\r\n").split("\t")

            # Accumulate until we have at least expected columns
            if len(parts) < expected_cols:
                continue

            # If we have too many columns, it's likely because the replyContent
            # itself contained tabs. We merge the "middle" extra columns back into reply_idx.
            if len(parts) > expected_cols:
                leading = parts[:reply_idx]
                trailing_count = expected_cols - reply_idx - 1
                trailing = parts[-trailing_count:] if trailing_count > 0 else []
                # Merge everything in the middle as the reply
                middle = " ".join(parts[reply_idx : len(parts) - trailing_count])
                parts = leading + [middle] + trailing

            # Final normalization to ensure no literal newlines remain inside the cell
            fixed_parts = [normalize_cell(p) for p in parts]
            outfile.write("\t".join(fixed_parts) + "\n")
            
            rows_written += 1
            rows_read += 1
            buffer = ""

            if rows_written % 10000 == 0:
                print(f"Processed {rows_written} rows...")

    print("\nTSV repair complete")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Rows processed: {rows_written}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Robust repair of Zepto TSVs with multi-line replies.")
    parser.add_argument("--input", required=True, help="Input TSV path")
    parser.add_argument("--output", required=True, help="Output TSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    repair_tsv(input_path, output_path)

if __name__ == "__main__":
    main()
