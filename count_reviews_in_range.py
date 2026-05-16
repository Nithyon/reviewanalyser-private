from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime

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

    raise RuntimeError("Could not resolve a valid Zepto package name.")


def parse_date(date_text: str, is_end: bool) -> datetime:
    if is_end:
        return datetime.strptime(date_text, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    return datetime.strptime(date_text, "%Y-%m-%d")


def main() -> None:
    parser = argparse.ArgumentParser(description="Count Google Play reviews in a date range.")
    parser.add_argument("--app-id", default=None, help="Google Play package name")
    parser.add_argument("--country", default="in", help="Country code")
    parser.add_argument("--lang", default="en", help="Language code")
    parser.add_argument("--start", default="2025-04-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2026-03-31", help="End date YYYY-MM-DD")
    parser.add_argument("--page-size", type=int, default=200, help="Reviews per page")

    args = parser.parse_args()

    start = parse_date(args.start, is_end=False)
    end = parse_date(args.end, is_end=True)

    app_id = resolve_app_id(args.app_id, args.country, args.lang)

    continuation_token = None
    pages_fetched = 0
    rows_seen = 0
    in_range = 0
    score_counts: Counter[int] = Counter()

    while True:
        batch, continuation_token = reviews(
            app_id,
            lang=args.lang,
            country=args.country,
            sort=Sort.NEWEST,
            count=args.page_size,
            continuation_token=continuation_token,
        )

        if not batch:
            break

        pages_fetched += 1
        rows_seen += len(batch)

        oldest_in_batch = None
        for row in batch:
            at = row.get("at")
            if not isinstance(at, datetime):
                continue

            if oldest_in_batch is None or at < oldest_in_batch:
                oldest_in_batch = at

            if start <= at <= end:
                in_range += 1
                score = row.get("score")
                if isinstance(score, int):
                    score_counts[score] += 1

        if continuation_token is None:
            break

        if oldest_in_batch is not None and oldest_in_batch < start:
            break

    print(f"APP_ID={app_id}")
    print(f"DATE_RANGE={start.date()} to {end.date()}")
    print(f"PAGES_FETCHED={pages_fetched}")
    print(f"ROWS_SEEN={rows_seen}")
    print(f"TOTAL_IN_RANGE={in_range}")
    for score in sorted(score_counts):
        print(f"SCORE_{score}={score_counts[score]}")


if __name__ == "__main__":
    main()
