import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

filepath = r"C:\Users\saini\reviewanalyser\output\zepto_reviews_bert_sentiment.tsv"
rows = []

with open(filepath, encoding="utf-8-sig") as f:
    reader
