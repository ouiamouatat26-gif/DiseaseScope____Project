import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_medlineplus"]

DISEASES = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
]

API_URL = "https://wsearch.nlm.nih.gov/ws/query"


def scrape_medlineplus(disease):
    print(f"Scraping MedlinePlus: {disease}")

    params = {
        "db": "healthTopics",
        "term": disease,
        "retmax": 100,
    }

    try:
        r = requests.get(API_URL, params=params, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception as e:
        print(f"  Error: {e}")
        return 0

    documents = root.findall(".//document")
    print(f"  {len(documents)} documents found")

    saved = 0
    for doc in documents:
        try:
            link = doc.get("url", "")
            if not link:
                continue

            def get_content(tag):
                el = doc.find(f".//content[@name='{tag}']")
                return el.text.strip() if el is not None and el.text else ""

            title = get_content("title")
            if not title:
                continue

            abstract = get_content("FullSummary") or get_content("snippet") or title
            abstract = " ".join(ET.fromstring(f"<x>{abstract}</x>").itertext()).strip()

            mesh_terms = [
                el.text.strip()
                for el in doc.findall(".//content[@name='mesh']")
                if el.text
            ]
            if disease not in mesh_terms:
                mesh_terms.append(disease)

            date_updated = get_content("dateUpdated") or datetime.now().strftime("%Y-%m-%d")

            record = {
                "titre": title,
                "resume": abstract[:3000],
                "auteurs": ["MedlinePlus Editorial Team"],
                "date_publication": date_updated,
                "journal": "MedlinePlus",
                "mots_cles": mesh_terms,
                "maladie": disease,
                "source": "MedlinePlus",
                "lien": link,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now(),
            }

            if not collection.find_one({"lien": link}):
                collection.insert_one(record)
                saved += 1

        except Exception:
            continue

    print(f"  {saved} articles saved")
    time.sleep(1)
    return saved


if __name__ == "__main__":
    print("=== MedlinePlus Scraper ===")
    total = 0
    for d in DISEASES:
        total += scrape_medlineplus(d)
    print(f"\nTotal saved: {total}")
    print(f"Total in MongoDB: {collection.count_documents({})}")
    for d in DISEASES:
        print(f"  {d}: {collection.count_documents({'maladie': d})}")