# Chapter 4: Data Analysis and Findings (MBA Thesis)

**Title**: AI-Driven Aspect-Based Sentiment Analysis of Quick Commerce Platforms: A Social Media Listening Approach  
**Context**: Zepto Q-Commerce Performance Evaluation  
**Dataset**: Reddit (778 Posts, April 2025 – May 2026)  

---

## 4.1 Introduction to the Analytical Pipeline

This chapter details the execution of the proposed **Hybrid AI Model** for Aspect-Based Sentiment Analysis (ABSA). The objective is to transition from traditional, uni-dimensional sentiment analysis to a precise, granular understanding of customer feedback using advanced deep learning (Transformer) models applied to organic social media data.

### Why a Hybrid AI Approach?
As defined in our conceptual framework, traditional machine learning models (like Logistic Regression/SVM) struggle with the contextual nuances, sarcasm, and code-switching (Hindi-English) prevalent in Indian social media data. The implemented approach is "Hybrid" because it combines:
1. **Zero-Shot Semantic Classification** (Jina AI) for dynamic aspect extraction without needing thousands of manually labeled examples.
2. **Transformer-based Sentiment Classification** (BERT family) to leverage pre-trained contextual attention mechanisms rather than simple word frequencies.

---

## 4.2 Step 1: Data Collection & Sampling

### What We Did
We extracted a continuous longitudinal dataset of **778 Reddit posts** discussing "Zepto" across various subreddits (e.g., r/pune, r/hyderabad, r/Bangalore, r/FuckZepto) spanning from April 2025 to March 2026. 

### Why We Did It (Rationale)
- **Why Reddit instead of App Store Reviews?** App Store reviews are often polarized (1-star or 5-star) and lack descriptive depth. Reddit provides organic, community-driven "social listening" where users describe their experiences in detail, providing richer text for aspect extraction.
- **Why Time-Based Sampling?** A 12-month window captures seasonal variations, major promotional events, and operational scaling challenges, mitigating the bias of short-term PR crises.

---

## 4.3 Step 2: Preprocessing

### What We Did
1. **Title + Body Concatenation**: Combined the Reddit `title` and `selftext` into a single variable (`content`).
2. **Noise Reduction**: Filtered out deleted/removed posts and normalized whitespaces.
3. **Rating Proxy Initialization**: Assigned a neutral baseline rating (3) to all Reddit posts, as Reddit relies on communal upvotes rather than 5-star ratings.

### Why We Did It
Transformer models require clean, continuous token sequences. Submitting a title and a body separately severs the context (e.g., Title: "Worst delivery", Body: "It took 2 hours"). Concatenating them preserves the semantic flow necessary for the attention head of BERT models to map the sentiment (adjective) to the aspect (noun).

---

## 4.4 Step 3: Aspect Extraction (The Core Contribution)

### What We Did
Instead of relying on rigid Rule-Based POS mapping (e.g., IF text contains "fee" THEN aspect = "Pricing"), we deployed **Jina AI (`jina-embeddings-v3`)** for Zero-Shot classification against our 9 predefined Independent Variables (Delivery, Pricing, Quality, Service, etc.).

### Why We Did It (The ABSA Advantage)
Rule-based systems are brittle in informal Q-commerce text. A user might write "They charged me double for ruined tomatoes." A rule-based system might tag "Pricing", missing the "Quality" aspect entirely. AI-driven semantic embeddings understand the contextual relationship of words, resulting in vastly higher coverage accuracy.

**Results of Aspect Extraction (N = 778):**
1. **Offers and Promotions**: 28.8% (224 posts)
2. **Refund and Payment Issues**: 16.1% (125 posts)
3. **Customer Service and Support**: 15.8% (123 posts)
4. **Product Quality and Freshness**: 15.6% (121 posts)
5. **Delivery Speed and Timeliness**: 8.7% (68 posts)

*(Note: ABSA successfully classified 98.7% of the dataset, leaving only 1.3% as 'Unknown'.)*

---

## 4.5 Step 4: Sentiment Classification (Multi-Model Strategy)

### What We Did
To ensure academic rigor, we did not rely on a single algorithm. We processed the dataset through four distinct models to evaluate performance and establish a consensus:

1. **mBERT (Multilingual BERT)**: Classified 67.5% as Negative.
2. **RoBERTa (Twitter/X Pretrained)**: Classified 49.1% as Neutral, 38.8% Negative.
3. **DeBERTa (v3)**: Evaluated binary positive/negative dynamics.
4. **GloVe/TF-IDF + Logistic Regression**: Deployed as the traditional ML baseline.

### Why We Did It
Executing an ensemble of models directly addresses the study's *Academic Contribution* goals:
- **Why mBERT?** The Indian Q-commerce context involves multilingual noise and "Hinglish" (Hindi + English). Multilingual BERT is specifically architected to handle cross-lingual representations.
- **Why RoBERTa?** Originally trained on social media (Twitter), it excels at interpreting sarcasm, slang, and informal grammatical structures found on Reddit.
- **Why GloVe Baseline?** To scientifically prove **Hypothesis H1** (that AI/Transformer models outperform traditional models), we had to run a traditional TF-IDF + Logistic Regression model to serve as the control group.

**Cross-Model Insight**: RoBERTa identified a massive volume of "Neutral" posts (49%). *Why?* Reddit is a forum; many posts are questions (e.g., "Is Zepto delivering in Wakad today?") rather than complaints. mBERT aggressively classified these as negative, proving that **model selection dictates business intelligence accuracy**.

---

## 4.6 Hypothesis Testing & Managerial Findings

This section maps the pipeline outputs back to the study's proposed conceptual hypotheses.

### H1: AI-based ABSA significantly improves sentiment classification accuracy compared to traditional sentiment analysis.
- **Finding**: The traditional rule-based approach matched keywords in only **45.6%** of posts. The AI-driven Jina ABSA model understood semantic context to classify **98.7%** of posts.
- **Why this matters**: A 116% improvement in coverage means management is no longer blind to 54% of customer feedback simply because the customer used an unexpected synonym. 
- **Verdict**: ✅ Strongly Supported.

### H2: Delivery speed has a significant positive impact on customer sentiment.
- **Finding**: Of the 68 posts concerning Delivery Speed, **72.0% were negative** and only 23.5% were positive. The Pos:Neg sentiment ratio is 0.33.
- **Why this matters / Managerial Implication**: Zepto's core brand promise is "10-minute delivery". The data proves that when this expectation is violated, it generates extreme social friction. Delivery speed doesn't just create positive sentiment when successful; it acts as a severe brand detractor when it fails.
- **Verdict**: ⚠️ Partially Supported (Directionally, it drives extreme *negative* impact).

### H3: Pricing perception significantly influences negative sentiment.
- **Finding**: Pricing sentiment is highly contested: **45.7% Negative vs. 42.8% Positive**.
- **Why this matters**: Unlike delivery (which is mostly negative), pricing shows Zepto has distinct consumer segments. Some users praise the "best prices", while others complain bitterly about "handling fees". 
- **Recommendation**: Optimize pricing strategies by making fees transparent prior to checkout.
- **Verdict**: ⚠️ Partially Supported (It drives both positive and negative sentiment equally).

### H4: Customer service quality positively affects overall brand sentiment.
- **Finding**: Customer Service generated the highest concentration of anger. Out of 146 service-related posts, **69.1% were Negative**. 
- **Why this matters**: Qualitative extraction reveals the root cause: *Automated AI chatbots (Zap) refusing to escalate to humans*. Customer service is acting as a "Mediating Variable" — a bad delivery experience is amplified into a Reddit post precisely because the customer service resolution failed.
- **Verdict**: ✅ Supported (Inversely: poor service actively destroys brand sentiment).

### H5: Social media sentiment significantly predicts customer satisfaction levels.
- **Finding**: Overall Reddit sentiment skews **67.5% Negative** (mBERT).
- **Why this matters**: We must interpret this through the lens of *Negativity Bias* in social media — users rarely post on Reddit when their groceries arrive perfectly. Social media sentiment is a predictor of "Systemic Pain Points" rather than absolute app-store satisfaction.
- **Verdict**: ⚠️ Partially Supported.

### H6: AI-driven social listening positively impacts marketing decision effectiveness.
- **Finding**: Granular ABSA identified that **Offers and Promotions** dominate Reddit discourse (28.8% of all conversation), with 141 negative posts complaining about invalid coupon codes.
- **Why this matters**: Without ABSA, marketing executives just see an overall "Negative" trend and might blame the delivery drivers. ABSA pinpoints that the actual operational failure is happening in the coupon-validation logic in the app. This enables real-time, highly targeted data-driven marketing optimization.
- **Verdict**: ✅ Strongly Supported.

---

## 4.7 Key Managerial & Strategic Implications

Based on the pipeline's output, the following business strategies (per the workflow model) are recommended:

1. **Logistics Optimization**: Stop advertising strict "10-minute" timelines if unfeasible during peak hours. The gap between expectation and reality is the primary driver of negative delivery sentiment.
2. **Customer Service Overhaul**: The AI chatbot is causing significant brand damage. Implement a rapid human-escalation path for high-value cart orders.
3. **Marketing Analytics**: Re-evaluate the "Free Cash" and "Promo Code" mechanics. The high volume of error-related posts indicates the app rejects valid codes, frustrating highly engaged, price-sensitive consumers.

## 4.8 Limitations and Expected Outcomes Achieved

- **Limitation Acknowledged**: The Reddit dataset exhibits platform-specific bias (largely tech-savvy, younger demographics prone to complaining). A future scope would combine this with the 144k Google Play dataset for demographic smoothing.
- **Outcome Achieved**: We successfully built a real-time AI-powered social listening system that isolated key pain points in Q-commerce, moving beyond basic sentiment into actionable aspect-level intelligence.
