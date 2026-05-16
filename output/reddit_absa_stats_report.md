# ABSA Statistics Report
**Source**: `reddit_zepto_jina_absa.tsv`  
**Total Reviews**: 778  

---

## 1. Aspect Distribution

| Aspect | Count | % |
|--------|------:|--:|
| Offers and Promotions | 224 | 28.8% |
| Refund and Payment Issues | 125 | 16.1% |
| Customer Service and Support | 123 | 15.8% |
| Product Quality and Freshness | 121 | 15.6% |
| Delivery Speed and Timeliness | 68 | 8.7% |
| Pricing and Charges | 35 | 4.5% |
| App Usability and Interface | 25 | 3.2% |
| Product Availability and Stock | 24 | 3.1% |
| Location and Serviceability | 23 | 3.0% |
| Unknown | 10 | 1.3% |

## 2. Aspect × Sentiment Cross-tabulation

| Aspect | Positive | Neutral | Negative |
|--------|--------:|--------:|---------:|
| App Usability and Interface | 13 | 7 | 5 |
| Customer Service and Support | 31 | 12 | 80 |
| Delivery Speed and Timeliness | 16 | 3 | 49 |
| Location and Serviceability | 2 | 0 | 21 |
| Offers and Promotions | 75 | 8 | 141 |
| Pricing and Charges | 15 | 4 | 16 |
| Product Availability and Stock | 4 | 0 | 20 |
| Product Quality and Freshness | 37 | 11 | 73 |
| Refund and Payment Issues | 8 | 6 | 111 |
| Unknown | 1 | 0 | 9 |

## 3. Aspect Average Ratings

| Aspect | Avg Rating | # Reviews |
|--------|----------:|---------:|
| Unknown | 1.00 | 10 |
| App Usability and Interface | 1.04 | 25 |
| Location and Serviceability | 3.22 | 23 |
| Product Availability and Stock | 3.88 | 24 |
| Delivery Speed and Timeliness | 6.34 | 68 |
| Offers and Promotions | 6.98 | 224 |
| Refund and Payment Issues | 8.24 | 125 |
| Product Quality and Freshness | 10.35 | 121 |
| Customer Service and Support | 13.63 | 123 |
| Pricing and Charges | 22.94 | 35 |

## 4. Hypothesis Testing Results

### H1_ABSA_improvement
**ABSA provides aspect-level granularity vs overall sentiment**

- **total_reviews**: 778
- **reviews_with_aspect**: 768
- **classification_rate**: 98.71
- **reviews_with_multiple_themes**: 124
- **granularity_gain_pct**: 16.15

### H2_delivery_speed_impact
**Delivery speed has significant positive impact on customer sentiment**

- **total_delivery_reviews**: 68
- **positive_pct**: 23.53
- **negative_pct**: 72.06
- **avg_rating**: 6.34
- **sentiment_ratio**: 0.3265

### H3_pricing_negative_sentiment
**Pricing perception significantly influences negative sentiment**

- **total_pricing_reviews**: 35
- **negative_pct**: 45.71
- **positive_pct**: 42.86
- **negative_dominance**: True

### H4_customer_service_quality
**Customer service quality positively affects brand sentiment**

- **total_service_reviews**: 146
- **positive_pct**: 22.6
- **negative_pct**: 69.18
- **avg_rating**: 11.99

### H5_social_media_sentiment_satisfaction
**Social media sentiment predicts customer satisfaction levels**

- **avg_rating**: 8.94
- **sentiment_distribution**: {'negative': 525, 'positive': 202, 'neutral': 51}
- **correlation_direction**: negative

### H6_ai_social_listening
**AI-driven social listening improves insight generation vs rule-based**

- **rule_based_coverage**: 45.63
- **absa_coverage**: 98.71
- **coverage_improvement_pct**: 116.34
- **unique_aspects_identified**: 10

## 5. Model Confidence

- **Mean confidence**: 0.1169
- **Min confidence**: 0.0000
- **Max confidence**: 0.1300

## 6. Monthly Aspect Trends

| Month | App Usability and Interface | Customer Service and Support | Delivery Speed and Timeliness | Location and Serviceability | Offers and Promotions | Pricing and Charges | Product Availability and Stock | Product Quality and Freshness | Refund and Payment Issues | Unknown |
|-------|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|
| 2025-04 | 22 | 93 | 36 | 18 | 159 | 25 | 15 | 89 | 82 | 10 |
| 2025-05 | 3 | 30 | 32 | 5 | 65 | 10 | 9 | 32 | 43 | 0 |

## 7. Rule-Based Themes vs ABSA Aspects

| Rule-Based Theme | Top ABSA Aspect | Agreement Count |
|-----------------|----------------|---------------:|
| app_bugs | Offers and Promotions | 8 |
| delivery_delay | Offers and Promotions | 51 |
| free_cash_issue | Offers and Promotions | 41 |
| location_unavailable | Refund and Payment Issues | 5 |
| out_of_stock | Refund and Payment Issues | 6 |
| pricing_charges | Product Quality and Freshness | 21 |
| product_quality | Product Quality and Freshness | 18 |
| refund_payment | Refund and Payment Issues | 24 |
| support_service | Customer Service and Support | 21 |
