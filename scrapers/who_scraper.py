import requests
from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]
collection = db["articles_who"]

maladies = ["cancer", "diabetes", "alzheimer", "heart disease"]

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://iris.who.int/",
    "Origin": "https://iris.who.int"
})


def scraper_who(maladie):
    """
    Scrape WHO IRIS via l'API DSpace 7 (/server/api/).
    WHO IRIS tourne sur DSpace 7 dont le bon endpoint est /server/api/
    et non /rest/api/ (qui était DSpace 6).
    """

    print(f"\n Scraping WHO IRIS pour : {maladie}")

    # Visite de la page d'accueil pour obtenir les cookies CSRF 
    try:
        session.get("https://iris.who.int/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    # Appel à l'API DSpace 7 correcte 
    # Endpoint correct pour DSpace 7 : /server/api/discover/search/objects
    url = "https://iris.who.int/server/api/discover/search/objects"

    params = {
        "query":    maladie,
        "page":     0,
        "size":     80,
        "sort":     "score,DESC",
        "embed":    "item/metadata"
    }

    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        print(f"   Erreur HTTP {response.status_code} : {e}")
        print(f"   Réponse serveur : {response.text[:300]}")
        return
    except Exception as e:
        print(f"   Erreur connexion : {e}")
        return

    objects = (
        data
        .get("_embedded", {})
        .get("searchResult", {})
        .get("_embedded", {})
        .get("objects", [])
    )

    print(f"   → {len(objects)} publications trouvées")

    if not objects:
        # Affiche la structure reçue pour diagnostiquer
        print(f"   Structure reçue : {list(data.keys())}")
        return

    publications_sauvegardees = 0

    for obj in objects:
        try:
            item = obj.get("_embedded", {}).get("indexableObject", {})
            uuid = item.get("uuid", "")
            if not uuid:
                continue

            # Métadonnées : dict {clé: [{value, language}]}
            metadata_list = item.get("metadata", {})
            meta = {
                cle: [v.get("value", "") for v in valeurs]
                for cle, valeurs in metadata_list.items()
            }

            identifiants = meta.get("dc.identifier.uri", [])
            url_pub = next((i for i in identifiants if i.startswith("http")), "")

            doc = {
                "titre":            meta.get("dc.title",                  ["Sans titre"])[0],
                "auteurs":          meta.get("dc.contributor.author",     []),
                "date_publication": meta.get("dc.date.issued",            ["Inconnue"])[0],
                "editeur":          meta.get("dc.publisher",              ["WHO"])[0],
                "resume":           meta.get("dc.description.abstract",   [""])[0],
                "sujets":           meta.get("dc.subject",                []),
                "type_document":    meta.get("dc.type",                   [""])[0],
                "langue":           meta.get("dc.language.iso",           [""])[0],
                "doi":              meta.get("dc.identifier.doi",         [""])[0],
                "url":              url_pub,
                "who_uuid":         uuid,
                "maladie":          maladie,
                "source":           "WHO IRIS",
                "date_scraping":    datetime.now()
            }

            if not collection.find_one({"who_uuid": uuid}):
                collection.insert_one(doc)
                publications_sauvegardees += 1

        except Exception as e:
            print(f"   Erreur sur un article : {e}")

    print(f"    {publications_sauvegardees} nouvelles publications sauvegardées")
    time.sleep(2)


if __name__ == "__main__":
    print(" Démarrage du scraping WHO IRIS...")
    print("=" * 50)

    for maladie in maladies:
        scraper_who(maladie)

    total = collection.count_documents({})
    print("\n" + "=" * 50)
    print(f" Scraping terminé !")
    print(f" Total publications dans MongoDB : {total}")