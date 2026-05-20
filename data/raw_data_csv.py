import pandas as pd
from pymongo import MongoClient
import os

if not os.path.exists("data"):
    os.makedirs("data")

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["diseasescope"]
    collection = db["articles_tous"]

    data = list(collection.find())
    if not data:
        print("Error: the 'articles_tous' collection is empty. Run fusionner.py first.")
    else:
        df = pd.DataFrame(data)
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)
        df.to_csv("data/raw_articles_complet.csv", index=False, encoding="utf-8-sig")
        print(f"Done. {len(df)} articles exported to data/raw_articles_complet.csv")

except Exception as e:
    print(f"Export error: {e}")
