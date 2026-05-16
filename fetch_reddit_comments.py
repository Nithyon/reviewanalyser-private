import argparse
import csv
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import requests

PULLPUSH_ENDPOINT = "https://api.pullpush.io/reddit/search/comment/"

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

def to_iso(epoch: float | None) -> str:
    if not epoch:
        return ""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()

def request_json_with_retry(url: str, params: dict, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            print(f"Attempt {attempt+1}/{max_attempts} failed: {resp.status_code}. Retrying in 2s...")
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_attempts} failed: {e}. Retrying in 2s...")
        time.sleep(2)
    return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--output-prefix", default="reddit_zepto_comments")
    parser.add_argument("--max-pages", type=int, default=500)
    args = parser.parse_args()

    # Parse ISO 8601 strings (e.g. 2025-04-01)
    def parse_dt(s: str, is_end: bool):
        dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if is_end: dt = dt + timedelta(days=1, microseconds=-1)
        return dt

    start_dt = parse_dt(args.start_date, False)
    end_dt = parse_dt(args.end_date, True)
    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    queries = PREDEFINED_QUERY_SETS["zepto-expanded"]
    all_comments = []
    seen_ids = set()

    for query in queries:
        print(f"Fetching comments for query: {query}")
        before_cursor = end_epoch
        pages = 0
        
        while pages < args.max_pages:
            pages += 1
            params = {
                "q": query,
                "after": start_epoch,
                "before": before_cursor,
                "size": 100,
                "sort": "desc",
                "sort_type": "created_utc",
            }
            payload = request_json_with_retry(PULLPUSH_ENDPOINT, params)
            rows = payload.get("data", [])
            
            if not rows:
                break
                
            page_timestamps = []
            for row in rows:
                c_id = row.get("id")
                if not c_id: continue
                
                c_utc = int(row.get("created_utc", 0))
                page_timestamps.append(c_utc)
                
                if c_id not in seen_ids and (start_epoch <= c_utc <= end_epoch):
                    seen_ids.add(c_id)
                    all_comments.append({
                        "id": c_id,
                        "link_id": row.get("link_id", ""),
                        "subreddit": row.get("subreddit", ""),
                        "author": row.get("author", ""),
                        "created_utc": c_utc,
                        "created_iso": to_iso(c_utc),
                        "score": row.get("score"),
                        "body": row.get("body", ""),
                        "permalink": f"https://reddit.com{row.get('permalink', '')}",
                    })
                    
            if not page_timestamps: break
            oldest = min(page_timestamps)
            if oldest <= start_epoch: break
            
            before_cursor = oldest - 1
            time.sleep(1)

    all_comments.sort(key=lambda x: x["created_utc"], reverse=True)
    
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    
    json_path = out_dir / f"{args.output_prefix}.json"
    tsv_path = out_dir / f"{args.output_prefix}.tsv"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=2)
        
    fields = ["id", "link_id", "subreddit", "author", "created_utc", "created_iso", "score", "permalink", "body"]
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_comments)
        
    print(f"Saved {len(all_comments)} comments to {tsv_path}")

if __name__ == "__main__":
    main()
