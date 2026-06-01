import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC  # <-- Changement d'algorithme pour plus de performance
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import json
import os
import warnings

warnings.filterwarnings("ignore")

# --- CHARGEMENT DES DONNÉES ---
path_corrige = "data/articles_etiquetes_corriges.csv"
path_defaut = "data/articles_etiquetes.csv"

if os.path.exists(path_corrige):
    file_path = path_corrige
    print(f"[INFO] Chargement de l'échantillon validé : {file_path}")
elif os.path.exists(path_defaut):
    file_path = path_defaut
    print(f"[WARNING] Utilisation du fichier par défaut : {file_path}")
else:
    raise FileNotFoundError("Aucun fichier de données trouvé dans 'data/'.")

df = pd.read_csv(file_path, encoding="utf-8-sig")

# Préparation du texte
df["titre"] = df["titre"].fillna("")
df["resume"] = df["resume"].fillna("")
df["texte"] = (df["titre"] + " " + df["resume"]).str.lower()
df = df[df["texte"].str.strip() != ""]

X = df["texte"]
y = df["type_contenu"]

# --- OPTIMISATION DU TF-IDF & STOP-WORDS AVANCÉS ---
print("[INFO] Vectorisation TF-IDF optimisée...")

# Liste de stop-words spécifiques aux publications médicales pour nettoyer le bruit
medical_stop_words = [
    "study", "results", "conclusion", "background", "methods", "aim", "objective",
    "patients", "disease", "diseases", "associated", "significantly", "significance",
    "compared", "v", "versus", "used", "using", "analysis", "reported", "abstract",
    "author", "authors", "article", "published", "journal", "evidence", "discussions"
]
# Fusion avec la liste standard anglaise
from sklearn.feature_extraction import text
final_stop_words = list(text.ENGLISH_STOP_WORDS.union(medical_stop_words))

vectorizer = TfidfVectorizer(
    max_features=25000,       # <-- Augmenté de 10k à 25k pour capturer plus de détails
    ngram_range=(1, 3), 
    stop_words=final_stop_words,
    sublinear_tf=True,
    min_df=2,                 # <-- Ignore les mots qui n'apparaissent qu'une seule fois dans tout le dataset
    max_df=0.85               # <-- Ignore les mots qui apparaissent dans plus de 85% des documents
)
X_vec = vectorizer.fit_transform(X)
print(f"[INFO] Dimensions de la matrice de vocabulaire : {X_vec.shape}")

# --- ENCODAGE DES CLASSES ---
le = LabelEncoder()
y_enc = le.fit_transform(y)
classes = list(le.classes_)

# --- SÉPARATION TRAIN / TEST ---
class_counts = pd.Series(y_enc).value_counts()
min_class_count = class_counts.min()

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

# --- ENTRAÎNEMENT AVEC LINEARSVC (PLUS ROBUSTE) ---
print("[INFO] Entraînement du classifieur SVM Linéaire...")
# LinearSVC gère nativement le déséquilibre avec class_weight='balanced'
temp_model = LinearSVC(C=0.5, class_weight='balanced', random_state=42, max_iter=2000)
temp_model.fit(X_train, y_train)

# Évaluation
y_pred = temp_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n================ RAPPORT D'ÉVALUATION OPTIMISÉ ================")
print(f"Nouvelle précision globale (Accuracy) : {round(acc*100, 2)}%")
print("-" * 75)

present_labels = sorted(list(set(y_test) | set(y_pred)))
target_names_filtered = [classes[idx] for idx in present_labels]

print(classification_report(
    y_test, 
    y_pred, 
    labels=present_labels, 
    target_names=target_names_filtered, 
    zero_division=0
))
print("=========================================================================\n")

# --- ENTRAÎNEMENT DU MODÈLE FINAL ---
print("[INFO] Entraînement du modèle SVM final sur tout le dataset...")
final_model = LinearSVC(C=0.5, class_weight='balanced', random_state=42, max_iter=2000)
final_model.fit(X_vec, y_enc)

# Sauvegarde (on garde le nom d'origine pour éviter de casser vos autres scripts)
os.makedirs("models", exist_ok=True)
joblib.dump(final_model, "models/random_forest.joblib")
joblib.dump(vectorizer,  "models/tfidf.joblib")
joblib.dump(le,          "models/label_encoder.joblib")

# Sauvegarde des métriques
metrics = {
    "accuracy": round(acc * 100, 2),
    "classes": classes,
    "n_articles_train": len(df),
    "stratified": stratified
}
with open("models/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("[OK] Modèle mis à jour avec succès dans models/")