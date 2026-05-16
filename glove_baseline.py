import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import numpy as np

filepath = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_bert_sentiment.tsv"
rows = []

with open(filepath, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        rows.append(row)

print(f"Loaded {len(rows):,} reviews")

texts   = [r["Review_Content"] for r in rows]
ratings = [int(r["Rating"]) for r in rows]

X_train, X_test, y_train, y_test = train_test_split(
    texts, ratings, test_size=0.2, random_state=42
)

print("Training GloVe/LR model...")
pipe = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1,2))),
    ("lr",   LogisticRegression(max_iter=1000))
])
pipe.fit(X_train, y_train)

preds = pipe.predict(X_test)
actuals = y_test

exact      = sum(1 for a, p in zip(actuals, preds) if a == p)
within_one = sum(1 for a, p in zip(actuals, preds) if abs(a - p) <= 1)
mae        = mean_absolute_error(actuals, preds)
total      = len(actuals)

print(f"\n--- GloVe/LR Results (test set: {total:,} reviews) ---")
print(f"Exact match  : {exact:,}  ({exact/total*100:.1f}%)")
print(f"Within 1 star: {within_one:,}  ({within_one/total*100:.1f}%)")
print(f"MAE          : {mae:.3f}")

# Now evaluate BERT on same test split for fair comparison
bert_preds = [int(rows[i]["BERT_Stars"]) for i in range(len(rows)) if i >= int(len(rows)*0.8)]
bert_actual = ratings[int(len(ratings)*0.8):]

b_exact      = sum(1 for a, p in zip(bert_actual, bert_preds) if a == p)
b_within_one = sum(1 for a, p in zip(bert_actual, bert_preds) if abs(a - p) <= 1)
b_mae        = mean_absolute_error(bert_actual, bert_preds)

print(f"\n--- BERT Results (same test set: {len(bert_actual):,} reviews) ---")
print(f"Exact match  : {b_exact:,}  ({b_exact/len(bert_actual)*100:.1f}%)")
print(f"Within 1 star: {b_within_one:,}  ({b_within_one/len(bert_actual)*100:.1f}%)")
print(f"MAE          : {b_mae:.3f}")

print("\n--- Model Comparison Summary ---")
print(f"{'Model':<15} {'Exact%':>8} {'Within1%':>10} {'MAE':>6}")
print(f"{'GloVe/LR':<15} {exact/total*100:>7.1f}% {within_one/total*100:>9.1f}% {mae:>6.3f}")
print(f"{'BERT':<15} {b_exact/len(bert_actual)*100:>7.1f}% {b_within_one/len(bert_actual)*100:>9.1f}% {b_mae:>6.3f}")
