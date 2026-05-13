import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["clinical_trials"]
maladies = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases"
]
def scraper_clinical_trials(maladie):
    print(f"\n Scraping ClinicalTrials : {maladie}")

    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": maladie,
        "pageSize": 200,
        "format": "json"
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        etudes = r.json().get("studies", [])
        print(f"   {len(etudes)} essais trouves")
    except Exception as e:
        print(f"   Erreur : {e}")
        return 0

    sauvegardes = 0
    for etude in etudes:
        try:
            proto = etude.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            statut_mod = proto.get("statusModule", {})
            desc_mod = proto.get("descriptionModule", {})
            cond_mod = proto.get("conditionsModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})

            nct_id = id_mod.get("nctId", "")
            lien = f"https://clinicaltrials.gov/study/{nct_id}"

            doc = {
                "titre": id_mod.get("briefTitle", "Sans titre"),
                "resume": desc_mod.get("briefSummary", ""),
                "auteurs": [],
                "date_publication": statut_mod.get("startDateStruct", {}).get("date", "Inconnue"),
                "journal": sponsor_mod.get("leadSponsor", {}).get("leadSponsorName", "Inconnu"),
                "mots_cles": cond_mod.get("conditions", []),
                "maladie": maladie,
                "source": "ClinicalTrials",
                "lien": lien,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now()
            }

            if not collection.find_one({"lien": lien}):
                collection.insert_one(doc)
                sauvegardes += 1
        except Exception as e:
            continue

    print(f"   {sauvegardes} sauvegardes")
    time.sleep(1)
    return sauvegardes

if __name__ == "__main__":
    print("=== ClinicalTrials Scraper ===")
    total = 0
    for m in maladies:
        total += scraper_clinical_trials(m)
    print(f"\nTotal : {total}")
    print(f"MongoDB : {collection.count_documents({})}")
    for m in maladies:
        print(f"   {m} : {collection.count_documents({'maladie': m})}")