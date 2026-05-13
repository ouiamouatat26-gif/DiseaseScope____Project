import pandas as pd
from pymongo import MongoClient
import os

# 1. Préparation du dossier data (Étape: Raw Data Storage)
if not os.path.exists('data'):
    os.makedirs('data')

try:
    # 2. Connexion à votre base DiseaseScope
    client = MongoClient("mongodb://localhost:27017/")
    db = client["diseasescope"]
    collection = db["articles_tous"] # La collection issue de fusionner.py

    # 3. Extraction vers DataFrame
    data = list(collection.find())
    if not data:
        print("Erreur : La collection 'articles_tous' est vide.")
    else:
        df = pd.DataFrame(data)
        
        # Nettoyage de l'ID MongoDB pour le CSV
        if '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)

        # 4. Export (Transition vers Data Versioning)
        df.to_csv("data/raw_articles_complet.csv", index=False, encoding='utf-8-sig')
        print(f"Succès ! {len(df)} articles exportés dans data/raw_articles_complet.csv")

except Exception as e:
    print(f"Erreur lors de l'export : {e}")