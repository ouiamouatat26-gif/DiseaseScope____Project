import requests
from pymongo import MongoClient
from datetime import datetime
import time


client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["clinical_trials"]

maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]


def scraper_clinical_trials(maladie):
    """Scrape ClinicalTrials.gov (API v2) pour une maladie et sauvegarde dans MongoDB."""

    print(f"\n Scraping ClinicalTrials pour : {maladie}")

    # Documentation : https://clinicaltrials.gov/data-api/api
    url = "https://clinicaltrials.gov/api/v2/studies"

    params = {
        "query.cond": maladie,      # Condition / maladie recherchée
        "pageSize": 80,             # Nombre de résultats max
        "format": "json",
        "fields": (                 # Champs souhaités (séparés par |)
            "NCTId|BriefTitle|OfficialTitle|OverallStatus|Phase|"
            "StartDate|CompletionDate|LeadSponsorName|BriefSummary|"
            "Condition|InterventionName|InterventionType|"
            "EnrollmentCount|StudyType|LocationCountry"
        )
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    etudes = data.get("studies", [])
    print(f"   → {len(etudes)} essais trouvés")

    etudes_sauvegardees = 0

    for etude in etudes:
        try:
            # L'API v2 imbrique les données dans protocolSection
            proto = etude.get("protocolSection", {})
            id_module       = proto.get("identificationModule", {})
            statut_module   = proto.get("statusModule", {})
            desc_module     = proto.get("descriptionModule", {})
            design_module   = proto.get("designModule", {})
            sponsor_module  = proto.get("sponsorCollaboratorsModule", {})
            cond_module     = proto.get("conditionsModule", {})
            interv_module   = proto.get("armsInterventionsModule", {})
            contacts_module = proto.get("contactsLocationsModule", {})

            nct_id = id_module.get("nctId", "")

            # Interventions : liste des noms
            interventions = [
                i.get("interventionName", "")
                for i in interv_module.get("interventions", [])
            ]

            # Pays des sites cliniques (dédupliqués)
            pays = list({
                loc.get("locationCountry", "")
                for loc in contacts_module.get("locations", [])
                if loc.get("locationCountry")
            })

            doc = {
                "nct_id": nct_id,
                "titre_bref": id_module.get("briefTitle", "Sans titre"),
                "titre_officiel": id_module.get("officialTitle", ""),
                "statut": statut_module.get("overallStatus", "Inconnu"),
                "phase": design_module.get("phases", []),
                "type_etude": design_module.get("studyType", ""),
                "date_debut": statut_module.get("startDateStruct", {}).get("date", "Inconnue"),
                "date_fin": statut_module.get("completionDateStruct", {}).get("date", "Inconnue"),
                "sponsor": sponsor_module.get("leadSponsor", {}).get("leadSponsorName", "Inconnu"),
                "resume": desc_module.get("briefSummary", ""),
                "conditions": cond_module.get("conditions", []),
                "interventions": interventions,
                "effectif": design_module.get("enrollmentInfo", {}).get("count", None),
                "pays": pays,
                "maladie": maladie,
                "source": "ClinicalTrials.gov",
                "date_scraping": datetime.now()
            }

            # Évite les doublons via le NCT ID
            existant = collection.find_one({"nct_id": nct_id})
            if not existant:
                collection.insert_one(doc)
                etudes_sauvegardees += 1

        except Exception as e:
            print(f"   Erreur sur un essai : {e}")

    print(f"    {etudes_sauvegardees} nouveaux essais sauvegardés")

    time.sleep(1)


if __name__ == "__main__":
    print(" Démarrage du scraping ClinicalTrials.gov...")
    print("=" * 50)

    for maladie in maladies:
        scraper_clinical_trials(maladie)

    total = collection.count_documents({})
    print("\n" + "=" * 50)
    print(f" Scraping terminé !")
    print(f" Total essais dans MongoDB : {total}")