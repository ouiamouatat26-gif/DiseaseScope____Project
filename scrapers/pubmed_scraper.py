import requests
from pymongo import MongoClient
from datetime import datetime
import time
import xml.etree.ElementTree as ET

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_pubmed"]

DISEASES = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
]


def scrape_pubmed(disease):
    print(f"Scraping PubMed: {disease}")

    # Étape 1 : Recherche des IDs d'articles avec la nouvelle limite de 1500
    try:
        response = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": disease,
                "retmax": 1500,  # <-- Augmenté pour fournir assez de matière au ML
                "retmode": "json",
                "sort": "date",
            },
            timeout=15,
        )
        response.raise_for_status()
        ids = response.json().get("esearchresult", {}).get("idlist", [])
        print(f"  {len(ids)} articles trouvés pour '{disease}'")
    except Exception as e:
        print(f"  Erreur lors de la recherche (eSearch): {e}")
        return 0

    if not ids:
        return 0

    # Étape 2 : Récupération des détails textuels (Fetch) par paquets
    # On découpe en paquets de 300 IDs pour éviter les requêtes trop lourdes ou rejetées par l'API
    saved = 0
    chunk_size = 300
    
    for i in range(0, len(ids), chunk_size):
        chunk_ids = ids[i:i + chunk_size]
        
        try:
            response2 = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(chunk_ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                },
                timeout=30,
            )
            response2.raise_for_status()
            root = ET.fromstring(response2.text)
        except Exception as e:
            print(f"  Erreur lors de la récupération du paquet (eFetch): {e}")
            continue

        # Étape 3 : Parsing XML et insertion dans MongoDB
        for article in root.findall(".//PubmedArticle"):
            try:
                title_el = article.find(".//ArticleTitle")
                title = title_el.text if title_el is not None else ""
                if not title:
                    continue

                abstract_parts = article.findall(".//AbstractText")
                abstract = " ".join([p.text for p in abstract_parts if p.text])
                if not abstract:
                    abstract = title

                authors = []
                for author in article.findall(".//Author"):
                    last = author.find("LastName")
                    first = author.find("ForeName")
                    if last is not None:
                        name = last.text
                        if first is not None:
                            name += " " + first.text
                        authors.append(name)

                pub_date = article.find(".//PubDate")
                year = pub_date.find("Year").text if pub_date is not None and pub_date.find("Year") is not None else ""
                month = pub_date.find("Month").text if pub_date is not None and pub_date.find("Month") is not None else ""
                publication_date = f"{year}-{month}" if year else "Unknown"

                journal_el = article.find(".//Journal/Title")
                journal = journal_el.text if journal_el is not None else "Unknown"

                keywords = [kw.text for kw in article.findall(".//Keyword") if kw.text]
                if not keywords:
                    keywords = [
                        mh.find("DescriptorName").text
                        for mh in article.findall(".//MeshHeading")
                        if mh.find("DescriptorName") is not None and mh.find("DescriptorName").text
                    ]
                if disease not in keywords:
                    keywords.append(disease)

                pmid_el = article.find(".//PMID")
                pmid = pmid_el.text if pmid_el is not None else ""
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

                doc = {
                    "titre": title,
                    "resume": abstract,
                    "auteurs": authors,
                    "date_publication": publication_date,
                    "journal": journal,
                    "mots_cles": keywords,
                    "maladie": disease,
                    "source": "PubMed",
                    "lien": link,
                    "type_contenu": "non_classifie",
                    "date_scraping": datetime.now(),
                }

                # Vérification anti-doublon en local durant l'insertion
                if link and not collection.find_one({"lien": link}):
                    collection.insert_one(doc)
                    saved += 1

            except Exception:
                continue
                
        # Pause de courtoisie pour respecter les serveurs du NCBI
        time.sleep(1)

    print(f"  -> {saved} nouveaux articles enregistrés en base pour '{disease}'")
    return saved


if __name__ == "__main__":
    print("=== PubMed Scraper (Version Volumétrie Élargie) ===")
    
    # NETTOYAGE : Supprime l'ancienne collection limitée à 200 articles pour faire place nette
    print("[INFO] Réinitialisation de la collection 'articles_pubmed'...")
    collection.drop()
    
    total = 0
    start_time = time.time()
    
    for d in DISEASES:
        total += scrape_pubmed(d)
        time.sleep(1.5)  # Temporisation entre les requêtes de recherche globale
        
    end_time = time.time()
    print(f"\n==================================================")
    print(f"Fin du scraping PubMed en {round((end_time - start_time)/60, 2)} minutes.")
    print(f"Total d'articles insérés : {total}")
    print(f"Total présent en base (Vérification) : {collection.count_documents({})}")
    print(f"==================================================")
    
    print("\nRépartition finale dans MongoDB :")
    for d in DISEASES:
        print(f"  - {d:22} : {collection.count_documents({'maladie': d})} articles")