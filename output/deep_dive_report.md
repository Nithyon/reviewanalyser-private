# Deep Technical Report

- Analysis model: `mbert`
- Rows analyzed: `144006`
- Models compared: `baseline, deberta, mbert`

## Executive Findings

- Base analysis model: mbert. Rows analyzed: 144006.
- Rating-sentiment association (Cramer's V): 0.6125 over 144006 rows.
- Model consensus on shared rows: 66.23% unanimous, 29.31% two-vs-one, 4.46% all-different.
- Strongest pairwise agreement: deberta_vs_mbert (kappa=0.6903).
- Weakest pairwise agreement: baseline_vs_deberta (kappa=0.457).
- Calibration proxy on 144006 rows: accuracy=0.8779, avg_confidence=0.5844, ECE=0.2935.
- Highest positive-share month: 2025-10 (66.9%).
- Highest negative-share month: 2025-06 (55.15%).
- Top theme at 1-star: free_cash_issue (25.67% prevalence).
- Top theme at 5-star: support_service (10.23% prevalence).

## Pairwise Model Agreement

| Pair | Overlap Rows | Agreement | Kappa |
|---|---:|---:|---:|
| baseline_vs_deberta | 144006 | 0.6785 | 0.4570 |
| baseline_vs_mbert | 144006 | 0.7699 | 0.5879 |
| deberta_vs_mbert | 144006 | 0.8317 | 0.6903 |

## Calibration (Rating Proxy)

- Samples: `144006` | Accuracy: `0.8779` | Avg confidence: `0.5844` | ECE: `0.2935`

| Confidence Bin | Samples | Avg Confidence | Proxy Accuracy | Gap |
|---|---:|---:|---:|---:|
| 0.0-0.1 | 2640 | 0.0000 | 0.0311 | 0.0311 |
| 0.2-0.3 | 5207 | 0.2676 | 0.3584 | 0.0908 |
| 0.3-0.4 | 11093 | 0.3487 | 0.6321 | 0.2834 |
| 0.4-0.5 | 42193 | 0.4704 | 0.9072 | 0.4368 |
| 0.5-0.6 | 25228 | 0.5400 | 0.9260 | 0.3861 |
| 0.6-0.7 | 14666 | 0.6493 | 0.9399 | 0.2906 |
| 0.7-0.8 | 15560 | 0.7546 | 0.9630 | 0.2084 |
| 0.8-0.9 | 17718 | 0.8508 | 0.9841 | 0.1333 |
| 0.9-1.0 | 9701 | 0.9360 | 0.9910 | 0.0550 |

## Rating vs Sentiment Association

- Samples: `144006` | Chi-square: `108051.5592` | Cramer's V: `0.6125`

| Rating | Negative | Neutral | Positive |
|---|---:|---:|---:|
| 1 | 47077 | 2133 | 2776 |
| 2 | 2265 | 398 | 459 |
| 3 | 1304 | 683 | 1055 |
| 4 | 716 | 867 | 5787 |
| 5 | 3343 | 4534 | 70609 |

## Theme Prevalence by Rating Bucket

| Rating | Reviews | Top Themes (theme: pct) |
|---|---:|---|
| 1 | 51986 | free_cash_issue: 25.67%, support_service: 18.87%, product_quality: 10.51%, pricing_charges: 9.72%, refund_payment: 7.35% |
| 2 | 3122 | free_cash_issue: 23.86%, pricing_charges: 12.17%, support_service: 9.93%, product_quality: 7.72%, delivery_delay: 6.02% |
| 3 | 3042 | free_cash_issue: 13.12%, pricing_charges: 7.82%, support_service: 6.44%, product_quality: 5.03%, delivery_delay: 3.98% |
| 4 | 7370 | support_service: 8.79%, free_cash_issue: 5.58%, pricing_charges: 4.56%, product_quality: 2.96%, delivery_delay: 1.23% |
| 5 | 78486 | support_service: 10.23%, pricing_charges: 3.08%, free_cash_issue: 2.91%, product_quality: 2.43%, delivery_delay: 0.34% |

## Monthly Trend Snapshot

| Month | Total | Neg % | Neu % | Pos % |
|---|---:|---:|---:|---:|
| 2025-04 | 19254 | 33.99 | 6.09 | 59.91 |
| 2025-05 | 22924 | 42.77 | 5.62 | 51.61 |
| 2025-06 | 18532 | 55.15 | 5.91 | 38.93 |
| 2025-07 | 16116 | 37.98 | 5.85 | 56.17 |
| 2025-08 | 12241 | 34.57 | 5.92 | 59.50 |
| 2025-09 | 11894 | 30.76 | 6.47 | 62.78 |
| 2025-10 | 14287 | 27.12 | 5.98 | 66.90 |
| 2025-11 | 5895 | 33.72 | 6.21 | 60.07 |
| 2025-12 | 6767 | 30.56 | 6.06 | 63.38 |
| 2026-01 | 6595 | 34.60 | 5.99 | 59.41 |
| 2026-02 | 6509 | 39.35 | 6.30 | 54.36 |
| 2026-03 | 2992 | 45.12 | 6.22 | 48.66 |
