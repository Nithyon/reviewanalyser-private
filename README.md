# Zepto Review Analysis (reviewanalyser)

Comprehensive social-listening pipeline for Zepto app reviews and Reddit data. This repository contains data acquisition, cleaning, multiple sentiment model runs (BERT, mBERT, DeBERTa, RoBERTa, GloVe baseline), ABSA exports, and deep diagnostic reporting for model comparison and reliability analysis.

## Key Features

- Collects app reviews (Google Play) and Reddit posts with configurable query windows.
- Cleans and repairs raw extracts and produces NVivo-compatible TSV exports.
- Runs multiple sentiment inference pipelines and a traditional GloVe baseline.
- Zero-shot ABSA (aspect) classification via Jina and ABSA reporting.
- Deep diagnostics: pairwise agreement, Cohen's Kappa, calibration (ECE), trend and theme×rating analysis.
- Produces both machine-readable JSON payloads and human-ready markdown reports.

## Repository layout (important files)

- `fetch_zepto_reviews.py` — Google Play review ingestion
- `fetch_reddit_posts.py` — Reddit + Pullpush retrieval and query expansion
- `clean_reviews_to_tsv.py` — Normalize raw extracts to TSV
- `repair_reviews_tsv.py` — Repair malformed TSV rows
- `prepare_nvivo_tsv.py` / `prepare_nvivo_absa.py` — NVivo export utilities
- `analyze_review_sentiment.py` — Core transformer sentiment engine (DeBERTa, RoBERTa, mBERT)
- `analyze_bert_sentiment.py` — Legacy BERT path
- `glove_baseline.py` — Traditional baseline model
- `jina_classify_aspects.py` — Zero-shot ABSA via Jina API
- `report_model_stats.py` — Aggregates model summaries and produces comparison reports
- `deep_dive_analysis.py` — Diagnostics (kappa, agreement, calibration, trend, theme-rating)
- `output/` — Generated artifacts, reports, JSON payloads, and NVivo TSVs

## Quickstart — Setup (Windows / cross-platform)

1. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Confirm scripts are working by running a small fetch or the included unit/utility functions.

## Typical workflows & example commands

Fetch Reddit posts (example with Pullpush provider):

```powershell
python fetch_reddit_posts.py --provider pullpush --start-date 2025-04-01 --end-date 2026-03-31 --query-set zepto-expanded --max-pages 200 --output-prefix reddit_zepto_posts_apr2025_mar2026_expanded
```

Fetch Google Play reviews (example):

```powershell
python fetch_zepto_reviews.py --output-prefix zepto_reviews
```

Convert raw JSON to a clean TSV:

```powershell
python clean_reviews_to_tsv.py --input output/zepto_reviews.json --output output/zepto_reviews_apr2025_mar2026.tsv
```

Run the core sentiment engine (DeBERTa example):

```powershell
python analyze_review_sentiment.py --model deberta --input output/zepto_reviews_apr2025_mar2026_nvivo.tsv --output-prefix zepto_reviews_deberta_sentiment
```

Run ABSA via Jina (zero-shot):

```powershell
python jina_classify_aspects.py --input output/reddit_zepto_posts_apr2025_mar2026_forsentiment.tsv --output-prefix reddit_zepto_jina_absa
```

Generate model comparison and deep diagnostics:

```powershell
python report_model_stats.py --inputs output/*_sentiment_summary.json --output output/model_stats_report.json
python deep_dive_analysis.py --inputs output/*_sentiment.tsv --output output/deep_dive_report.json
```

## Outputs and reports

- Human-readable reports (Markdown): `output/model_stats_report.md`, `output/deep_dive_report.md`, `output/reddit_absa_stats_report.md`, `output/detailed_analysis_report.md`.
- Machine-readable payloads: `output/*.json` (for dashboards or programmatic ingestion).
- NVivo exports and ABSA TSVs: `output/*_nvivo.tsv`, `output/*_absa.tsv`.

## Large files & repository size guidance

Some artifacts in `output/` are large (multi-GB or multi-100MB JSON/TSV). GitHub recommends keeping files <50MB and enforces a hard 100MB file limit. Recommended approaches:

- Use Git LFS to track large outputs:

```powershell
git lfs install
git lfs track "output/*.json" "output/*.tsv"
git add .gitattributes
git commit -m "Track large outputs with Git LFS"
```

- Keep only summary files in the repo and push full artifacts to cloud storage (S3, GDrive, Azure Blob) with signed links.
- If desired, I can help migrate the current large files to LFS or remove them from history.

## Privacy & security notes

- The repository contains processed user-generated content and analytical outputs. Before widely publishing or sharing, ensure that any personal data or PII is removed or sanitized.

## Contributing

- Fork the repo, create a feature branch, open a PR against `main`. Avoid committing raw data artifacts—use `output/` only for summary artifacts.

## License

Add a `LICENSE` file with your chosen license (MIT/Apache-2.0) if you want to make terms explicit. I can add one if you tell me which license to use.

## Maintainer / Contact

- GitHub: `Nithyon`
- For access requests or questions, open an issue or contact the repo owner.

---
This README provides operational guidance, typical commands, and governance notes for the `reviewanalyser` project.
