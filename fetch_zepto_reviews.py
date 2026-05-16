import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from google_play_scraper import Sort, app, reviews, search


DEFAULT_CANDIDATE_APP_IDS = [
    "com.zeptoconsumerapp",
    "com.zepto.buyer",
    "com.zepto.user",
]


def resolve_app_id(explicit_app_id: str | None, country: str, lang: str) -> str:
    if explicit_app_id:
        app(explicit_app_id, lang=lang, country=country)
        return explicit_app_id

    for app_id in DEFAULT_CANDIDATE_APP_IDS:
        try:
            app(app_id, lang=lang, country=country)
            return app_id
        except Exception:
            continue

    results = search("Zepto", lang=lang, country=country, n_hits=20)
    for result in results:
        found_id = result.get("appId", "")
        title = (result.get("title", "") or "").lower()
        if "zepto" in found_id.lower() or "zepto" in title:
            try:
                app(found_id, lang=lang, country=country)
                return found_id
            except Exception:
                continue

    raise RuntimeError(
        "Could not resolve a valid Zepto package name. "
        "Pass --app-id explicitly if needed."
    )


def parse_date(date_text: str, is_end: bool) -> datetime:
    parsed = datetime.strptime(date_text, "%Y-%m-%d")
    if is_end:
        return parsed.replace(hour=23, minute=59, second=59)
    return parsed


def fetch_reviews(
    app_id: str, count: int, lang: str, country: str, page_size: int
) -> list[dict[str, Any]]:
    all_reviews: list[dict[str, Any]] = []
    token = None

    while len(all_reviews) < count:
        batch_size = min(200, page_size, count - len(all_reviews))
        batch, token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=token,
        )
        if not batch:
            break

        all_reviews.extend(batch)

        if token is None:
            break

    return all_reviews[:count]


def fetch_reviews_in_range(
    app_id: str,
    start: datetime,
    end: datetime,
    lang: str,
    country: str,
    page_size: int,
) -> list[dict[str, Any]]:
    all_reviews: list[dict[str, Any]] = []
    token = None

    while True:
        batch, token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=min(200, page_size),
            continuation_token=token,
        )
        if not batch:
            break

        oldest_in_batch = None
        for item in batch:
            at = item.get("at")
            if not isinstance(at, datetime):
                continue

            if oldest_in_batch is None or at < oldest_in_batch:
                oldest_in_batch = at

            if start <= at <= end:
                all_reviews.append(item)

        if token is None:
            break

        if oldest_in_batch is not None and oldest_in_batch < start:
            break

    return all_reviews


def build_output_row(item: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for field in fields:
        value = item.get(field, "")
        if isinstance(value, datetime):
            row[field] = value.isoformat()
        elif value is None:
            row[field] = ""
        else:
            row[field] = value
    return row


def save_outputs(
    reviews_data: list[dict[str, Any]], output_prefix: Path
) -> tuple[Path, Path, Path]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")
    tsv_path = output_prefix.with_suffix(".tsv")

    with json_path.open("w", encoding="utf-8") as jf:
        json.dump(reviews_data, jf, ensure_ascii=False, indent=2, default=str)

    csv_fields = [
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

    with csv_path.open("w", newline="", encoding="utf-8") as cf, tsv_path.open(
        "w", newline="", encoding="utf-8"
    ) as tf:
        csv_writer = csv.DictWriter(cf, fieldnames=csv_fields)
        tsv_writer = csv.DictWriter(tf, fieldnames=csv_fields, delimiter="\t")
        csv_writer.writeheader()
        tsv_writer.writeheader()
        for item in reviews_data:
            row = build_output_row(item, csv_fields)
            csv_writer.writerow(row)
            tsv_writer.writerow(row)

    return json_path, csv_path, tsv_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Zepto reviews from Google Play and save JSON/CSV/TSV outputs."
    )
    parser.add_argument("--app-id", default=None, help="Explicit Google Play package name")
    parser.add_argument(
        "--count",
        type=int,
        default=300,
        help="Number of reviews to fetch (default: 300). Ignored when a date range is provided.",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Start date YYYY-MM-DD. Must be used with --end-date.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date YYYY-MM-DD. Must be used with --start-date.",
    )
    parser.add_argument("--lang", default="en", help="Language code, e.g. en")
    parser.add_argument("--country", default="in", help="Country code, e.g. in")
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        help="Reviews per page (default: 200).",
    )
    parser.add_argument(
        "--output-prefix",
        default="output/zepto_reviews",
        help="Output path without extension (default: output/zepto_reviews)",
    )

    args = parser.parse_args()

    if args.page_size <= 0:
        raise ValueError("--page-size must be > 0")

    if bool(args.start_date) != bool(args.end_date):
        raise ValueError("--start-date and --end-date must be provided together")

    app_id = resolve_app_id(args.app_id, args.country, args.lang)

    start = None
    end = None
    if args.start_date and args.end_date:
        start = parse_date(args.start_date, is_end=False)
        end = parse_date(args.end_date, is_end=True)
        if start > end:
            raise ValueError("--start-date must be earlier than or equal to --end-date")

        reviews_data = fetch_reviews_in_range(
            app_id, start, end, args.lang, args.country, args.page_size
        )
    else:
        reviews_data = fetch_reviews(
            app_id, args.count, args.lang, args.country, args.page_size
        )

    json_path, csv_path, tsv_path = save_outputs(reviews_data, Path(args.output_prefix))

    print(f"Resolved app id: {app_id}")
    if start and end:
        print(f"Date range: {start.date()} to {end.date()}")
    print(f"Fetched reviews: {len(reviews_data)}")
    print(f"JSON saved to: {json_path}")
    print(f"CSV saved to: {csv_path}")
    print(f"TSV saved to: {tsv_path}")


if __name__ == "__main__":
    main()
