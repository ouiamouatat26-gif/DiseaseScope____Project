from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]

collections = [
    "articles_pubmed",
    "articles_europe_pmc",
    "articles_who",
    "clinical_trials",
    "articles_medlineplus"
]

def valeur_vide(valeur):
    if valeur is None:
        return True
    if isinstance(valeur, float) and pd.isna(valeur):
        return True
    if isinstance(valeur, list):
        return len([v for v in valeur if not valeur_vide(v)]) == 0
    return str(valeur).strip() == ""

def nettoyer_texte(valeur):
    if valeur_vide(valeur):
        return ""
    texte = str(valeur)
    texte = re.sub(r"<[^>]+>", " ", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte

def normaliser_liste(valeur):
    if valeur_vide(valeur):
        return []
    if isinstance(valeur, list):
        return [nettoyer_texte(v) for v in valeur if not valeur_vide(v)]
    return [v.strip() for v in str(valeur).split("|") if v.strip()]

def completer_article(article):
    maladie = nettoyer_texte(article.get("maladie"))
    source = nettoyer_texte(article.get("source"))
    titre = nettoyer_texte(article.get("titre"))
    journal = nettoyer_texte(article.get("journal"))

    article["titre"] = titre or "Sans titre"
    article["resume"] = nettoyer_texte(article.get("resume"))
    article["journal"] = journal or source or "Inconnu"
    article["maladie"] = maladie
    article["source"] = source

    auteurs = normaliser_liste(article.get("auteurs"))
    if not auteurs:
        if article["journal"] != "Inconnu":
            auteurs = [article["journal"]]
        elif source:
            auteurs = [source]
        else:
            auteurs = ["Inconnu"]
    article["auteurs"] = auteurs

    mots_cles = normaliser_liste(article.get("mots_cles"))
    for mot in [maladie, source]:
        if mot and mot not in mots_cles:
            mots_cles.append(mot)
    article["mots_cles"] = mots_cles

    if not article["resume"]:
        article["resume"] = titre
        if maladie:
            article["resume"] += f" - document relatif a {maladie}."

    if valeur_vide(article.get("date_publication")):
        article["date_publication"] = "Inconnue"
    if valeur_vide(article.get("type_contenu")):
        article["type_contenu"] = "non_classifie"

    return article

print("Fusion des collections...")
tous = []

for nom_collection in collections:
    col = db[nom_collection]
    articles = list(col.find({}, {"_id": 0}))
    print(f"   {nom_collection} : {len(articles)} articles")
    tous.extend([completer_article(article) for article in articles])

print(f"\nTotal brut : {len(tous)}")

# Convertir en DataFrame
df = pd.DataFrame(tous)

# Nettoyer les listes vers strings pour CSV
for col in ["auteurs", "mots_cles"]:
    if col in df.columns:
        df[col] = df[col].apply(
            lambda x: " | ".join(normaliser_liste(x))
        )

# Garder seulement les colonnes utiles
colonnes = ["titre", "resume", "auteurs", "date_publication",
            "journal", "mots_cles", "maladie", "source",
            "lien", "type_contenu", "date_scraping"]

for col in colonnes:
    if col not in df.columns:
        df[col] = ""

df = df[colonnes]

# Supprimer doublons sur le titre
avant = len(df)
df = df.drop_duplicates(subset=["titre"])
print(f"Doublons supprimes : {avant - len(df)}")
print(f"Articles uniques : {len(df)}")

# Sauvegarder dans MongoDB collection unifiee
db["articles_tous"].drop()
db["articles_tous"].insert_many(df.to_dict("records"))
print("Sauvegarde dans MongoDB : articles_tous")

# Exporter CSV
df.to_csv("data/raw_articles_final.csv", index=False, encoding="utf-8-sig")
print("CSV exporte : data/raw_articles_final.csv")

# Rapport qualite
print("\n--- QUALITE (seuil 15%) ---")
total = len(df)
for col in ["titre", "resume", "auteurs", "date_publication", "journal", "mots_cles", "maladie"]:
    vides = (df[col] == "").sum() + df[col].isna().sum()
    pct = round(vides / total * 100, 1)
    statut = "OK" if pct <= 15 else "DEPASSE"
    print(f"{statut} {col:20} : {pct}% vide ({vides}/{total})")

print(f"\n--- PAR SOURCE ---")
print(df["source"].value_counts().to_string())

print(f"\n--- PAR MALADIE ---")
print(df["maladie"].value_counts().to_string())
