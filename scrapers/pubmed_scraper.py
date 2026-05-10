
import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_pubmed"]
maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]

def scraper_pubmed(maladie):
    print(f"\n Scraping PubMed : {maladie}")

    url_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params_search = {
        "db": "pubmed",
        "term": maladie,
        "retmax": 200,
        "retmode": "json",
        "sort": "date"
    }

    try:
        r = requests.get(url_search, params=params_search, timeout=15)
        r.raise_for_status()
        ids = r.json()["esearchresult"]["idlist"]
        print(f"   {len(ids)} articles trouves")
    except Exception as e:
        print(f"   Erreur recherche : {e}")
        return 0

    if not ids:
        return 0

    url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params_fetch = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}

    try:
        r2 = requests.get(url_fetch, params=params_fetch, timeout=15)
        r2.raise_for_status()
        data = r2.json()
    except Exception as e:
        print(f"   Erreur details : {e}")
        return 0

    sauvegardes = 0
    for id_article in ids:
        try:
            info = data["result"][id_article]
            doc = {
                "titre": info.get("title", "Sans titre"),
                "resume": "",
                "auteurs": [a["name"] for a in info.get("authors", [])],
                "date_publication": info.get("pubdate", "Inconnue"),
                "journal": info.get("source", "Inconnu"),
                "mots_cles": [],
                "maladie": maladie,
                "source": "PubMed",
                "lien": f"https://pubmed.ncbi.nlm.nih.gov/{id_article}/",
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }
            if not collection.find_one({"lien": doc["lien"]}):
                collection.insert_one(doc)
                sauvegardes += 1
        except Exception as e:
            continue

    print(f"   {sauvegardes} sauvegardes")
    time.sleep(1)
    return sauvegardes

if __name__ == "__main__":
    print("===== PubMed Scraper =====")
    total = 0
    for m in maladies:
        total += scraper_pubmed(m)
    print(f"\nTotal : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")