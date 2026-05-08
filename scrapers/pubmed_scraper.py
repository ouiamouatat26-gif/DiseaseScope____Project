
import requests         
from pymongo import MongoClient 
from datetime import datetime   
import time          
# --- CONNEXION À MONGODB ---
client = MongoClient("mongodb://localhost:27017/")

db = client["diseasescope"]
collection = db["articles"]
maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]

def scraper_pubmed(maladie):

    print(f"\n Scraping pour : {maladie}")

    url_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params_search = {
        "db": "pubmed",      
        "term": maladie,    
        "retmax": 80,        
        "retmode": "json"    
    }

    response_search = requests.get(url_search, params=params_search)
    data_search = response_search.json()

    ids = data_search["esearchresult"]["idlist"]
    print(f"   → {len(ids)} articles trouvés")

    # ----------------------------------------
    # ÉTAPE 2 : Récupérer les détails de chaque article
    # ----------------------------------------

    url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    params_fetch = {
        "db": "pubmed",
        "id": ",".join(ids),   # Tous les IDs séparés par des virgules
        "retmode": "json"
    }

    # Récupérer les détails
    response_fetch = requests.get(url_fetch, params=params_fetch)
    data_fetch = response_fetch.json()

    # ----------------------------------------
    # ÉTAPE 3 : Sauvegarder chaque article dans MongoDB
    # ----------------------------------------

    articles_sauvegardes = 0  # Compteur

    for id_article in ids:
        try:
            # Extraire les infos de cet article
            article_info = data_fetch["result"][id_article]

            # Construire la fiche de l'article
            doc = {
                "titre": article_info.get("title", "Sans titre"),
                "auteurs": [a["name"] for a in article_info.get("authors", [])],
                "date_publication": article_info.get("pubdate", "Inconnue"),
                "journal": article_info.get("source", "Inconnu"),
                "maladie": maladie,
                "source": "PubMed",
                "pubmed_id": id_article,
                "date_scraping": datetime.now()
            }

            # Vérifier si l'article existe déjà (éviter les doublons)
            existant = collection.find_one({"pubmed_id": id_article})
            if not existant:
                collection.insert_one(doc)
                articles_sauvegardes += 1

        except Exception as e:
            # Si une erreur arrive sur UN article, on continue avec les autres
            print(f"   Erreur sur {id_article} : {e}")

    print(f"    {articles_sauvegardes} nouveaux articles sauvegardés")

    # Pause 1 seconde entre chaque maladie (bonne pratique)
    time.sleep(1)


# --- LANCEMENT ---
print(" Démarrage du scraping PubMed...")
print("=" * 50)

for maladie in maladies:
    scraper_pubmed(maladie)

# Afficher le total dans MongoDB
total = collection.count_documents({})
print("\n" + "=" * 50)
print(f" Scraping terminé !")
print(f" Total articles dans MongoDB : {total}")