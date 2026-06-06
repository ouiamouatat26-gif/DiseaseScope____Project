"""
================================================================================
 STAGE 2 - CLASSIFICATION SUPERVISÉE SUR LES TOPICS DÉCOUVERTS
================================================================================

Le Stage 1 (src/topic_modeling.py) a découvert les catégories réelles du corpus
de façon NON-SUPERVISÉE (BERTopic). On a donc maintenant, pour chaque article,
un label "topic" fiable issu des données elles-mêmes.

Ce Stage 2 entraîne un modèle SUPERVISÉ (TF-IDF + LinearSVC) qui apprend la
correspondance  texte -> topic.  Objectif : pouvoir prédire INSTANTANÉMENT la
catégorie d'un NOUVEL article, sans refaire tourner tout le pipeline BERTopic
(embedding + UMAP + HDBSCAN) à chaque inférence.

    Stage 1 (lourd, hors-ligne)  : découvre les catégories     -> labels
    Stage 2 (léger, temps réel)  : apprend texte -> label      -> prédiction live

SORTIE :
    - models/topic_classifier.joblib   : le classifieur supervisé
    - models/topic_tfidf.joblib        : le vectoriseur TF-IDF associé
    - models/topic_label_encoder.joblib: l'encodeur de labels
    - models/topic_metrics.json        : accuracy + rapport de classification
================================================================================
"""

import os
import json
import warnings

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

DATA_IN = "data/articles_topics.csv"

MEDICAL_STOP_WORDS = [
    "study", "results", "conclusion", "background", "methods", "aim", "objective",
    "patients", "disease", "diseases", "associated", "significantly", "significance",
    "compared", "versus", "used", "using", "analysis", "reported", "abstract",
    "author", "authors", "article", "published", "journal", "evidence", "discussion",
]


def main():
    if not os.path.exists(DATA_IN):
        raise FileNotFoundError(
            f"'{DATA_IN}' introuvable. Lancez d'abord : python src/topic_modeling.py"
        )

    print(f"[INFO] Chargement des données étiquetées par BERTopic : {DATA_IN}")
    df = pd.read_csv(DATA_IN, encoding="utf-8-sig")

    df["texte"] = (df["titre"].fillna("") + " " + df["resume"].fillna("")).str.lower()
    df = df[df["texte"].str.strip() != ""]

    # On apprend sur le LABEL LISIBLE du topic (ex: "3_treatment_dose_clinical").
    # On écarte les éventuels outliers résiduels (-1) qui ne forment pas un topic.
    df = df[df["topic"] != -1]

    X = df["texte"]
    y = df["topic_label"]

    print(f"[INFO] {len(df)} articles, {y.nunique()} catégories découvertes.")

    # --- Vectorisation TF-IDF ------------------------------------------------
    stop_words = list(ENGLISH_STOP_WORDS.union(MEDICAL_STOP_WORDS))
    vectorizer = TfidfVectorizer(
        max_features=25000,
        ngram_range=(1, 2),
        stop_words=stop_words,
        sublinear_tf=True,
        min_df=2,
        max_df=0.85,
    )
    X_vec = vectorizer.fit_transform(X)
    print(f"[INFO] Matrice TF-IDF : {X_vec.shape}")

    # --- Encodage des labels -------------------------------------------------
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # --- Split train / test --------------------------------------------------
    stratify = y_enc if pd.Series(y_enc).value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y_enc, test_size=0.2, random_state=42, stratify=stratify
    )

    # --- Entraînement --------------------------------------------------------
    print("[INFO] Entraînement du classifieur supervisé (LinearSVC) ...")
    model = LinearSVC(C=0.5, class_weight="balanced", random_state=42, max_iter=3000)
    model.fit(X_train, y_train)

    # --- Évaluation ----------------------------------------------------------
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    present = sorted(set(y_test) | set(y_pred))
    target_names = [le.classes_[i] for i in present]

    print("\n" + "=" * 70)
    print(f"  ACCURACY (texte -> topic) : {round(acc * 100, 2)} %")
    print("=" * 70)
    print(classification_report(y_test, y_pred, labels=present,
                                target_names=target_names, zero_division=0))

    # --- Réentraînement final sur tout le dataset ----------------------------
    print("[INFO] Réentraînement final sur l'ensemble du dataset ...")
    final_model = LinearSVC(C=0.5, class_weight="balanced", random_state=42, max_iter=3000)
    final_model.fit(X_vec, y_enc)

    # --- Sauvegardes ---------------------------------------------------------
    os.makedirs("models", exist_ok=True)
    joblib.dump(final_model, "models/topic_classifier.joblib")
    joblib.dump(vectorizer, "models/topic_tfidf.joblib")
    joblib.dump(le, "models/topic_label_encoder.joblib")

    with open("models/topic_metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "accuracy": round(acc * 100, 2),
            "n_classes": int(y.nunique()),
            "classes": list(le.classes_),
            "n_articles": int(len(df)),
        }, f, indent=2, ensure_ascii=False)

    print("[OK] Modèles supervisés sauvegardés dans models/ "
          "(topic_classifier, topic_tfidf, topic_label_encoder)")


if __name__ == "__main__":
    main()
