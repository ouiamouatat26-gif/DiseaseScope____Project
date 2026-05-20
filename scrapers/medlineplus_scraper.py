import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_medlineplus"]

maladies = {
    "cancer": "cancer",
    "diabetes": "diabetes",
    "alzheimer": "alzheimer",
    "heart disease": "heartdisease",
    "neurological diseases": "neurologicdiseases",
    "respiratory diseases": "respiratorydiseases",
    "eye diseases": "eyediseases",
    "digestive diseases": "digestivediseases",
    "infectious diseases": "infectiousdiseases",
    "autoimmune diseases": "autoimmunediseases"
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def scraper_medlineplus(maladie, terme):
    print(f"\n🔍 Scraping MedlinePlus : {maladie}")

    url = f"https://medlineplus.gov/{terme}.html"
    sauvegardes = 0

    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return 0

    # Récupérer tous les liens d'articles dans la page
    tous_liens = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        texte = a.text.strip()
        if len(texte) > 20 and ("medlineplus.gov" in href or href.startswith("/")):
            if not href.startswith("http"):
                href = "https://medlineplus.gov" + href
            tous_liens.append((texte, href))

    print(f"   → {len(tous_liens)} liens trouvés")

    for texte, lien in tous_liens[:50]:
        try:
            if collection.find_one({"lien": lien}):
                continue

            # Aller chercher le contenu de chaque page
            r2 = requests.get(lien, headers=headers, timeout=10)
            soup2 = BeautifulSoup(r2.content, "html.parser")

            # Chercher le résumé
            resume = ""
            for div_id in ["topic-summary", "toc", "ency-content"]:
                div = soup2.find("div", {"id": div_id})
                if div:
                    paragraphes = div.find_all("p")
                    resume = " ".join([p.text.strip() for p in paragraphes if len(p.text.strip()) > 30])
                    break

            if not resume:
                body = soup2.find("main") or soup2.find("article")
                if body:
                    paragraphes = body.find_all("p")
                    resume = " ".join([p.text.strip() for p in paragraphes[:5] if len(p.text.strip()) > 30])

            if not resume:
                continue

            doc = {
                "titre": texte,
                "resume": resume[:2000],
                "auteurs": ["MedlinePlus Editorial Team"],
                "date_publication": datetime.now().strftime("%Y-%m-%d"),
                "journal": "MedlinePlus",
                "mots_cles": [maladie],
                "maladie": maladie,
                "source": "MedlinePlus",
                "lien": lien,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            collection.insert_one(doc)
            sauvegardes += 1
            print(f"   ✅ {texte[:55]}...")
            time.sleep(0.5)

        except Exception as e:
            continue

    print(f"   📦 {sauvegardes} articles sauvegardés")
    time.sleep(2)
    return sauvegardes

if __name__ == "__main__":
    print("=== MedlinePlus Scraper ===")
    total = 0
    for maladie, terme in maladies.items():
        total += scraper_medlineplus(maladie, terme)
    print(f"\n✅ Total : {total}")
    print(f"📊 MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")
