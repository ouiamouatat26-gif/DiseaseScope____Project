import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import os

df = pd.read_csv("data/articles_etiquetes.csv", encoding="utf-8-sig")
df = df[df["texte"].notna() & (df["texte"] != "")]
print(f"Articles : {len(df)}")

X = df["texte"]
y = df["type_contenu"]

vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2), stop_words="english")
X_vec = vectorizer.fit_transform(X)
print(f"TF-IDF : {X_vec.shape}")

le = LabelEncoder()
y_enc = le.fit_transform(y)
print(f"Classes : {list(le.classes_)}")

X_train, X_test, y_train, y_test = train_test_split(X_vec, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\n✅ Accuracy : {round(acc*100, 2)}%")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# Créer le dossier "models" s'il n'existe pas
os.makedirs("models", exist_ok=True)

joblib.dump(model,      "models/random_forest.joblib")
joblib.dump(vectorizer, "models/tfidf.joblib")
joblib.dump(le,         "models/label_encoder.joblib")
json.dump({"accuracy": round(acc*100,2), "classes": list(le.classes_), "n_articles": len(df)},
          open("models/metrics.json","w"), indent=2)

print(" Modèle sauvegardé dans models/")
