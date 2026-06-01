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
if not (os.path.exists("models/random_forest.joblib") and 
        os.path.exists("models/tfidf.joblib") and 
        os.path.exists("models/label_encoder.joblib")):
    raise FileNotFoundError("Modèles introuvables dans models/. Avez-vous exécuté 'python src/train_model.py' ?")

model      = joblib.load("models/random_forest.joblib")
vectorizer = joblib.load("models/tfidf.joblib")
le         = joblib.load("models/label_encoder.joblib")

# Chargement de l'échantillon validé par l'humain pour réintégration directe
print("[INFO] Chargement de l'échantillon humain depuis data/articles_etiquetes_corriges.csv...")
if not os.path.exists("data/articles_etiquetes_corriges.csv"):
    raise FileNotFoundError("Le fichier data/articles_etiquetes_corriges est introuvable. Étape de validation manquante.")

human_df = pd.read_csv("data/articles_etiquetes_corriges.csv", encoding="utf-8-sig")

# Dictionnaire pour mapper : titre -> label humain validé
# On applique .strip() pour éviter les écarts d'espaces blancs
human_labels = dict(zip(
    human_df["titre"].fillna("").str.strip(), 
    human_df["type_contenu"]
))
print(f"[INFO] Chargé {len(human_labels)} articles validés manuellement.")

# Prédictions sur l'ensemble du dataset par le modèle ML
print("[INFO] Calcul des prédictions du modèle sur l'ensemble du dataset...")
X = vectorizer.transform(df["texte"])
model_preds = le.inverse_transform(model.predict(X))

# Consolidation Human-in-the-loop
# Si un article a été validé par l'humain, on garde l'étiquette humaine, sinon on prend la prédiction ML
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

# Suppression des colonnes de texte technique / temporaire pour le fichier propre final
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
print("============================================================\n")

# Sauvegarde du dataset consolidé final
df.to_csv("data/articles_classifies.csv", index=False, encoding="utf-8-sig")
print("[OK] data/articles_classifies.csv créé avec succès avec toutes les données étiquetées !")