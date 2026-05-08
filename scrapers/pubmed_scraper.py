
import requests
from pymongo import MongoClient
from datetime import datetime
import time


client = MongoClient("mongodb://localhost:27017/")

db = client["diseasescope"]

collection = db["articles"]

print(" Connecté à MongoDB !")

maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]

def scraper_pubmed(maladie):
    """
    Cette fonction scrape PubMed pour une maladie donnée
    et sauvegarde les articles dans MongoDB
    """
    
    print(f"\n Scraping pour : {maladie}")
    print("-" * 40)

    
    url_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    
    params_search = {
        "db": "pubmed",       
        "term": maladie,      
        "retmax": 80,         
        "retmode": "json",    
        "sort": "date"       
                              
    }

    
    response_search = requests.get(url_search, params=params_search)
    data_search = response_search.json()

    
    ids = data_search["esearchresult"]["idlist"]
    print(f"   → {len(ids)} articles trouvés sur PubMed")

   
    if not ids:
        print(f"   ⚠️ Aucun article pour : {maladie}")
        return 0

   
    url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    params_fetch = {
        "db": "pubmed",
        "id": ",".join(ids),  
        "retmode": "json"
    }

    
    response_fetch = requests.get(url_fetch, params=params_fetch)
    data_fetch = response_fetch.json()

    
    articles_sauvegardes = 0  
    for id_article in ids:
        try:
            
            article_info = data_fetch["result"][id_article]

           
            doc = {
                "titre": article_info.get("title", "Sans titre"),
                
                "auteurs": [
                    a["name"] 
                    for a in article_info.get("authors", [])
                ],
                
                "date_publication": article_info.get("pubdate", "Inconnue"),
                
                "journal": article_info.get("source", "Inconnu"),
                
                "maladie": maladie,
                
                "source": "PubMed",
                
                "pubmed_id": id_article,
                
               
                "lien": f"https://pubmed.ncbi.nlm.nih.gov/{id_article}/",

                
                "type_contenu": "non_classifie",
                
                "date_scraping": datetime.now()
            }

            
            existant = collection.find_one({"pubmed_id": id_article})
            
            if not existant:
               
                collection.insert_one(doc)
                articles_sauvegardes += 1
                print(f"    Sauvegardé : {doc['titre'][:50]}...")
            else:
               
                print(f"    Déjà existant : {id_article}")

        except Exception as e:
            
            print(f"    Erreur sur {id_article} : {e}")
            continue

    print(f"    {articles_sauvegardes} nouveaux articles sauvegardés")
    
   
    time.sleep(1)
    
    return articles_sauvegardes


print("\n Démarrage du scraping PubMed...")
print("=" * 50)

total_general = 0


for maladie in maladies:
    nombre = scraper_pubmed(maladie)
    total_general += nombre


print("\n" + "=" * 50)
print(f" Scraping terminé !")
print(f"Total articles sauvegardés : {total_general}")
print(f" Total dans MongoDB : {collection.count_documents({})}")
print("\nDétail par maladie :")
for maladie in maladies:
    count = collection.count_documents({"maladie": maladie})
    print(f"   {maladie} : {count} articles")
