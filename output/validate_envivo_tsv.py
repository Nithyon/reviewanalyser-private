import csv

filepath = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_apr2025_mar2026_nvivo.tsv"

expected_cols = 9  # Review_ID, Author, Rating, Date, Review_Content, Thumbs_Up, Official_Reply, Reply_Date, App_Version

total_rows = 0
bad_rows = []
empty_review = 0
missing_rating = 0
rating_values = set()

with open(filepath, encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    print(f"Header ({len(header)} cols): {header}\n")

    for i, row in enumerate(reader, start=2):
        total_rows += 1
        if len(row) != expected_cols:
            bad_rows.append((i, len(row), row[:3]))
        else:
            review_text = row[4].strip()
            rating = row[2].strip()
            if not review_text:
                empty_review += 1
            if not rating:
                missing_rating += 1
            else:
                rating_values.add(rating)

print(f"Total data rows:               {total_rows:,}")
print(f"Rows with wrong column count:  {len(bad_rows)}")
if bad_rows:
    print(f"  --> First 5 bad rows: {bad_rows[:5]}")
print(f"Rows with empty Review_Content:{empty_review}")
print(f"Rows with missing Rating:      {missing_rating}")
print(f"Unique rating values found:    {sorted(rating_values)}")
status = "CLEAN - All good!" if len(bad_rows) == 0 else "BROKEN - needs repair"
print(f"\nFile looks {status}")

