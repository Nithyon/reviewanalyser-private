# Repository Findings & Statistics

## Overview
The **Review Analyser** repository is a comprehensive data scraping and NLP pipeline designed to extract, clean, and analyze user reviews and social media mentions related to **Zepto**, specifically from Google Play Store and Reddit. It utilizes Deep Learning models (`torch`, `transformers`) to conduct sentiment analysis on the fetched data.

## Core Dependencies
Based on the `requirements.txt`:
- `google-play-scraper`: Utilized to scrape Google Play app reviews.
- `requests`: General HTTP requests for APIs, particularly the Reddit Pullpush API.
- `torch` & `transformers`: Used for running sentiment analysis models (specifically utilizing variants like BERT and mBERT as indicated by file names).

## Codebase Statistics (Python Scripts)
The repository contains 12 primary Python scripts driving the pipeline structure. Here is a breakdown of their purposes, ordered by size/estimated complexity:

1. **`fetch_reddit_posts.py`** (~23.3 KB, ~620 lines)
   - Fetches Reddit discussions concerning Zepto using configurable date windows and multi-query setups.
2. **`analyze_review_sentiment.py`** (~12.3 KB, ~344 lines)
   - Handles the core logic of processing reviews through transformer-based sentiment models, inferring sentiment automatically.
3. **`fetch_zepto_reviews.py`** (~7.4 KB, ~200 lines)
   - Primary data collection script for scraping Google Play Store reviews for the Zepto App.
4. **`prepare_nvivo_tsv.py`** (~6.4 KB, ~180 lines)
   - Prepares and formats the processed TSV data for import into NVivo (a qualitative data analysis software system workflow).
5. **`count_reviews_in_range.py`** (~3.7 KB, ~90 lines)
   - Utility tool to quickly count the raw number of Google Play reviews in a specific date window.
6. **`repair_reviews_tsv.py`** (~3.3 KB, ~72 lines)
   - Utility for fixing malformed or broken TSV datasets before running sentiment analysis or exporting.
7. **`glove_baseline.py`** (~2.5 KB)
   - A baseline NLP script likely utilizing GloVe word embeddings for text representation and predicting sentiment as a comparative baseline.
8. **`clean_reviews_to_tsv.py`** (~2.1 KB, ~51 lines)
   - Cleans the raw JSON data extracted from stores into a standardized, usable TSV format (`User`, `Rating`, `Comment`).
9. **`analyze_bert_sentiment.py`** (~1.9 KB, ~44 lines)
   - Additional script for running generic BERT sentiment predictions on the cleaned datasets.
10. **`validate_envivo_tsv.py`** (~1.4 KB)
    - Validates that TSV output structurally fits the strict formatting rules for NVivo import.
11. **`detect_languages.py`** (~1.4 KB)
    - Detects languages of the reviews to handle multilingual complexity before model inference (mBERT focuses extensively on supporting multi-lingual datasets).

## Data and Output Statistics (`/output` Directory)
The project has processed significant, gigabyte-level equivalents of unstructured strings natively converted into actionable data.

- **Total Output Data Files**: 30 files (.csv, .tsv, .json)
- **Top-Level Scale & Data Mass**:
  - **Raw Zepto Reviews (Apr 2025 - Mar 2026)**: Massive datasets like the 84.4 MB JSON file (`zepto_reviews_apr2025_mar2026.json`) and ~34 MB equivalent TSVs. This implies hundreds of thousands of user reviews stored locally.
  - **Sentiment Data**: Post sentiment-analysis files approach 40 MB in scale (`zepto_reviews_apr2025_mar2026_sentiment.csv`).
  - **Reddit Coverage**: Historical posts span global coverage over a full longitudinal year (Apr 2025 - Mar 2026), generating aggregated JSON chunks close to ~1 MB representing thousands of discussions.
  - **Model Testing Sets**: Testing splits (e.g., `zepto_reviews_mbert_sentiment_test.tsv` at ~60 KB) indicate localized evaluation, validation iterations, or specific benchmarking for Multilingual BERT (mBERT).

## Architectural Pipeline Identified
1. **Extraction**: `fetch_zepto_reviews.py` & `fetch_reddit_posts.py` capture raw unstructured social media signals and reviews to unrefined JSON files.
2. **Cleaning & Standardization**: `clean_reviews_to_tsv.py` normalizes formatting. Utilities like `detect_languages.py` and `repair_reviews_tsv.py` ensure data uniformity.
3. **Deep Analysis**: `analyze_review_sentiment.py` processes normalized files using underlying `transformers` + `torch` stacks for inference.
4. **Qualitative Export**: `prepare_nvivo_tsv.py` ultimately bridges AI-processed structural datasets back into traditional researcher stacks (NVivo).
