import csv
import torch
from transformers import pipeline

INPUT  = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_apr2025_mar2026_nvivo.tsv"
OUTPUT = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_bert_sentiment.tsv"

print("Loading BERT model...")
classifier = pipeline(
    "text-classification",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=0 if torch.cuda.is_available() else -1
)

def stars_to_label(stars):
    if stars >= 4: return "positive"
    if stars == 3: return "neutral"
    return "negative"

rows = []
with open(INPUT, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    fieldnames = list(reader.fieldnames)
    for row in reader:
        rows.append(row)

print(f"Loaded {len(rows):,} reviews. Starting BERT scoring...")


BATCH = 32
with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
    out_fields = fieldnames + ["BERT_Stars", "BERT_Sentiment", "BERT_Confidence"]
    writer = csv.DictWriter(f, fieldnames=out_fields, delimiter="\t")
    writer.writeheader()

    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        texts = [r["Review_Content"][:512] for r in batch]

        try:
            results = classifier(texts, truncation=True, max_length=512)
        except Exception as e:
            print(f"  Batch {i} error: {e}")
            results = [{"label": "3 stars", "score": 0.0}] * len(batch)

        for row, res in zip(batch, results):
            stars = int(res["label"][0])
            row["BERT_Stars"]      = stars
            row["BERT_Sentiment"]  = stars_to_label(stars)
            row["BERT_Confidence"] = round(res["score"], 4)
            writer.writerow(row)

        if i % 1000 == 0:
            print(f"  Processed {i:,} / {len(rows):,}")

print(f"\nDone! Output saved to:\n{OUTPUT}")
