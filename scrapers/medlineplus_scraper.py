import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_medlineplus"]

maladies = {
    "cancer": "https://medlineplus.gov/cancer.html",
    "diabetes": "https://medlineplus.gov/diabetes.html",
    "alzheimer": "https://medlineplus.gov/alzheimersdisease.html",
    "heart disease": "https://medlineplus.gov/heartdiseases.html",
    "neurological diseases": "https://medlineplus.gov/neurologicdiseases.html",
    "respiratory diseases": "https://medlineplus.gov/respiratorydiseases.html",
    "eye diseases": "https://medlineplus.gov/eyediseases.html",
    "digestive diseases": "https://medlineplus.gov/digestivediseases.html",
    "infectious diseases": "https://medlineplus.gov/infectiousdiseases.html",
    "autoimmune diseases": "https://medlineplus.gov/autoimmunediseases.html"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def scraper_medlineplus(maladie, url):
    print(f"\n Scraping MedlinePlus : {maladie}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"   Erreur : {e}")
        return 0

    soup = BeautifulSoup(response.content, "html.parser")
    sauvegardes = 0

    liens_articles = soup.find_all("a", href=True)

    for lien_tag in liens_articles:
        try:
            texte = lien_tag.text.strip()
            lien = lien_tag.get("href", "")

            if len(texte) < 15:
                continue

            if not lien.startswith("http"):
                lien = "https://medlineplus.gov" + lien

            doc = {
                "titre": texte,
                "resume": "",
                "auteurs": [],
                "date_publication": datetime.now().strftime("%Y-%m-%d"),
                "journal": "MedlinePlus",
                "mots_cles": [maladie],
                "maladie": maladie,
                "source": "MedlinePlus",
                "lien": lien,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            if not collection.find_one({"lien": lien}):
                collection.insert_one(doc)
                sauvegardes += 1
                print(f"   Sauvegarde : {texte[:50]}...")

        except Exception as e:
            continue

    print(f"   {sauvegardes} articles sauvegardes")
    time.sleep(1)
    return sauvegardes

if __name__ == "__main__":
    print("Scraping MedlinePlus avec BeautifulSoup...")
    print("=" * 50)

    total = 0
    for maladie, url in maladies.items():
        total += scraper_medlineplus(maladie, url)

    print("=" * 50)
    print(f"Total : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    print("\nPar maladie :")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")