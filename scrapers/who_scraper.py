import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_who"]

DISEASES = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://iris.who.int/",
})


def scrape_who(disease):
    print(f"Scraping WHO: {disease}")

    try:
        session.get("https://iris.who.int/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    url = "https://iris.who.int/server/api/discover/search/objects"
    params = {
        "query": disease,
        "page": 0,
        "size": 100,
        "sort": "score,DESC",
    }

    try:
        r = session.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  Error: {e}")
        return 0

    objects = (
        data.get("_embedded", {})
        .get("searchResult", {})
        .get("_embedded", {})
        .get("objects", [])
    )
    print(f"  {len(objects)} articles found")

    saved = 0
    for obj in objects:
        try:
            item = obj.get("_embedded", {}).get("indexableObject", {})
            uuid = item.get("uuid", "")
            if not uuid:
                continue

            metadata_list = item.get("metadata", {})
            meta = {
                key: [v.get("value", "") for v in values]
                for key, values in metadata_list.items()
            }

            identifiers = meta.get("dc.identifier.uri", [])
            link = next((i for i in identifiers if i.startswith("http")), "")
            title = meta.get("dc.title", ["Untitled"])[0]
            abstract = meta.get("dc.description.abstract", [""])[0]
            if not abstract:
                descriptions = meta.get("dc.description", [])
                abstract = descriptions[0] if descriptions else title

            keywords = meta.get("dc.subject", [])
            if disease not in keywords:
                keywords.append(disease)

            doc = {
                "titre": title,
                "resume": abstract,
                "auteurs": meta.get("dc.contributor.author", []) or ["WHO"],
                "date_publication": meta.get("dc.date.issued", ["Unknown"])[0],
                "journal": meta.get("dc.publisher", ["WHO"])[0],
                "mots_cles": keywords,
                "maladie": disease,
                "source": "WHO",
                "lien": link,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now(),
            }

            if not collection.find_one({"lien": link}) and link:
                collection.insert_one(doc)
                saved += 1

        except Exception:
            continue

    print(f"  {saved} saved")
    time.sleep(2)
    return saved


if __name__ == "__main__":
    print("=== WHO Scraper ===")
    total = 0
    for d in DISEASES:
        total += scrape_who(d)
    print(f"\nTotal saved: {total}")
    print(f"Total in MongoDB: {collection.count_documents({})}")
    for d in DISEASES:
        print(f"  {d}: {collection.count_documents({'maladie': d})}")
