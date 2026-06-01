import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["clinical_trials"]

DISEASES = [
    "cancer", "diabetes", "alzheimer", "heart disease",
    "neurological diseases", "respiratory diseases",
    "eye diseases", "digestive diseases",
    "infectious diseases", "autoimmune diseases",
]


def scrape_clinical_trials(disease):
    print(f"Scraping ClinicalTrials: {disease}")

    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": disease,
        "pageSize": 1000,
        "format": "json",
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        studies = r.json().get("studies", [])
        print(f"  {len(studies)} trials found")
    except Exception as e:
        print(f"  Error: {e}")
        return 0

    saved = 0
    for study in studies:
        try:
            proto = study.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            desc_mod = proto.get("descriptionModule", {})
            cond_mod = proto.get("conditionsModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
            contacts_mod = proto.get("contactsLocationsModule", {})

            nct_id = id_mod.get("nctId", "")
            link = f"https://clinicaltrials.gov/study/{nct_id}"
            sponsor = sponsor_mod.get("leadSponsor", {}).get("name", "ClinicalTrials")

            contacts = []
            for contact in contacts_mod.get("centralContacts", []):
                name = contact.get("name", "").strip()
                if name:
                    contacts.append(name)
            if not contacts and sponsor:
                contacts = [sponsor]

            doc = {
                "titre": id_mod.get("briefTitle", "Untitled"),
                "resume": desc_mod.get("briefSummary") or id_mod.get("briefTitle", ""),
                "auteurs": contacts,
                "date_publication": status_mod.get("startDateStruct", {}).get("date", "Unknown"),
                "journal": sponsor,
                "mots_cles": cond_mod.get("conditions", []),
                "maladie": disease,
                "source": "ClinicalTrials",
                "lien": link,
                "type_contenu": "non_classifie",
                "date_scraping": datetime.now(),
            }

            if not collection.find_one({"lien": link}):
                collection.insert_one(doc)
                saved += 1

        except Exception:
            continue

    print(f"  {saved} saved")
    time.sleep(1)
    return saved


if __name__ == "__main__":
    print("=== ClinicalTrials Scraper ===")
    total = 0
    for d in DISEASES:
        total += scrape_clinical_trials(d)
    print(f"\nTotal saved: {total}")
    print(f"Total in MongoDB: {collection.count_documents({})}")
    for d in DISEASES:
        print(f"  {d}: {collection.count_documents({'maladie': d})}")
