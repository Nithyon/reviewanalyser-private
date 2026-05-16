from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

REDDIT_BASE_URL = "https://www.reddit.com"
SEARCH_ENDPOINT = f"{REDDIT_BASE_URL}/search.json"
PULLPUSH_ENDPOINT = "https://api.pullpush.io/reddit/search/submission/"
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
PREDEFINED_QUERY_SETS: dict[str, list[str]] = {
    "zepto-expanded": [
        "zepto",
        '"zepto app" OR "zepto delivery" OR "zepto now" OR zeptonow',
        '"zepto refund" OR "zepto support" OR "zepto customer care"',
        '"zepto late delivery" OR "zepto missing item" OR "zepto cancellation"',
        '"zepto vs blinkit" OR "zepto vs instamart" OR "zepto vs bigbasket"',
        "#zepto OR zeptonow",
    ]
}


@dataclass
class Config:
    query: str
    days: int
    start_date: str | None
    end_date: str | None
    max_pages: int
    limit_per_page: int
    request_delay_seconds: float
    timeout_seconds: int
    out_dir: Path
    output_prefix: str
    user_agent: str
    max_request_attempts: int
    retry_backoff_seconds: float
    use_month_slices: bool
    provider: str
    query_set: str | None
    query_file: str | None


class TemporaryRequestError(RuntimeError):
    pass


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Reddit posts matching a query (global search, no OAuth), "
            "with date window support."
        )
    )
    parser.add_argument(
        "--query",
        default='zepto OR "zepto app" OR "zepto delivery"',
        help="Reddit search query (global search).",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help=(
            "Start of date window in UTC. Supports YYYY-MM-DD or ISO datetime "
            "(e.g., 2026-03-01 or 2026-03-01T00:00:00+00:00)."
        ),
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help=(
            "End of date window in UTC. Supports YYYY-MM-DD or ISO datetime "
            "(e.g., 2026-03-12 or 2026-03-12T23:59:59+00:00)."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help=(
            "Fallback lookback window in days when start/end are not fully provided. "
            "If both start and end are provided, this is ignored."
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum paginated requests.",
    )
    parser.add_argument(
        "--limit-per-page",
        type=int,
        default=100,
        choices=[10, 25, 50, 100],
        help="Posts per request.",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=1.0,
        help="Delay between successful page requests.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="HTTP timeout per request.",
    )
    parser.add_argument("--out-dir", default="output", help="Output directory.")
    parser.add_argument(
        "--output-prefix",
        default="reddit_zepto_posts",
        help="Output file prefix (without extension).",
    )
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (compatible; ZeptoRedditFetcher/2.0)",
        help="User-Agent header.",
    )
    parser.add_argument(
        "--max-request-attempts",
        type=int,
        default=6,
        help="Maximum attempts per HTTP request including retries.",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=1.5,
        help="Base exponential backoff in seconds for request retries.",
    )
    parser.add_argument(
        "--no-month-slices",
        action="store_true",
        help="Disable month-wise date slices and run one broad query window.",
    )
    parser.add_argument(
        "--provider",
        default="reddit",
        choices=["reddit", "pullpush"],
        help="Data source provider. Use pullpush for broader historical retrieval.",
    )
    parser.add_argument(
        "--query-set",
        default=None,
        choices=sorted(PREDEFINED_QUERY_SETS.keys()),
        help="Use a predefined multi-query expansion set and merge unique posts.",
    )
    parser.add_argument(
        "--query-file",
        default=None,
        help="Path to a text file with one query per line. Blank lines and # comments are ignored.",
    )

    args = parser.parse_args()

    if args.days <= 0:
        raise ValueError("--days must be > 0")
    if args.max_pages <= 0:
        raise ValueError("--max-pages must be > 0")
    if args.max_request_attempts <= 0:
        raise ValueError("--max-request-attempts must be > 0")
    if args.retry_backoff_seconds <= 0:
        raise ValueError("--retry-backoff-seconds must be > 0")
    if args.query_set and args.query_file:
        raise ValueError("Use either --query-set or --query-file, not both.")

    return Config(
        query=args.query,
        days=args.days,
        start_date=args.start_date,
        end_date=args.end_date,
        max_pages=args.max_pages,
        limit_per_page=args.limit_per_page,
        request_delay_seconds=args.request_delay_seconds,
        timeout_seconds=args.timeout_seconds,
        out_dir=Path(args.out_dir),
        output_prefix=args.output_prefix,
        user_agent=args.user_agent,
        max_request_attempts=args.max_request_attempts,
        retry_backoff_seconds=args.retry_backoff_seconds,
        use_month_slices=not args.no_month_slices,
        provider=args.provider,
        query_set=args.query_set,
        query_file=args.query_file,
    )


def resolve_query_list(config: Config) -> list[str]:
    if config.query_file:
        query_path = Path(config.query_file)
        if not query_path.exists():
            raise FileNotFoundError(f"Query file not found: {query_path}")

        queries: list[str] = []
        for line in query_path.read_text(encoding="utf-8").splitlines():
            q = line.strip()
            if not q or q.startswith("#"):
                continue
            queries.append(q)
    elif config.query_set:
        queries = PREDEFINED_QUERY_SETS[config.query_set]
    else:
        queries = [config.query]

    # Deduplicate while preserving order.
    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        if query in seen:
            continue
        seen.add(query)
        deduped.append(query)

    if not deduped:
        raise ValueError("No queries resolved. Check --query or query source.")

    return deduped


def post_key(row: dict[str, Any]) -> str | None:
    post_id = row.get("id")
    if post_id:
        return f"id:{post_id}"
    name = row.get("name")
    if name:
        return f"name:{name}"
    permalink = row.get("permalink")
    if permalink:
        return f"permalink:{permalink}"
    return None


def next_month_boundary(dt: datetime) -> datetime:
    if dt.month == 12:
        return datetime(dt.year + 1, 1, 1, tzinfo=timezone.utc)
    return datetime(dt.year, dt.month + 1, 1, tzinfo=timezone.utc)


def build_month_windows(start_dt: datetime, end_dt: datetime) -> list[tuple[datetime, datetime]]:
    windows: list[tuple[datetime, datetime]] = []
    cursor = datetime(start_dt.year, start_dt.month, 1, tzinfo=timezone.utc)

    while cursor <= end_dt:
        month_end = next_month_boundary(cursor) - timedelta(microseconds=1)
        window_start = max(start_dt, cursor)
        window_end = min(end_dt, month_end)

        if window_start <= window_end:
            windows.append((window_start, window_end))

        cursor = next_month_boundary(cursor)

    return windows


def build_windowed_query(base_query: str, start_epoch: float, end_epoch: float) -> str:
    return (
        f"({base_query}) AND timestamp:{int(start_epoch)}..{int(end_epoch)}"
    )


def parse_datetime_utc(value: str, *, is_end: bool) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("Date value cannot be empty")

    if DATE_ONLY_RE.match(text):
        dt = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if is_end:
            dt = dt + timedelta(days=1) - timedelta(microseconds=1)
        return dt

    normalized = text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def resolve_date_window(config: Config) -> tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc)

    start_dt = (
        parse_datetime_utc(config.start_date, is_end=False) if config.start_date else None
    )
    end_dt = parse_datetime_utc(config.end_date, is_end=True) if config.end_date else None

    if start_dt is None and end_dt is None:
        end_dt = now_utc
        start_dt = end_dt - timedelta(days=config.days)
    elif start_dt is None and end_dt is not None:
        start_dt = end_dt - timedelta(days=config.days)
    elif start_dt is not None and end_dt is None:
        end_dt = now_utc

    if start_dt is None or end_dt is None:
        raise RuntimeError("Failed to resolve date window")

    if start_dt > end_dt:
        raise ValueError("--start-date must be earlier than or equal to --end-date")

    return start_dt, end_dt


def build_session(user_agent: str) -> requests.Session:
    session = requests.Session()

    # Keep adapter-level retries small; request-level retries below handle full robustness.
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.5,
        status_forcelist=sorted(RETRYABLE_STATUS_CODES),
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
    return session


def to_iso(epoch: float | None) -> str:
    if not epoch:
        return ""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def normalize_post(data: dict[str, Any]) -> dict[str, Any]:
    created_utc = data.get("created_utc")
    permalink = data.get("permalink") or ""
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "title": data.get("title") or "",
        "subreddit": data.get("subreddit") or "",
        "author": data.get("author") or "",
        "created_utc": created_utc,
        "created_iso": to_iso(created_utc),
        "score": data.get("score"),
        "upvote_ratio": data.get("upvote_ratio"),
        "num_comments": data.get("num_comments"),
        "url": data.get("url") or "",
        "permalink": urljoin(REDDIT_BASE_URL, permalink),
        "domain": data.get("domain") or "",
        "is_self": data.get("is_self"),
        "selftext": data.get("selftext") or "",
    }


def request_json_with_retry(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any],
    timeout_seconds: int,
    max_attempts: int,
    backoff_seconds: float,
) -> dict[str, Any]:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(url, params=params, timeout=timeout_seconds)

            if 200 <= response.status_code < 300:
                return response.json()

            if response.status_code in RETRYABLE_STATUS_CODES:
                raise TemporaryRequestError(f"Retryable status code: {response.status_code}")

            snippet = response.text[:300].replace("\n", " ")
            raise RuntimeError(f"Request failed ({response.status_code}): {snippet}")

        except (
            requests.RequestException,
            json.JSONDecodeError,
            TemporaryRequestError,
        ) as exc:
            last_error = exc
            if attempt >= max_attempts:
                break

            sleep_seconds = backoff_seconds * (2 ** (attempt - 1))
            print(
                f"Request attempt {attempt}/{max_attempts} failed: {exc}. "
                f"Retrying in {sleep_seconds:.1f}s..."
            )
            time.sleep(sleep_seconds)

    raise RuntimeError(f"Request failed after {max_attempts} attempts: {last_error}")


def fetch_page(
    session: requests.Session,
    query: str,
    limit: int,
    after: str | None,
    timeout_seconds: int,
    max_attempts: int,
    backoff_seconds: float,
) -> dict[str, Any]:
    params = {
        "q": query,
        "sort": "new",
        "t": "all",  # Full history window on Reddit side.
        "syntax": "cloudsearch",
        "limit": limit,
        "raw_json": 1,
        "type": "link",
        "restrict_sr": "false",  # Global (not subreddit-restricted) search.
    }
    if after:
        params["after"] = after

    payload = request_json_with_retry(
        session,
        SEARCH_ENDPOINT,
        params=params,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    if "data" not in payload:
        raise RuntimeError("Unexpected response shape from Reddit endpoint")
    return payload["data"]


def fetch_posts(
    config: Config,
    start_dt: datetime,
    end_dt: datetime,
    query: str,
) -> list[dict[str, Any]]:
    if config.provider == "pullpush":
        return fetch_posts_pullpush(config, start_dt, end_dt, query)

    session = build_session(config.user_agent)

    all_posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    if config.use_month_slices:
        windows = build_month_windows(start_dt, end_dt)
    else:
        windows = [(start_dt, end_dt)]

    print(f"Active query windows: {len(windows)}")

    for window_idx, (window_start, window_end) in enumerate(windows, start=1):
        window_start_epoch = window_start.timestamp()
        window_end_epoch = window_end.timestamp()
        window_query = (
            build_windowed_query(query, window_start_epoch, window_end_epoch)
            if config.use_month_slices
            else query
        )

        after: str | None = None
        pages = 0

        while pages < config.max_pages:
            pages += 1
            data = fetch_page(
                session=session,
                query=window_query,
                limit=config.limit_per_page,
                after=after,
                timeout_seconds=config.timeout_seconds,
                max_attempts=config.max_request_attempts,
                backoff_seconds=config.retry_backoff_seconds,
            )

            children = data.get("children", [])
            if not children:
                print(f"Window {window_idx}: page {pages}: no results, stopping.")
                break

            page_timestamps: list[float] = []
            kept = 0
            newer_than_end = 0
            older_than_start = 0

            for child in children:
                raw = child.get("data", {})
                post_id = raw.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                created_utc = raw.get("created_utc")
                if not isinstance(created_utc, (int, float)):
                    continue

                created_utc = float(created_utc)
                page_timestamps.append(created_utc)

                if created_utc > window_end_epoch:
                    newer_than_end += 1
                    continue

                if created_utc < window_start_epoch:
                    older_than_start += 1
                    continue

                all_posts.append(normalize_post(raw))
                kept += 1

            oldest_in_page = min(page_timestamps) if page_timestamps else None
            newest_in_page = max(page_timestamps) if page_timestamps else None

            print(
                f"Window {window_idx}: page {pages}: fetched={len(children)}, kept={kept}, "
                f"newer_than_end={newer_than_end}, older_than_start={older_than_start}, "
                f"newest={to_iso(newest_in_page)}, oldest={to_iso(oldest_in_page)}"
            )

            # Once oldest item in this page is older than current window start,
            # subsequent pages will also be older due to sort=new.
            if oldest_in_page is not None and oldest_in_page < window_start_epoch:
                print(
                    f"Window {window_idx}: stopping pagination at page {pages} (crossed window start)."
                )
                break

            after = data.get("after")
            if not after:
                print(f"Window {window_idx}: no further 'after' cursor, stopping.")
                break

            if config.request_delay_seconds > 0:
                time.sleep(config.request_delay_seconds)

    all_posts.sort(key=lambda row: row.get("created_utc") or 0, reverse=True)
    return all_posts


def normalize_pullpush_post(data: dict[str, Any]) -> dict[str, Any]:
    created_utc = data.get("created_utc")
    permalink = data.get("permalink") or ""
    if permalink and not permalink.startswith("http"):
        permalink = urljoin(REDDIT_BASE_URL, permalink)

    return {
        "id": data.get("id"),
        "name": data.get("name") or (f"t3_{data.get('id')}" if data.get("id") else None),
        "title": data.get("title") or "",
        "subreddit": data.get("subreddit") or "",
        "author": data.get("author") or "",
        "created_utc": created_utc,
        "created_iso": to_iso(created_utc if isinstance(created_utc, (int, float)) else None),
        "score": data.get("score"),
        "upvote_ratio": data.get("upvote_ratio"),
        "num_comments": data.get("num_comments"),
        "url": data.get("url") or "",
        "permalink": permalink,
        "domain": data.get("domain") or "",
        "is_self": data.get("is_self"),
        "selftext": data.get("selftext") or "",
    }


def fetch_posts_pullpush(
    config: Config,
    start_dt: datetime,
    end_dt: datetime,
    query: str,
) -> list[dict[str, Any]]:
    session = build_session(config.user_agent)
    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    all_posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    before_cursor = end_epoch
    pages = 0

    while pages < config.max_pages:
        pages += 1
        params = {
            "q": query,
            "after": start_epoch,
            "before": before_cursor,
            "size": config.limit_per_page,
            "sort": "desc",
            "sort_type": "created_utc",
        }

        payload = request_json_with_retry(
            session,
            PULLPUSH_ENDPOINT,
            params=params,
            timeout_seconds=config.timeout_seconds,
            max_attempts=config.max_request_attempts,
            backoff_seconds=config.retry_backoff_seconds,
        )
        rows = payload.get("data", [])

        if not rows:
            print(f"Page {pages}: no results, stopping.")
            break

        kept = 0
        page_timestamps: list[int] = []
        for raw in rows:
            post_id = raw.get("id")
            if not post_id or post_id in seen_ids:
                continue

            created_utc = raw.get("created_utc")
            if not isinstance(created_utc, (int, float)):
                continue
            created_utc = int(created_utc)
            page_timestamps.append(created_utc)

            if not (start_epoch <= created_utc <= end_epoch):
                continue

            seen_ids.add(post_id)
            all_posts.append(normalize_pullpush_post(raw))
            kept += 1

        oldest_in_page = min(page_timestamps) if page_timestamps else None
        newest_in_page = max(page_timestamps) if page_timestamps else None
        print(
            f"Page {pages}: fetched={len(rows)}, kept={kept}, "
            f"newest={to_iso(float(newest_in_page) if newest_in_page else None)}, "
            f"oldest={to_iso(float(oldest_in_page) if oldest_in_page else None)}"
        )

        if oldest_in_page is None or oldest_in_page <= start_epoch:
            print("Stopping pagination: crossed start date boundary.")
            break

        before_cursor = oldest_in_page - 1
        if config.request_delay_seconds > 0:
            time.sleep(config.request_delay_seconds)

    all_posts.sort(key=lambda row: row.get("created_utc") or 0, reverse=True)
    return all_posts


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def write_delimited(path: Path, rows: list[dict[str, Any]], delimiter: str) -> None:
    fields = [
        "id",
        "name",
        "title",
        "subreddit",
        "author",
        "created_utc",
        "created_iso",
        "score",
        "upvote_ratio",
        "num_comments",
        "url",
        "permalink",
        "domain",
        "is_self",
        "selftext",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = parse_args()
    start_dt, end_dt = resolve_date_window(config)
    query_list = resolve_query_list(config)

    config.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Provider: {config.provider}")
    print(f"Date window UTC: {start_dt.isoformat()} to {end_dt.isoformat()}")
    print(f"Queries to run: {len(query_list)}")

    posts: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for idx, query in enumerate(query_list, start=1):
        print(f"\nQuery {idx}/{len(query_list)}: {query}")
        query_posts = fetch_posts(config, start_dt=start_dt, end_dt=end_dt, query=query)
        added = 0
        for row in query_posts:
            key = post_key(row)
            if key is None or key in seen_keys:
                continue
            seen_keys.add(key)
            posts.append(row)
            added += 1
        print(f"Query {idx} fetched: {len(query_posts)}, merged new: {added}")

    posts.sort(key=lambda row: row.get("created_utc") or 0, reverse=True)

    json_path = config.out_dir / f"{config.output_prefix}.json"
    csv_path = config.out_dir / f"{config.output_prefix}.csv"
    tsv_path = config.out_dir / f"{config.output_prefix}.tsv"

    write_json(json_path, posts)
    write_delimited(csv_path, posts, delimiter=",")
    write_delimited(tsv_path, posts, delimiter="\t")

    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved TSV: {tsv_path}")
    print(f"Total posts collected: {len(posts)}")


if __name__ == "__main__":
    main()