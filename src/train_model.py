import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import os
import warnings

warnings.filterwarnings("ignore")

# --- AJUSTEMENT SÉCURISÉ DU CHEMIN DU FICHIER ---
possible_paths = ["data/articles_etiquetes_corriges.csv", "articles_etiquetes_corriges.csv"]
file_path = None

for path in possible_paths:
    if os.path.exists(path):
        file_path = path
        break

if not file_path:
    raise FileNotFoundError(
        "Le fichier 'articles_etiquetes_corriges.csv' est introuvable (testé dans le dossier 'data/' et à la racine). "
        "Veuillez vérifier son emplacement."
    )

print(f"[INFO] Chargement de l'échantillon validé depuis {file_path}...")
df = pd.read_csv(file_path, encoding="utf-8-sig")

# Remplacement des valeurs vides et nettoyage
df = df[df["texte"].notna() & (df["texte"].str.strip() != "")]
print(f"[INFO] Nombre d'articles valides trouvés : {len(df)}")

if len(df) < 5:
    raise ValueError("L'échantillon d'entraînement est trop petit pour entraîner un modèle. Il doit y avoir au moins 5 articles.")

X = df["texte"]
y = df["type_contenu"]

# Vectorisation TF-IDF
print("[INFO] Vectorisation TF-IDF en cours...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
X_vec = vectorizer.fit_transform(X)
print(f"[INFO] Dimensions de la matrice TF-IDF : {X_vec.shape}")

# Encodage des classes
le = LabelEncoder()
y_enc = le.fit_transform(y)
classes = list(le.classes_)
print(f"[INFO] Catégories trouvées : {classes}")

# Vérification pour la stratification sécurisée
class_counts = pd.Series(y_enc).value_counts()
min_class_count = class_counts.min()

print("[INFO] Séparation des données pour évaluation (80% train / 20% test)...")
# Stratifier uniquement si toutes les classes possèdent au moins 2 exemples
if len(class_counts) > 1 and min_class_count >= 2:
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    stratified = True
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y_enc, test_size=0.2, random_state=42
    )
    stratified = False
    print("[WARNING] Certaines catégories possèdent trop peu d'exemples. Séparation sans stratification.")

# Entraînement initial sur la portion Train pour évaluation
print("[INFO] Entraînement temporaire du classifieur Random Forest pour évaluation...")
temp_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
temp_model.fit(X_train, y_train)

# Évaluation sur la portion Test
y_pred = temp_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n================ RAPPORT D'ÉVALUATION (Test Split) ================")
print(f"Précision globale (Accuracy) : {round(acc*100, 2)}% (Stratifié : {stratified})")
print("-" * 67)

# --- CORRECTION ROBUSTE DU CLASSIFICATION REPORT ---
# On passe les labels explicites (les entiers uniques vus en test/pred) 
# et on extrait les noms de classes correspondants de manière alignée.
present_labels = sorted(list(set(y_test) | set(y_pred)))
target_names_filtered = [classes[idx] for idx in present_labels]

try:
    print(classification_report(
        y_test, 
        y_pred, 
        labels=present_labels, 
        target_names=target_names_filtered, 
        zero_division=0
    ))
except Exception as e:
    print(f"Erreur d'affichage du rapport complet : {e}")
    print(classification_report(y_test, y_pred, zero_division=0))
print("===================================================================\n")

# Entraînement du modèle final sur la TOTALITÉ de l'échantillon
print("[INFO] Entraînement du modèle FINAL sur l'intégralité de l'échantillon...")
final_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
final_model.fit(X_vec, y_enc)

# Créer le dossier "models" s'il n'existe pas
os.makedirs("models", exist_ok=True)

# Sauvegarde du modèle final et des outils associés
joblib.dump(final_model, "models/random_forest.joblib")
joblib.dump(vectorizer,  "models/tfidf.joblib")
joblib.dump(le,          "models/label_encoder.joblib")

# Export des métriques
metrics = {
    "accuracy": round(acc * 100, 2),
    "classes": classes,
    "n_articles": len(df),
    "stratified": stratified
}
with open("models/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("[OK] Modèle final sauvegardé avec succès dans models/")
print("[ACTION SUIVANTE] Lancez maintenant votre script de prédiction pour étiqueter le reste de vos articles.")