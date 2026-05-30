import pandas as pd
import joblib

df = pd.read_csv("data/raw_articles_final.csv", encoding="utf-8-sig")
df["texte"] = (df["titre"].fillna("") + " " + df["resume"].fillna("")).str.lower()

model      = joblib.load("models/random_forest.joblib")
vectorizer = joblib.load("models/tfidf.joblib")
le         = joblib.load("models/label_encoder.joblib")

X = vectorizer.transform(df["texte"])
df["type_contenu"] = le.inverse_transform(model.predict(X))

print("=== Résultat ===")
print(df["type_contenu"].value_counts())
print(f"Total : {len(df)}")

df.to_csv("data/articles_classifies.csv", index=False, encoding="utf-8-sig")
print("data/articles_classifies.csv créé")
