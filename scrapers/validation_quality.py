from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]


def validate_data():
    data = list(db["articles_tous"].find())
    if not data:
        print("The database is empty. Run fusionner.py first.")
        return

    df = pd.DataFrame(data)

    print("\n--- STATISTICS BY DISEASE ---")
    print(df["maladie"].value_counts())

    print("\n--- MISSING DATA RATES ---")
    missing = df.isnull().mean() * 100
    print(missing)

    for col, pct in missing.items():
        if pct > 15:
            print(f"ALERT: Column '{col}' has too many missing values ({pct:.2f}%)")


if __name__ == "__main__":
    validate_data()
