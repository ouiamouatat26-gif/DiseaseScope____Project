import pandas as pd
import joblib
import os

print("[INFO] Chargement du dataset complet depuis data/clean_articles.csv...")
if not os.path.exists("data/clean_articles.csv"):
    raise FileNotFoundError("Le fichier data/clean_articles.csv est introuvable. Veuillez exécuter le nettoyage des données d'abord.")

df = pd.read_csv("data/clean_articles.csv", encoding="utf-8-sig")
df["texte"] = (df["titre"].fillna("") + " " + df["resume"].fillna("")).str.lower()
print(f"[INFO] Dataset complet chargé : {len(df)} articles.")

# Chargement du modèle et des outils d'encodage
print("[INFO] Chargement des modèles entraînés...")
if not (os.path.exists("models/linearsvc.joblib") and 
        os.path.exists("models/tfidf.joblib") and 
        os.path.exists("models/label_encoder.joblib")):
    raise FileNotFoundError("Modèles introuvables dans models/. Avez-vous exécuté 'python src/train_model.py' ?")

model      = joblib.load("models/linearsvc.joblib")
vectorizer = joblib.load("models/tfidf.joblib")
le         = joblib.load("models/label_encoder.joblib")

# --- Gérer l'absence du fichier corrigé ---
path_corrige = "data/articles_etiquetes_corriges.csv"
path_defaut  = "data/articles_etiquetes.csv"

if os.path.exists(path_corrige):
    file_human_path = path_corrige
    print(f"[INFO] Chargement de l'échantillon humain validé : {file_human_path}")
elif os.path.exists(path_defaut):
    file_human_path = path_defaut
    print(f"[WARNING] '{path_corrige}' introuvable. Bascule sur le fichier par défaut : {file_human_path}")
else:
    raise FileNotFoundError(
        f"Aucun fichier d'échantillon trouvé ('{path_corrige}' ou '{path_defaut}'). "
        "Veuillez exécuter votre script d'étiquetage initial d'abord."
    )

human_df = pd.read_csv(file_human_path, encoding="utf-8-sig")

# Dictionnaire pour mapper : titre -> label humain validé
human_labels = dict(zip(
    human_df["titre"].fillna("").str.strip(),
    human_df["type_contenu"]
))
print(f"[INFO] Chargé {len(human_labels)} articles de référence pour la consolidation.")

# Prédictions sur l'ensemble du dataset par le modèle ML
print("[INFO] Calcul des prédictions du modèle sur l'ensemble du dataset...")
X = vectorizer.transform(df["texte"])
model_preds = le.inverse_transform(model.predict(X))

# Consolidation Human-in-the-loop
df["pred_ml"] = model_preds

def consolider_label(row):
    titre_normalise = str(row["titre"]).strip()
    if titre_normalise in human_labels:
        return human_labels[titre_normalise], "HUMAN"
    else:
        return row["pred_ml"], "MODEL"

consolidated = df.apply(consolider_label, axis=1)
df["type_contenu"] = [item[0] for item in consolidated]
df["source_label"] = [item[1] for item in consolidated]

# Suppression des colonnes temporaires
df.drop(columns=["texte", "pred_ml"], inplace=True)

# Affichage des statistiques de consolidation
print("\n" + "=" * 60)
print("            BILAN DU PIPELINE CLASSIFICATION (HITL)")
print("=" * 60)
repartition_source = df["source_label"].value_counts()
print(f"Articles validés par l'humain (conservés) : {repartition_source.get('HUMAN', 0)}")
print(f"Articles prédits par le modèle ML         : {repartition_source.get('MODEL', 0)}")
print("-" * 60)
print("Répartition finale des catégories :")
print(df["type_contenu"].value_counts().to_string())
print("=" * 60 + "\n")

# --- CORRECTION : s'assurer que le dossier data/ existe ---
os.makedirs("data", exist_ok=True)

# Sauvegarde du dataset consolidé final
df.to_csv("data/articles_classifies.csv", index=False, encoding="utf-8-sig", errors="replace")
print("[OK] data/articles_classifies.csv créé avec succès avec toutes les données étiquetées !")