import csv
from collections import Counter

filepath = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_apr2025_mar2026_nvivo.tsv"

def detect_script(text):
    hindi     = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    tamil     = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    telugu    = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    kannada   = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
    malayalam = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
    bengali   = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    total = len(text.strip())
    if total == 0:
        return "empty"
    indic = hindi + tamil + telugu + kannada + malayalam + bengali
    if indic / total > 0.3:
        if hindi:     return "hindi"
        if tamil:     return "tamil"
        if telugu:    return "telugu"
        if kannada:   return "kannada"
        if malayalam: return "malayalam"
        if bengali:   return "bengali"
    return "english_or_mixed"

counts = Counter()

with open(filepath, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        counts[detect_script(row.get("Review_Content", ""))] += 1

total = sum(counts.values())
print("Script Distribution:")
for lang, count in counts.most_common():
    print(f"  {lang:<25} {count:>8,}  ({count/total*100:.1f}%)")
