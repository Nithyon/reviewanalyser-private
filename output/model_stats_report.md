# Model Stats Report

| Model | Run | Rows | Scored | Neg | Neu | Pos | Neg % | Neu % | Pos % | Summary |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| bert | full | 144006 | 144006 | 54705 | 6955 | 82346 | 38.0% | 4.8% | 57.2% | no |
| deberta | full | 144006 | 141366 | 75472 | 2640 | 65894 | 52.4% | 1.8% | 45.8% | yes |
| mbert | full | 144006 | 141366 | 54705 | 8615 | 80686 | 38.0% | 6.0% | 56.0% | yes |
| unspecified | full | 144006 | 141366 | 34841 | 21546 | 87619 | 24.2% | 15.0% | 60.8% | yes |
| deberta | test | 100 | 98 | 59 | 2 | 39 | 59.0% | 2.0% | 39.0% | yes |
| mbert | test | 200 | 198 | 94 | 13 | 93 | 47.0% | 6.5% | 46.5% | yes |

## Model Runs

### bert (full)
- Source: `zepto_reviews_bert_sentiment.tsv`
- Model: `nlptown/bert-base-multilingual-uncased-sentiment`
- Rows total: `144006`
- Rows scored: `144006`
- Rows skipped too short: `0`
- Negative / Neutral / Positive: `54705` / `6955` / `82346`
- Class distribution: `38.0%` negative, `4.8%` neutral, `57.2%` positive
- Average confidence: `0.5913`
- Output TSV: `output\zepto_reviews_bert_sentiment.tsv`

### deberta (full)
- Source: `zepto_reviews_deberta_sentiment_summary.json`
- Model: `mrm8488/deberta-v3-small-finetuned-sst2`
- Rows total: `144006`
- Rows scored: `141366`
- Rows skipped too short: `2640`
- Negative / Neutral / Positive: `75472` / `2640` / `65894`
- Class distribution: `52.4%` negative, `1.8%` neutral, `45.8%` positive
- Average source rating: `3.3975`
- Output TSV: `output\zepto_reviews_deberta_sentiment.tsv`
- Output CSV: `output\zepto_reviews_deberta_sentiment.csv`
- Top themes: `support_service=18992`, `free_cash_issue=17182`, `pricing_charges=8424`, `product_quality=7985`, `delivery_delay=4359`

### mbert (full)
- Source: `zepto_reviews_mbert_sentiment_summary.json`
- Model: `nlptown/bert-base-multilingual-uncased-sentiment`
- Rows total: `144006`
- Rows scored: `141366`
- Rows skipped too short: `2640`
- Negative / Neutral / Positive: `54705` / `8615` / `80686`
- Class distribution: `38.0%` negative, `6.0%` neutral, `56.0%` positive
- Average source rating: `3.3975`
- Output TSV: `output\zepto_reviews_mbert_sentiment.tsv`
- Output CSV: `output\zepto_reviews_mbert_sentiment.csv`
- Top themes: `support_service=18992`, `free_cash_issue=17182`, `pricing_charges=8424`, `product_quality=7985`, `delivery_delay=4359`

### unspecified (full)
- Source: `zepto_reviews_apr2025_mar2026_sentiment.tsv_summary.json`
- Model: `unspecified-model`
- Rows total: `144006`
- Rows scored: `141366`
- Rows skipped too short: `2640`
- Negative / Neutral / Positive: `34841` / `21546` / `87619`
- Class distribution: `24.2%` negative, `15.0%` neutral, `60.8%` positive
- Average source rating: `3.3975`
- Output TSV: `output\zepto_reviews_apr2025_mar2026_sentiment.tsv`
- Output CSV: `output\zepto_reviews_apr2025_mar2026_sentiment.csv`
- Top themes: `support_service=18992`, `free_cash_issue=17182`, `pricing_charges=8424`, `product_quality=7985`, `delivery_delay=4359`

### deberta (test)
- Source: `zepto_reviews_deberta_sentiment_test_summary.json`
- Model: `mrm8488/deberta-v3-small-finetuned-sst2`
- Rows total: `100`
- Rows scored: `98`
- Rows skipped too short: `2`
- Negative / Neutral / Positive: `59` / `2` / `39`
- Class distribution: `59.0%` negative, `2.0%` neutral, `39.0%` positive
- Average source rating: `3.12`
- Output TSV: `output\zepto_reviews_deberta_sentiment_test.tsv`
- Output CSV: `output\zepto_reviews_deberta_sentiment_test.csv`
- Top themes: `support_service=24`, `product_quality=9`, `delivery_delay=6`, `pricing_charges=4`, `refund_payment=4`

### mbert (test)
- Source: `zepto_reviews_mbert_sentiment_test_summary.json`
- Model: `nlptown/bert-base-multilingual-uncased-sentiment`
- Rows total: `200`
- Rows scored: `198`
- Rows skipped too short: `2`
- Negative / Neutral / Positive: `94` / `13` / `93`
- Class distribution: `47.0%` negative, `6.5%` neutral, `46.5%` positive
- Average source rating: `3.05`
- Output TSV: `output\zepto_reviews_mbert_sentiment_test.tsv`
- Output CSV: `output\zepto_reviews_mbert_sentiment_test.csv`
- Top themes: `support_service=41`, `delivery_delay=15`, `product_quality=14`, `refund_payment=10`, `pricing_charges=7`
