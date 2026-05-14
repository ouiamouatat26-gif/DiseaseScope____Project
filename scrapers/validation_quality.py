from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["diseasescope"]

def valider_donnees():
    # 1. On récupère la collection fusionnée
    data = list(db["articles_tous"].find())
    if not data:
        print("La base est vide ! Lance d'abord fusionner.py")
        return
    
    df = pd.DataFrame(data)

    # 2. Check de la répartition (Ton Étape A)
    print("\n--- STATISTIQUES PAR MALADIE ---")
    print(df['maladie'].value_counts())

    # 3. Check du seuil de 15% (Ton Étape B - Exigence Prof)
    print("\n--- TAUX DE DONNÉES MANQUANTES ---")
    vide = df.isnull().mean() * 100
    print(vide)
    
    # Alerte visuelle si > 15%
    for col, per in vide.items():
        if per > 15:
            print(f"❌ ALERTE : La colonne '{col}' est trop vide ({per:.2f}%)")

if __name__ == "__main__":
    valider_donnees()