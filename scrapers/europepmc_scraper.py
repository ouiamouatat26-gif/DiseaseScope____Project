import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_europe_pmc"]

DISEASES = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
]


def scrape_europe_pmc(disease):
    print(f"Scraping Europe PMC: {disease}")

    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": disease,
        "resultType": "core",
        "pageSize": 200,
        "format": "json",
        "sort": "CITED desc",
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        articles = r.json().get("resultList", {}).get("result", [])
        print(f"  {len(articles)} articles found")
    except Exception as e:
        print(f"  Error: {e}")
        return 0

    saved = 0
    for article in articles:
        try:
            pmid = article.get("pmid", "")
            pmcid = article.get("pmcid", "")

            author_list = article.get("authorList", {}).get("author", [])
            authors = [
                f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
                for a in author_list
                if f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
            ]
            if not authors and article.get("authorString"):
                authors = [a.strip() for a in article.get("authorString", "").split(",") if a.strip()]

            keywords = article.get("keywordList", {}).get("keyword", [])
            if disease not in keywords:
                keywords.append(disease)

            if pmid:
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            elif pmcid:
                link = f"https://europepmc.org/article/PMC/{pmcid}"
            else:
                link = ""

            doc = {
                "titre": article.get("title", "Untitled"),
                "resume": article.get("abstractText") or article.get("title", ""),
                "auteurs": authors,
                "date_publication": article.get("firstPublicationDate", "Unknown"),
                "journal": article.get("journalTitle", "Unknown"),
                "mots_cles": keywords,
                "maladie": disease,
                "source": "Europe PMC",
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
    time.sleep(1)
    return saved


if __name__ == "__main__":
    print("=== Europe PMC Scraper ===")
    total = 0
    for d in DISEASES:
        total += scrape_europe_pmc(d)
    print(f"\nTotal saved: {total}")
    print(f"Total in MongoDB: {collection.count_documents({})}")
    for d in DISEASES:
        print(f"  {d}: {collection.count_documents({'maladie': d})}")
