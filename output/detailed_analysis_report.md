# Zepto Review Analysis Project - Full Timeline and Execution Order

Date generated: 2026-03-24
Scope: End-to-end reconstruction of what was done in this repository, from initial data pulls to deep technical reporting.

## How this timeline was reconstructed

This report is based on:
- Script and artifact modification timestamps in the workspace
- Available pipeline documentation in [README.md](README.md)
- Existing findings and report artifacts in [repo_statistics_and_findings.md](repo_statistics_and_findings.md), [output/model_stats_report.md](output/model_stats_report.md), and [output/deep_dive_report.md](output/deep_dive_report.md)

Note: Timeline order reflects file last-write evidence and generated artifacts, which is the best available execution trace in this workspace.

## Executive summary

You built and ran a complete social listening + sentiment intelligence pipeline in this order:
1. Collected Zepto app reviews and Reddit data
2. Standardized and repaired datasets for analysis
3. Produced baseline and transformer sentiment outputs (BERT, mBERT, DeBERTa)
4. Added model comparison reporting and ABSA workstream
5. Produced final deep-dive technical diagnostics (agreement, calibration, trend, theme-ratings)

Final status: The repository now contains both operational outputs and report-ready artifacts for technical and management audiences.

## Chronological timeline (ordered)

### Phase 1 - Initial data acquisition and setup (2026-03-12)

- 2026-03-12 13:20:27
  - Generated base Zepto review extracts:
    - [output/zepto_reviews.json](output/zepto_reviews.json)
    - [output/zepto_reviews.csv](output/zepto_reviews.csv)

- 2026-03-12 14:24:36
  - Prepared cleaning utility script:
    - [clean_reviews_to_tsv.py](clean_reviews_to_tsv.py)

- 2026-03-12 14:34:51
  - Prepared review counting utility:
    - [count_reviews_in_range.py](count_reviews_in_range.py)

- 2026-03-12 14:59:29 to 15:13:53
  - Produced initial Reddit pull artifacts:
    - [output/reddit_zepto_posts.csv](output/reddit_zepto_posts.csv)
    - [output/reddit_zepto_posts.tsv](output/reddit_zepto_posts.tsv)
    - [output/reddit_zepto_posts.json](output/reddit_zepto_posts.json)

- 2026-03-12 15:53:37
  - Produced 12-month Reddit dataset:
    - [output/reddit_zepto_posts_apr2025_mar2026.json](output/reddit_zepto_posts_apr2025_mar2026.json)
    - [output/reddit_zepto_posts_apr2025_mar2026.csv](output/reddit_zepto_posts_apr2025_mar2026.csv)
    - [output/reddit_zepto_posts_apr2025_mar2026.tsv](output/reddit_zepto_posts_apr2025_mar2026.tsv)

- 2026-03-12 15:59:07
  - Produced expanded-query Reddit dataset:
    - [output/reddit_zepto_posts_apr2025_mar2026_expanded.json](output/reddit_zepto_posts_apr2025_mar2026_expanded.json)
    - [output/reddit_zepto_posts_apr2025_mar2026_expanded.csv](output/reddit_zepto_posts_apr2025_mar2026_expanded.csv)
    - [output/reddit_zepto_posts_apr2025_mar2026_expanded.tsv](output/reddit_zepto_posts_apr2025_mar2026_expanded.tsv)

### Phase 2 - Pipeline hardening and year-scale app review processing (2026-03-13)

- 2026-03-13 11:03:58
  - Core acquisition + docs scripts finalized:
    - [fetch_reddit_posts.py](fetch_reddit_posts.py)
    - [fetch_zepto_reviews.py](fetch_zepto_reviews.py)
    - [README.md](README.md)

- 2026-03-13 11:04:44 to 11:08:33
  - Generated year-scale Zepto review dataset and cleaned TSV:
    - [output/zepto_reviews_apr2025_mar2026.json](output/zepto_reviews_apr2025_mar2026.json)
    - [output/zepto_reviews_apr2025_mar2026.tsv](output/zepto_reviews_apr2025_mar2026.tsv)
    - [output/zepto_reviews_apr2025_mar2026_clean.tsv](output/zepto_reviews_apr2025_mar2026_clean.tsv)

- 2026-03-13 11:38:22 to 11:56:15
  - NVivo + repair + sentiment baseline flow:
    - [prepare_nvivo_tsv.py](prepare_nvivo_tsv.py)
    - [repair_reviews_tsv.py](repair_reviews_tsv.py)
    - [output/zepto_reviews_apr2025_mar2026_fixed.tsv](output/zepto_reviews_apr2025_mar2026_fixed.tsv)
    - [output/zepto_reviews_apr2025_mar2026_nvivo.tsv](output/zepto_reviews_apr2025_mar2026_nvivo.tsv)
    - [output/zepto_reviews_apr2025_mar2026_sentiment.tsv](output/zepto_reviews_apr2025_mar2026_sentiment.tsv)
    - [output/zepto_reviews_apr2025_mar2026_sentiment.csv](output/zepto_reviews_apr2025_mar2026_sentiment.csv)
    - [output/zepto_reviews_apr2025_mar2026_sentiment.tsv_summary.json](output/zepto_reviews_apr2025_mar2026_sentiment.tsv_summary.json)

### Phase 3 - Model expansion (2026-03-15 to 2026-03-23)

- 2026-03-15
  - Added additional model pipelines:
    - [analyze_bert_sentiment.py](analyze_bert_sentiment.py)
    - [glove_baseline.py](glove_baseline.py)

- 2026-03-19 17:56:09
  - Generated legacy BERT run output:
    - [output/zepto_reviews_bert_sentiment.tsv](output/zepto_reviews_bert_sentiment.tsv)

- 2026-03-19 18:27:30 to 19:04:36
  - Generated mBERT test and full outputs:
    - [output/zepto_reviews_mbert_sentiment_test.tsv](output/zepto_reviews_mbert_sentiment_test.tsv)
    - [output/zepto_reviews_mbert_sentiment_test.csv](output/zepto_reviews_mbert_sentiment_test.csv)
    - [output/zepto_reviews_mbert_sentiment_test_summary.json](output/zepto_reviews_mbert_sentiment_test_summary.json)
    - [output/zepto_reviews_mbert_sentiment.tsv](output/zepto_reviews_mbert_sentiment.tsv)
    - [output/zepto_reviews_mbert_sentiment.csv](output/zepto_reviews_mbert_sentiment.csv)
    - [output/zepto_reviews_mbert_sentiment_summary.json](output/zepto_reviews_mbert_sentiment_summary.json)

- 2026-03-20 03:07:37
  - Backfilled full-year CSV:
    - [output/zepto_reviews_apr2025_mar2026.csv](output/zepto_reviews_apr2025_mar2026.csv)

- 2026-03-23 00:40:38 to 01:53:02
  - Updated core sentiment engine and generated DeBERTa test + full outputs:
    - [analyze_review_sentiment.py](analyze_review_sentiment.py)
    - [output/zepto_reviews_deberta_sentiment_test.tsv](output/zepto_reviews_deberta_sentiment_test.tsv)
    - [output/zepto_reviews_deberta_sentiment_test.csv](output/zepto_reviews_deberta_sentiment_test.csv)
    - [output/zepto_reviews_deberta_sentiment_test_summary.json](output/zepto_reviews_deberta_sentiment_test_summary.json)
    - [output/zepto_reviews_deberta_sentiment.tsv](output/zepto_reviews_deberta_sentiment.tsv)
    - [output/zepto_reviews_deberta_sentiment.csv](output/zepto_reviews_deberta_sentiment.csv)
    - [output/zepto_reviews_deberta_sentiment_summary.json](output/zepto_reviews_deberta_sentiment_summary.json)

### Phase 4 - Stats and repository reporting (2026-03-22 to 2026-03-23)

- 2026-03-22 11:34:54
  - Generated repository-level findings doc:
    - [repo_statistics_and_findings.md](repo_statistics_and_findings.md)

- 2026-03-23 20:15:27 to 20:15:40
  - Added model comparison reporter and generated model stats:
    - [report_model_stats.py](report_model_stats.py)
    - [output/model_stats_report.json](output/model_stats_report.json)
    - [output/model_stats_report.md](output/model_stats_report.md)

### Phase 5 - ABSA and social listening extension (2026-03-24)

- 2026-03-24 11:56:24 to 12:02:33
  - Added ABSA workflow scripts:
    - [prepare_nvivo_absa.py](prepare_nvivo_absa.py)
    - [report_absa_stats.py](report_absa_stats.py)
    - [jina_classify_aspects.py](jina_classify_aspects.py)

- 2026-03-24 12:16:17 to 12:36:52
  - Built Reddit-for-sentiment input, multi-model Reddit sentiment outputs, ABSA outputs, and ABSA reports:
    - [output/reddit_zepto_posts_apr2025_mar2026_forsentiment.tsv](output/reddit_zepto_posts_apr2025_mar2026_forsentiment.tsv)
    - [output/reddit_zepto_mbert_sentiment.tsv](output/reddit_zepto_mbert_sentiment.tsv)
    - [output/reddit_zepto_mbert_sentiment.csv](output/reddit_zepto_mbert_sentiment.csv)
    - [output/reddit_zepto_mbert_sentiment_summary.json](output/reddit_zepto_mbert_sentiment_summary.json)
    - [output/reddit_zepto_deberta_sentiment.tsv](output/reddit_zepto_deberta_sentiment.tsv)
    - [output/reddit_zepto_deberta_sentiment.csv](output/reddit_zepto_deberta_sentiment.csv)
    - [output/reddit_zepto_deberta_sentiment_summary.json](output/reddit_zepto_deberta_sentiment_summary.json)
    - [output/reddit_zepto_roberta_sentiment.tsv](output/reddit_zepto_roberta_sentiment.tsv)
    - [output/reddit_zepto_roberta_sentiment.csv](output/reddit_zepto_roberta_sentiment.csv)
    - [output/reddit_zepto_roberta_sentiment_summary.json](output/reddit_zepto_roberta_sentiment_summary.json)
    - [output/reddit_zepto_glove_sentiment.tsv](output/reddit_zepto_glove_sentiment.tsv)
    - [output/reddit_zepto_glove_sentiment.csv](output/reddit_zepto_glove_sentiment.csv)
    - [output/reddit_zepto_glove_sentiment_summary.json](output/reddit_zepto_glove_sentiment_summary.json)
    - [output/reddit_zepto_jina_absa.tsv](output/reddit_zepto_jina_absa.tsv)
    - [output/reddit_zepto_jina_absa.csv](output/reddit_zepto_jina_absa.csv)
    - [output/reddit_zepto_jina_absa_summary.json](output/reddit_zepto_jina_absa_summary.json)
    - [output/reddit_zepto_absa_nvivo.tsv](output/reddit_zepto_absa_nvivo.tsv)
    - [output/reddit_absa_stats_report.json](output/reddit_absa_stats_report.json)
    - [output/reddit_absa_stats_report.md](output/reddit_absa_stats_report.md)

### Phase 6 - Deep technical diagnostics and final reporting (2026-03-24)

- 2026-03-24 12:13:08
  - Added deep diagnostics engine:
    - [deep_dive_analysis.py](deep_dive_analysis.py)

- 2026-03-24 12:16:53
  - Generated deep report artifacts:
    - [output/deep_dive_report.json](output/deep_dive_report.json)
    - [output/deep_dive_report.md](output/deep_dive_report.md)

- 2026-03-24 12:46:15
  - Detailed narrative report generated/updated:
    - [output/detailed_analysis_report.md](output/detailed_analysis_report.md)

## Final ordered execution map (start to finish)

1. Fetch raw app reviews and Reddit posts
2. Expand Reddit query coverage for a full-year window
3. Clean and repair review datasets
4. Prepare NVivo-ready TSVs
5. Run baseline sentiment pipeline
6. Run BERT and mBERT test/full sentiment pipelines
7. Run DeBERTa test/full sentiment pipelines
8. Generate model-level comparative statistics
9. Run Reddit sentiment suite (mBERT, DeBERTa, RoBERTa, GloVe baseline)
10. Run zero-shot ABSA classification and ABSA statistics reporting
11. Run deep diagnostics (agreement, kappa, calibration, trend, theme x rating)
12. Consolidate detailed technical reporting

## Current deliverables available now

Core analysis reports:
- [output/model_stats_report.md](output/model_stats_report.md)
- [output/reddit_absa_stats_report.md](output/reddit_absa_stats_report.md)
- [output/deep_dive_report.md](output/deep_dive_report.md)
- [output/detailed_analysis_report.md](output/detailed_analysis_report.md)

Machine-readable report payloads:
- [output/model_stats_report.json](output/model_stats_report.json)
- [output/reddit_absa_stats_report.json](output/reddit_absa_stats_report.json)
- [output/deep_dive_report.json](output/deep_dive_report.json)

## What this means for your project maturity

- Data engineering: Complete (collection, cleaning, repair, standardization)
- Sentiment modeling: Complete with multi-model comparison
- ABSA and thematic intelligence: Complete and reportable
- Diagnostics quality: Strong (pairwise agreement, kappa, calibration, trend views)
- Research output readiness: High (markdown + JSON + NVivo exports available)

## Key code used in this project

### A) Data collection and source expansion

- [fetch_zepto_reviews.py](fetch_zepto_reviews.py): Google Play review ingestion.
- [fetch_reddit_posts.py](fetch_reddit_posts.py): Reddit and Pullpush retrieval with date-window slicing, retry logic, and query expansion.

Example command pattern:

```powershell
c:/Users/saini/reviewanalyser/.venv/Scripts/python.exe fetch_reddit_posts.py --provider pullpush --start-date 2025-04-01 --end-date 2026-03-31 --query-set zepto-expanded --max-pages 200 --output-prefix reddit_zepto_posts_apr2025_mar2026_expanded
```

### B) Cleaning, repair, and NVivo preparation

- [clean_reviews_to_tsv.py](clean_reviews_to_tsv.py): Converts raw extract to normalized TSV.
- [repair_reviews_tsv.py](repair_reviews_tsv.py): Repairs malformed rows.
- [prepare_nvivo_tsv.py](prepare_nvivo_tsv.py): Creates NVivo-compatible exports.
- [prepare_nvivo_absa.py](prepare_nvivo_absa.py): NVivo export path for ABSA outputs.

### C) Sentiment modeling pipeline

- [analyze_review_sentiment.py](analyze_review_sentiment.py): Main sentiment engine with transformer inference and theme tagging.
- [analyze_bert_sentiment.py](analyze_bert_sentiment.py): BERT-oriented run path.
- [glove_baseline.py](glove_baseline.py): Traditional baseline model.

Core modeling logic used in [analyze_review_sentiment.py](analyze_review_sentiment.py):

```python
classifier = pipeline(
  "text-classification",
  model=model_name,
  device=device,
)

themes = extract_themes(text)
sentiment_label = parse_model_label(model_label, label_map)
```

### D) ABSA classification and ABSA statistics

- [jina_classify_aspects.py](jina_classify_aspects.py): Zero-shot aspect classification via Jina API.
- [report_absa_stats.py](report_absa_stats.py): ABSA hypothesis-style reporting.

Core ABSA endpoint configuration in [jina_classify_aspects.py](jina_classify_aspects.py):

```python
JINA_CLASSIFY_URL = "https://api.jina.ai/v1/classify"
JINA_MODEL = "jina-embeddings-v3"
```

### E) Aggregation and deep diagnostics

- [report_model_stats.py](report_model_stats.py): Merges model summaries and generates comparison reports.
- [deep_dive_analysis.py](deep_dive_analysis.py): Deep diagnostics (kappa, agreement, calibration, association, trend and theme/rating analysis).

Core deep metrics in [deep_dive_analysis.py](deep_dive_analysis.py):

```python
def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
  ...

def pairwise_model_agreement(model_rows: dict[str, dict[str, dict]]) -> dict:
  ...

def confidence_calibration(rows: dict[str, dict], bins: int = 10) -> dict:
  ...
```

## Key outputs and findings to cite

### Primary generated reports

- [output/model_stats_report.md](output/model_stats_report.md)
- [output/reddit_absa_stats_report.md](output/reddit_absa_stats_report.md)
- [output/deep_dive_report.md](output/deep_dive_report.md)
- [output/detailed_analysis_report.md](output/detailed_analysis_report.md)

### Machine-readable report payloads

- [output/model_stats_report.json](output/model_stats_report.json)
- [output/reddit_absa_stats_report.json](output/reddit_absa_stats_report.json)
- [output/deep_dive_report.json](output/deep_dive_report.json)

### Most important quantitative findings (from current run artifacts)

1. Total Zepto review rows analyzed: 144006 (full production-scale run).
2. Rating-sentiment association strength: Cramer's V = 0.6125 ([output/deep_dive_report.md](output/deep_dive_report.md)).
3. Model consensus on shared rows: 66.23% unanimous, 29.31% two-vs-one, 4.46% all-different ([output/deep_dive_report.md](output/deep_dive_report.md)).
4. Pairwise strongest agreement: deberta vs mbert, kappa = 0.6903.
5. Pairwise weakest agreement: baseline vs deberta, kappa = 0.4570.
6. Calibration diagnostic: proxy accuracy = 0.8779, average confidence = 0.5844, ECE = 0.2935.
7. Highest positive month: 2025-10 at 66.90%; highest negative month: 2025-06 at 55.15%.
8. Theme concentration by rating: 1-star dominated by free_cash_issue at 25.67%; 5-star dominated by support_service at 10.23%.
9. mBERT full-run class distribution: negative 54705, neutral 8615, positive 80686 ([output/model_stats_report.md](output/model_stats_report.md)).
10. DeBERTa full-run class distribution: negative 75472, neutral 2640, positive 65894 ([output/model_stats_report.md](output/model_stats_report.md)).

### Suggested citation mapping (for thesis/report writing)

- Pipeline chronology and execution evidence: this file [output/detailed_analysis_report.md](output/detailed_analysis_report.md).
- Model comparison table and run-level distributions: [output/model_stats_report.md](output/model_stats_report.md).
- Deep technical diagnostics and reliability checks: [output/deep_dive_report.md](output/deep_dive_report.md).
- ABSA coverage and hypothesis-oriented insights on Reddit stream: [output/reddit_absa_stats_report.md](output/reddit_absa_stats_report.md).
