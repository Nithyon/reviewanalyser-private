import os
import json
import praw
from datetime import datetime, timezone

def main():
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERROR: Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.")
        print("You can get these by creating an app at https://www.reddit.com/prefs/apps")
        return

    print("Connecting to Reddit using PRAW...")
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="ZeptoReviewFetcher/1.0 (by /u/YourUsername)"
    )

    query = 'zepto OR "zepto app" OR "zepto delivery"'
    print(f"Searching Reddit for: {query}")
    
    # Note: PRAW limits search to the last 1000 items maximum.
    # We use time_filter="year" to approximate the March 2025 - March 2026 window.
    # Precise start/end dates are not supported by the official Reddit API.
    
    posts = []
    try:
        # Search across all subreddits
        for submission in reddit.subreddit("all").search(query, time_filter="year", limit=1000):
            created_utc = submission.created_utc
            dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            
            # Filter exactly for March 1, 2025 to March 31, 2026
            if datetime(2025, 3, 1, tzinfo=timezone.utc) <= dt <= datetime(2026, 3, 31, tzinfo=timezone.utc):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "subreddit": submission.subreddit.display_name,
                    "score": submission.score,
                    "created_utc": created_utc,
                    "created_iso": dt.isoformat(),
                    "url": submission.url
                })
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    print(f"Fetched {len(posts)} posts within the date range from PRAW.")
    
    # Save results
    out_file = "output/praw_reddit_zepto.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
        
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    main()
