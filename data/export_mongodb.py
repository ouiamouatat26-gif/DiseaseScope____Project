import pandas as pd
from pymongo import MongoClient
import ast

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_tous"]

print("📥 Export depuis MongoDB...")

articles = list(collection.find({}, {"_id": 0}))
print(f"   → {len(articles)} articles trouvés dans MongoDB")

rows = []
for article in articles:
    auteurs = article.get("auteurs", [])
    if isinstance(auteurs, list):
        auteurs_str = " | ".join(auteurs)
    else:
        auteurs_str = str(auteurs)

    mots_cles = article.get("mots_cles", [])
    if isinstance(mots_cles, list):
        mots_cles_str = " | ".join(mots_cles)
    else:
        mots_cles_str = str(mots_cles)

    row = {
        "titre": str(article.get("titre", "")),
        "resume": str(article.get("resume", "")),
        "auteurs": auteurs_str,
        "date_publication": str(article.get("date_publication", "")),
        "journal": str(article.get("journal", "")),
        "mots_cles": mots_cles_str,
        "maladie": str(article.get("maladie", "")),
        "source": str(article.get("source", "")),
        "lien": str(article.get("lien", "")),
        "type_contenu": str(article.get("type_contenu", "non_classifie")),
        "date_scraping": str(article.get("date_scraping", "")),
    }
    rows.append(row)

df = pd.DataFrame(rows)

print(f"\n📊 Vérification avant sauvegarde :")
print(f"   Lignes : {len(df)}")
print(f"   Colonnes : {df.shape[1]}")
print(f"\n   Valeurs manquantes :")
for col in df.columns:
    vides = (df[col] == "") .sum() + df[col].isna().sum()
    pct = round(vides / len(df) * 100, 1)
    print(f"   {col:20} : {vides} vides ({pct}%)")

df.to_csv("data/raw_articles_propre.csv", index=False, encoding="utf-8-sig")
print(f"\n✅ Fichier sauvegardé : data/raw_articles_propre.csv")