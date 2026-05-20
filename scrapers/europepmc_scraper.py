import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_europe_pmc"]
maladies = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases"
]
def scraper_europe_pmc(maladie):
    print(f"\n Scraping Europe PMC : {maladie}")

    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": maladie,
        "resultType": "core",
        "pageSize": 200,
        "format": "json",
        "sort": "CITED desc"
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        articles = r.json().get("resultList", {}).get("result", [])
        print(f"   {len(articles)} articles trouves")
    except Exception as e:
        print(f"   Erreur : {e}")
        return 0

    sauvegardes = 0
    for article in articles:
        try:
            pmid = article.get("pmid", "")
            pmcid = article.get("pmcid", "")
            unique_id = pmid or pmcid or article.get("id", "")

            auteur_list = article.get("authorList", {}).get("author", [])
            auteurs = [
                f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
                for a in auteur_list
                if f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
            ]
            if not auteurs and article.get("authorString"):
                auteurs = [a.strip() for a in article.get("authorString", "").split(",") if a.strip()]

            mots_cles = article.get("keywordList", {}).get("keyword", [])
            if maladie not in mots_cles:
                mots_cles.append(maladie)

            if pmid:
                lien = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            elif pmcid:
                lien = f"https://europepmc.org/article/PMC/{pmcid}"
            else:
                lien = ""

            doc = {
                "titre": article.get("title", "Sans titre"),
                "resume": article.get("abstractText") or article.get("title", ""),
                "auteurs": auteurs,
                "date_publication": article.get("firstPublicationDate", "Inconnue"),
                "journal": article.get("journalTitle", "Inconnu"),
                "mots_cles": mots_cles,
                "maladie": maladie,
                "source": "Europe PMC",
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
    time.sleep(1)
    return sauvegardes

if __name__ == "__main__":
    print("=== Europe PMC Scraper ===")
    total = 0
    for m in maladies:
        total += scraper_europe_pmc(m)
    print(f"\nTotal : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")
