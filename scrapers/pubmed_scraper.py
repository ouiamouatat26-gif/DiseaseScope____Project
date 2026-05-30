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

    response = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": disease,
            "retmax": 200,
            "retmode": "json",
            "sort": "date",
        },
        timeout=15,
    )
    ids = response.json()["esearchresult"]["idlist"]
    print(f"  {len(ids)} articles found")
    if not ids:
        return 0

    response2 = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
        },
        timeout=30,
    )

    try:
        root = ET.fromstring(response2.text)
    except ET.ParseError as e:
        print(f"  XML parsing error: {e}")
        return 0

    saved = 0
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
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            # Extract publication type
            pub_types = []
            for pt in article.findall(".//PublicationType"):
                if pt.text:
                    pub_types.append(pt.text.lower().replace(" ", "_"))
            type_contenu = pub_types[0] if pub_types else "non_classifie"

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
                "type_contenu": type_contenu,
                "date_scraping": datetime.now(),
            }

            if not collection.find_one({"lien": link}):
                collection.insert_one(doc)
                saved += 1

        except Exception:
            continue

    time.sleep(1)
    print(f"  {saved} saved")
    return saved


if __name__ == "__main__":
    print("=== PubMed Scraper ===")
    total = 0
    for d in DISEASES:
        total += scrape_pubmed(d)
    print(f"\nTotal saved: {total}")
    print(f"Total in MongoDB: {collection.count_documents({})}")
    for d in DISEASES:
        print(f"  {d}: {collection.count_documents({'maladie': d})}")
