# Review Analyser

## Scripts

- `fetch_zepto_reviews.py`: Fetch Zepto reviews from Google Play and save JSON/CSV.
- `clean_reviews_to_tsv.py`: Convert review JSON to a clean 3-column TSV (`User`, `Rating`, `Comment`).
- `count_reviews_in_range.py`: Count Google Play reviews in a date window.
- `fetch_reddit_posts.py`: Fetch Zepto-related Reddit posts from the last N days and save JSON/CSV/TSV.

## Setup

```powershell
c:/Users/saini/reviewanalyser/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Fetch 1 month Reddit data

```powershell
c:/Users/saini/reviewanalyser/.venv/Scripts/python.exe fetch_reddit_posts.py --days 30 --query "zepto OR \"zepto app\" OR \"zepto delivery\""
```

Outputs are written to `output/reddit_zepto_posts.json`, `output/reddit_zepto_posts.csv`, and `output/reddit_zepto_posts.tsv`.

## Fetch 12 month Reddit data (global Zepto posts)

```powershell
c:/Users/saini/reviewanalyser/.venv/Scripts/python.exe fetch_reddit_posts.py --provider pullpush --start-date 2025-04-01 --end-date 2026-03-31 --query zepto --max-pages 200 --output-prefix reddit_zepto_posts_apr2025_mar2026
```

By default, the script uses month-wise date slices for the `reddit` provider. For broader historical coverage, use the `pullpush` provider.

## One-command expanded query merge

Use a predefined query set, merge all matches, and deduplicate by post id/name/permalink:

```powershell
c:/Users/saini/reviewanalyser/.venv/Scripts/python.exe fetch_reddit_posts.py --provider pullpush --start-date 2025-04-01 --end-date 2026-03-31 --query-set zepto-expanded --max-pages 200 --output-prefix reddit_zepto_posts_apr2025_mar2026_expanded
```

You can also provide your own list of queries with `--query-file` (one query per line).
