from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]

COLLECTIONS = [
    "articles_pubmed",
    "articles_europe_pmc",
    "articles_who",
    "clinical_trials",
    "articles_medlineplus",
]


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, list):
        return len([v for v in value if not is_empty(v)]) == 0
    return str(value).strip() == ""


def clean_text(value):
    if is_empty(value):
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_list(value):
    if is_empty(value):
        return []
    if isinstance(value, list):
        return [clean_text(v) for v in value if not is_empty(v)]
    return [v.strip() for v in str(value).split("|") if v.strip()]


def complete_article(article):
    disease = clean_text(article.get("maladie"))
    source = clean_text(article.get("source"))
    title = clean_text(article.get("titre"))
    journal = clean_text(article.get("journal"))

    article["titre"] = title or "Untitled"
    article["resume"] = clean_text(article.get("resume"))
    article["journal"] = journal or source or "Unknown"
    article["maladie"] = disease
    article["source"] = source

    authors = normalize_list(article.get("auteurs"))
    if not authors:
        if article["journal"] != "Unknown":
            authors = [article["journal"]]
        elif source:
            authors = [source]
        else:
            authors = ["Unknown"]
    article["auteurs"] = authors

    keywords = normalize_list(article.get("mots_cles"))
    for word in [disease, source]:
        if word and word not in keywords:
            keywords.append(word)
    article["mots_cles"] = keywords

    if not article["resume"]:
        article["resume"] = title
        if disease:
            article["resume"] += f" — document related to {disease}."

    if is_empty(article.get("date_publication")):
        article["date_publication"] = "Unknown"
    if is_empty(article.get("type_contenu")):
        article["type_contenu"] = "non_classifie"

    return article


print("Merging collections...")
all_articles = []

for collection_name in COLLECTIONS:
    col = db[collection_name]
    articles = list(col.find({}, {"_id": 0}))
    print(f"  {collection_name}: {len(articles)} articles")
    all_articles.extend([complete_article(a) for a in articles])

print(f"\nRaw total: {len(all_articles)}")

if not all_articles:
    print("No articles found. Run the scrapers first.")
    exit(1)

df = pd.DataFrame(all_articles)

for col in ["auteurs", "mots_cles"]:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: " | ".join(normalize_list(x)))

COLUMNS = [
    "titre", "resume", "auteurs", "date_publication",
    "journal", "mots_cles", "maladie", "source",
    "lien", "type_contenu", "date_scraping",
]

for col in COLUMNS:
    if col not in df.columns:
        df[col] = ""

df = df[COLUMNS]

before = len(df)
df = df[df["lien"] != ""]
df = df.drop_duplicates(subset=["lien"])
df = df.drop_duplicates(subset=["titre", "source"])
print(f"Duplicates removed: {before - len(df)}")
print(f"Unique articles: {len(df)}")

db["articles_tous"].drop()
db["articles_tous"].insert_many(df.to_dict("records"))
print("Saved to MongoDB: articles_tous")

df.to_csv("data/raw_articles_final.csv", index=False, encoding="utf-8-sig")
print("CSV exported: data/raw_articles_final.csv")

print("\n--- QUALITY CHECK (15% threshold) ---")
total = len(df)
for col in ["titre", "resume", "auteurs", "date_publication", "journal", "mots_cles", "maladie"]:
    empty = (df[col] == "").sum() + df[col].isna().sum()
    pct = round(empty / total * 100, 1)
    status = "OK" if pct <= 15 else "EXCEEDS THRESHOLD"
    print(f"{status:20} {col:20}: {pct}% empty ({empty}/{total})")

print("\n--- BY SOURCE ---")
print(df["source"].value_counts().to_string())

print("\n--- BY DISEASE ---")
print(df["maladie"].value_counts().to_string())