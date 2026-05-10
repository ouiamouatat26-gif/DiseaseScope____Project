import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_who"]
maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://iris.who.int/"
})

def scraper_who(maladie):
    print(f"\n Scraping WHO : {maladie}")

    try:
        session.get("https://iris.who.int/", timeout=10)
        time.sleep(1)
    except:
        pass

    url = "https://iris.who.int/server/api/discover/search/objects"
    params = {
        "query": maladie,
        "page": 0,
        "size": 100,
        "sort": "score,DESC"
    }

    try:
        r = session.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"   Erreur : {e}")
        return 0

    objects = (
        data.get("_embedded", {})
        .get("searchResult", {})
        .get("_embedded", {})
        .get("objects", [])
    )
    print(f"   {len(objects)} articles trouves")

    sauvegardes = 0
    for obj in objects:
        try:
            item = obj.get("_embedded", {}).get("indexableObject", {})
            uuid = item.get("uuid", "")
            if not uuid:
                continue

            metadata_list = item.get("metadata", {})
            meta = {
                cle: [v.get("value", "") for v in valeurs]
                for cle, valeurs in metadata_list.items()
            }

            identifiants = meta.get("dc.identifier.uri", [])
            lien = next((i for i in identifiants if i.startswith("http")), "")

            doc = {
                "titre": meta.get("dc.title", ["Sans titre"])[0],
                "resume": meta.get("dc.description.abstract", [""])[0],
                "auteurs": meta.get("dc.contributor.author", []),
                "date_publication": meta.get("dc.date.issued", ["Inconnue"])[0],
                "journal": meta.get("dc.publisher", ["WHO"])[0],
                "mots_cles": meta.get("dc.subject", []),
                "maladie": maladie,
                "source": "WHO",
                "lien": lien,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            if not collection.find_one({"lien": lien}) and lien:
                collection.insert_one(doc)
                sauvegardes += 1
        except Exception as e:
            continue

    print(f"   {sauvegardes} sauvegardes")
    time.sleep(2)
    return sauvegardes

if __name__ == "__main__":
    print("===== WHO Scraper =====")
    total = 0
    for m in maladies:
        total += scraper_who(m)
    print(f"\nTotal : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")