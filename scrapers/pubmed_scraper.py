
import requests
from pymongo import MongoClient
from datetime import datetime
import time
import xml.etree.ElementTree as ET

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_pubmed"]

maladies = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases"
]

def scraper_pubmed(maladie):
    print(f"\n🔍 Scraping PubMed : {maladie}")

    # Étape 1 : récupérer les IDs
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": maladie, "retmax": 200,
                "retmode": "json", "sort": "date"},
        timeout=15
    )
    ids = r.json()["esearchresult"]["idlist"]
    print(f"   → {len(ids)} articles trouvés")
    if not ids:
        return 0

    # Étape 2 : récupérer résumés + détails via efetch (XML)
    r2 = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(ids),
                "retmode": "xml", "rettype": "abstract"},
        timeout=30
    )

    try:
        root = ET.fromstring(r2.text)
    except:
        print("   ❌ Erreur parsing XML")
        return 0

    sauvegardes = 0
    for article in root.findall(".//PubmedArticle"):
        try:
            # Titre
            titre_el = article.find(".//ArticleTitle")
            titre = titre_el.text if titre_el is not None else ""
            if not titre:
                continue

            # Résumé
            resume_parts = article.findall(".//AbstractText")
            resume = " ".join([p.text for p in resume_parts if p.text])
            if not resume:
                resume = titre

            # Auteurs
            auteurs = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    nom = last.text
                    if first is not None:
                        nom += " " + first.text
                    auteurs.append(nom)

            # Date
            pub_date = article.find(".//PubDate")
            annee = pub_date.find("Year").text if pub_date is not None and pub_date.find("Year") is not None else ""
            mois = pub_date.find("Month").text if pub_date is not None and pub_date.find("Month") is not None else ""
            date_pub = f"{annee}-{mois}" if annee else "Inconnue"

            # Journal
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "Inconnu"

            # Mots-clés
            mots_cles = [kw.text for kw in article.findall(".//Keyword") if kw.text]
            if not mots_cles:
                mots_cles = [
                    mh.find("DescriptorName").text
                    for mh in article.findall(".//MeshHeading")
                    if mh.find("DescriptorName") is not None and mh.find("DescriptorName").text
                ]
            if maladie not in mots_cles:
                mots_cles.append(maladie)

            # PMID
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            lien = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            doc = {
                "titre": titre,
                "resume": resume,
                "auteurs": auteurs,
                "date_publication": date_pub,
                "journal": journal,
                "mots_cles": mots_cles,
                "maladie": maladie,
                "source": "PubMed",
                "lien": lien,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            if not collection.find_one({"lien": lien}):
                collection.insert_one(doc)
                sauvegardes += 1

        except Exception as e:
            continue

    time.sleep(1)
    print(f"   ✅ {sauvegardes} sauvegardés")
    return sauvegardes

if __name__ == "__main__":
    print("=== PubMed Scraper ===")
    total = 0
    for m in maladies:
        total += scraper_pubmed(m)
    print(f"\nTotal : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")
