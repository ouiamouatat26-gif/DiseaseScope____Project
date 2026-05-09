import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_europe_pmc"]

maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]


def scraper_europe_pmc(maladie):
    """Scrape Europe PMC pour une maladie donnée et sauvegarde dans MongoDB."""

    print(f"\n Scraping Europe PMC pour : {maladie}")

    #Recherche des articles 
    url_search = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params_search = {
        "query": maladie,
        "resultType": "core",       # Retourne les métadonnées complètes
        "pageSize": 80,
        "format": "json",
        "sort": "CITED desc"        # Les plus cités en premier
    }

    response_search = requests.get(url_search, params=params_search)
    response_search.raise_for_status()
    data_search = response_search.json()

    articles = data_search.get("resultList", {}).get("result", [])
    print(f"   → {len(articles)} articles trouvés")

    articles_sauvegardes = 0

    for article in articles:
        try:
            pmid = article.get("pmid", "")
            pmcid = article.get("pmcid", "")

            # Clé unique : pmid si dispo, sinon pmcid, sinon id Europe PMC
            unique_id = pmid or pmcid or article.get("id", "")

            # Extraction des auteurs
            auteur_list = article.get("authorList", {}).get("author", [])
            auteurs = [
                f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
                for a in auteur_list
            ]

            # Extraction des mots-clés
            keyword_list = article.get("keywordList", {}).get("keyword", [])

            doc = {
                "titre": article.get("title", "Sans titre"),
                "auteurs": auteurs,
                "date_publication": article.get("firstPublicationDate", "Inconnue"),
                "journal": article.get("journalTitle", "Inconnu"),
                "resume": article.get("abstractText", ""),
                "mots_cles": keyword_list,
                "citations": article.get("citedByCount", 0),
                "doi": article.get("doi", ""),
                "pmid": pmid,
                "pmcid": pmcid,
                "maladie": maladie,
                "source": "Europe PMC",
                "europe_pmc_id": unique_id,
                "date_scraping": datetime.now()
            }

            # Évite les doublons
            existant = collection.find_one({"europe_pmc_id": unique_id})
            if not existant:
                collection.insert_one(doc)
                articles_sauvegardes += 1

        except Exception as e:
            print(f"   Erreur sur un article : {e}")

    print(f"    {articles_sauvegardes} nouveaux articles sauvegardés")

    time.sleep(1)


if __name__ == "__main__":
    print(" Démarrage du scraping Europe PMC...")
    print("=" * 50)

    for maladie in maladies:
        scraper_europe_pmc(maladie)

    total = collection.count_documents({})
    print("\n" + "=" * 50)
    print(f" Scraping terminé !")
    print(f" Total articles dans MongoDB : {total}")