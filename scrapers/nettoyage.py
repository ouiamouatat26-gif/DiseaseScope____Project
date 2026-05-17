from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]

print("Chargement des donnees...")
articles = list(db["articles_tous"].find({}, {"_id": 0}))
df = pd.DataFrame(articles)
print(f"Total avant nettoyage : {len(df)}")

print("\nETAPE 1 - Titres vides...")
avant = len(df)
df = df[df["titre"].notna()]
df = df[df["titre"] != "Sans titre"]
df = df[df["titre"].str.len() > 10]
print(f"Supprimes : {avant - len(df)}")

print("\nETAPE 2 - Doublons...")
avant = len(df)
df = df.drop_duplicates(subset=["titre", "maladie"])
print(f"Doublons supprimes : {avant - len(df)}")

print("\nETAPE 3 - Dates...")
def nettoyer_date(date_str):
    if not date_str or str(date_str) == "Inconnue":
        return "Inconnue"
    date_str = str(date_str).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    if re.match(r"\d{4}", date_str):
        return date_str[:4]
    return "Inconnue"

df["date_publication"] = df["date_publication"].apply(nettoyer_date)
print("Dates uniformisees")

print("\nETAPE 4 - Texte...")
df["titre"] = df["titre"].str.strip()
df["titre"] = df["titre"].str.replace(r"\s+", " ", regex=True)
df["resume"] = df["resume"].fillna("")
df["maladie"] = df["maladie"].str.lower().str.strip()
df["auteurs"] = df["auteurs"].apply(
    lambda x: x if isinstance(x, list) else []
)
df["mots_cles"] = df["mots_cles"].apply(
    lambda x: x if isinstance(x, list) else []
)
print("Texte nettoye")

print(f"\nTotal apres nettoyage : {len(df)}")
print("\nPar maladie :")
print(df["maladie"].value_counts())
print("\nPar source :")
print(df["source"].value_counts())

print("\nSauvegarde MongoDB...")
col_propre = db["articles_propres"]
col_propre.drop()
col_propre.insert_many(df.to_dict("records"))
print(f"articles_propres : {col_propre.count_documents({})} articles")

print("\nExport CSV propre...")
df.to_csv("data/articles_propres_v1.0.csv",
          index=False, encoding="utf-8-sig")
print("CSV cree : data/articles_propres_v1.0.csv")
print("\nNettoyage termine !")