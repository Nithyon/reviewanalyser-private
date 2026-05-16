# AI-Driven Aspect-Based Sentiment Analysis of Quick Commerce Platforms: A Social Media Listening Approach

## Extended Abstract

### Background and Motivation

The rapid proliferation of Quick Commerce (Q-commerce) platforms in India — including Zepto, Blinkit, and Swiggy Instamart — has fundamentally restructured urban last-mile grocery delivery by promising sub-15-minute fulfilment windows. As these platforms scale aggressively across Tier-1 and Tier-2 cities, the volume of organic consumer feedback on digital storefronts such as the Google Play Store has grown exponentially, generating hundreds of thousands of unstructured textual reviews annually. This Voice of Customer (VoC) data constitutes one of the richest, most authentic signals of consumer satisfaction and operational performance available to platform operators and academic researchers alike.

However, current industry practice remains predominantly reliant on aggregate star ratings and basic keyword-level sentiment scoring. Traditional sentiment analysis treats each review as a monolithic unit, assigning a single polarity label (positive, negative, or neutral) without distinguishing the specific service dimension the consumer is evaluating. A review such as *"Delivery was super fast but the tomatoes were completely rotten and customer care didn't help at all"* contains three distinct service evaluations — yet a conventional model would collapse this into a single "mixed" or "negative" verdict, rendering the insight operationally useless. This limitation creates a critical blind spot for marketing and operations executives who require granular, aspect-level intelligence to allocate resources, prioritise interventions, and diagnose systemic performance gaps.

This study addresses this gap by proposing and implementing a **Hybrid AI-Driven Aspect-Based Sentiment Analysis (ABSA)** framework that decomposes consumer VoC data into discrete service dimensions, classifies sentiment independently for each aspect, and aggregates the results into a strategic diagnostic matrix capable of identifying both explicit and latent performance failures within the Zepto Q-commerce ecosystem.

### Dataset and Scope

The empirical foundation of this study is a longitudinal corpus of **144,006 Google Play Store reviews** for the Zepto application, spanning a complete financial year from **April 2025 to March 2026**. This twelve-month window was deliberately chosen to capture seasonal demand fluctuations (e.g., monsoon logistics disruptions, festive-season promotional surges), platform scaling events, and the natural evolution of consumer sentiment over time — thereby mitigating the temporal bias inherent in cross-sectional samples.

Reviews were programmatically extracted using the Google Play Scraper API, yielding structured metadata including the review text, star rating (1–5), timestamp, and reviewer pseudonym. After extraction, the dataset underwent rigorous preprocessing: noise reduction (removal of emojis, URLs, and excessive whitespace), text normalisation, language detection to flag multilingual (Hinglish) entries, and structural repair to ensure schema consistency. Of the 144,006 total reviews, **141,366** contained sufficient textual content (≥3 tokens) to be processed through the downstream AI pipeline, while 2,640 ultra-short entries were excluded from model inference but retained for demographic completeness.

### Methodology: The Hybrid ABSA Framework

The analytical pipeline is executed in three sequential stages — Aspect Extraction, Sentiment Classification, and Strategic Diagnostic Aggregation — each designed to address a specific limitation of traditional approaches.

**Stage 1 — Zero-Shot Aspect Extraction via Jina AI.** Rather than relying on rigid rule-based keyword matching or manually labelled training corpora, this study deploys the **Jina AI Embeddings API (jina-embeddings-v3)** for zero-shot semantic classification. Each review is encoded into a high-dimensional vector representation and compared against nine predefined performance dimensions corresponding to the study's Independent Variables: (1) Delivery Speed and Timeliness, (2) Pricing and Charges, (3) Product Quality and Freshness, (4) Customer Service and Support, (5) Product Availability and Stock, (6) App Usability and Interface, (7) Refund and Payment Issues, (8) Location and Serviceability, and (9) Offers and Promotions. The model assigns each review to the aspect with the highest cosine similarity score, along with a confidence value and the full probability distribution across all nine categories. This approach overcomes the brittleness of keyword dictionaries — for instance, a review stating *"They charged me double for ruined vegetables"* is simultaneously recognised as relevant to both Pricing and Product Quality, regardless of whether the exact keywords "price" or "quality" appear in the text. Critically, the zero-shot paradigm eliminates the need for thousands of manually annotated training examples, making the framework scalable and immediately deployable across new product categories or competitor platforms.

**Stage 2 — Multi-Model Transformer Sentiment Classification.** To ensure methodological robustness and establish cross-model consensus, each review is independently scored by multiple Transformer-based deep learning architectures:

- **Multilingual BERT (mBERT)** — `nlptown/bert-base-multilingual-uncased-sentiment` — specifically selected for its ability to handle the Hinglish (Hindi + English) code-switching pervasive in Indian app store reviews, providing 3-class sentiment with star-rating granularity.
- **DeBERTa v3** — `mrm8488/deberta-v3-small-finetuned-sst2` — leveraging disentangled attention mechanisms for superior contextual disambiguation in binary sentiment tasks.
- **GloVe + TF-IDF Logistic Regression Baseline** — deployed as a traditional machine learning control to empirically validate the hypothesis (H1) that Transformer models outperform classical approaches.

This ensemble strategy enables rigorous inter-model comparison. Pairwise Cohen's Kappa agreement analysis revealed that DeBERTa and mBERT exhibited the highest concordance (κ = 0.69), while the GloVe baseline demonstrated the weakest agreement with Transformer models (κ = 0.46), empirically confirming the superiority of contextual deep learning architectures. Across all three models, unanimous sentiment consensus was achieved for **66.23%** of reviews, with a further 29.31% showing two-of-three agreement, providing a statistically grounded confidence layer for downstream diagnosis.

**Stage 3 — Strategic Gap Diagnosis.** The core analytical contribution lies in the systematic cross-referencing of aspect frequency distributions against aspect-level sentiment polarity to construct a diagnostic matrix. Four distinct gap typologies are identified:

1. **Direct Operational Gaps** — aspects with high negative sentiment concentration (e.g., Customer Service at 69.1% negative) indicating clear, actionable underperformance.
2. **Latent Experience Gaps** — aspects with disproportionately high neutral sentiment, interpreted as indicators of inconsistent, ambiguous, or unresolved customer experiences that evade traditional binary analysis.
3. **Systemic Process Failures** — aspects exhibiting both high discussion frequency and high negativity (e.g., Offers/Promotions accounting for the largest share of conversation volume with 17,182 "free cash" complaints concentrated in 1-star reviews).
4. **High-Impact Low-Visibility Issues** — infrequently discussed aspects that nonetheless generate extreme negative sentiment when they surface, representing asymmetric churn risk.

### Key Findings

Thematic decomposition of the 144,006-review corpus reveals that **Customer Support and Service** dominates conversation volume (18,992 mentions), followed by **Offers and Promotions** (17,182 mentions centred on invalid coupon/free-cash redemption failures), **Pricing and Charges** (8,424), **Product Quality** (7,985), and **Delivery Delays** (4,359). Sentiment-wise, mBERT classified 56.1% of reviews as positive and 38.0% as negative, while DeBERTa — which applies a more aggressive classification boundary — reported 52.4% negative and 45.8% positive, underscoring that model selection materially influences business intelligence outputs.

The most strategically significant finding is that the highest concentration of 1-star reviews is dominated by the *"free cash issue"* theme (25.67% of all 1-star reviews), indicating that promotional mechanic failures in the application layer — not delivery or product quality — constitute the single largest driver of extreme dissatisfaction. This insight, invisible to aggregate star-rating analysis, demonstrates the diagnostic power of the ABSA framework.

### Contribution and Implications

This study makes three contributions: (1) it extends the application of ABSA into the under-researched Q-commerce domain using a production-scale VoC dataset; (2) it introduces a novel diagnostic taxonomy that leverages neutral sentiment as an indicator of latent performance gaps; and (3) it provides an immediately actionable intelligence framework enabling Q-commerce operators to prioritise operational investment based on empirically grounded, aspect-level consumer feedback rather than aggregate satisfaction proxies.

**Keywords:** Aspect-Based Sentiment Analysis, Quick Commerce, Voice of Customer, Transformer Models, BERT, Zero-Shot Classification, Jina AI, Social Media Listening, Performance Gap Analysis, Customer Experience
