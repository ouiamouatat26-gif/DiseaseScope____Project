from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection_finale = db["articles_tous"]
maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]
sources = ["articles_pubmed", "articles_europe_pmc", "articles_who", "clinical_trials"]

print("===== Fusion des collections =====")

total = 0
doublons = 0

for nom in sources:
    col = db[nom]
    articles = list(col.find({}))
    print(f"\n {nom} : {len(articles)} articles")

    for article in articles:
        try:
            doc = {
                "titre": article.get("titre", "Sans titre"),
                "resume": article.get("resume", ""),
                "auteurs": article.get("auteurs", []),
                "date_publication": article.get("date_publication", "Inconnue"),
                "journal": article.get("journal", "Inconnu"),
                "mots_cles": article.get("mots_cles", []),
                "maladie": article.get("maladie", "general"),
                "source": article.get("source", "Inconnu"),
                "lien": article.get("lien", ""),
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            existant = collection_finale.find_one({
                "lien": doc["lien"],
                "maladie": doc["maladie"]
            })

            if not existant and doc["lien"]:
                collection_finale.insert_one(doc)
                total += 1
            else:
                doublons += 1

        except Exception as e:
            continue

print(f"\n===== Resultat =====")
print(f"Total fusionne : {total}")
print(f"Doublons ignores : {doublons}")
print(f"Total articles_tous : {collection_finale.count_documents({})}")

print("\nPar maladie :")
for m in maladies:
    print(f"   {m} : {collection_finale.count_documents({'maladie': m})}")

print("\nPar source :")
for s in ["PubMed", "Europe PMC", "WHO", "ClinicalTrials"]:
    print(f"   {s} : {collection_finale.count_documents({'source': s})}")