"""
================================================================================
 STAGE 1 - DÉCOUVERTE NON-SUPERVISÉE DES CATÉGORIES (BERTopic)
================================================================================

Ce script remplace l'étiquetage par mots-clés (src/etiqueter.py) par une vraie
approche de Machine Learning NON-SUPERVISÉE.

Au lieu d'imposer des catégories à la main, on laisse les données révéler leurs
propres regroupements ("topics") via le pipeline BERTopic en 7 étapes :

    1. Embed          -> transformer chaque article en vecteur (SentenceTransformer)
    2. Reduce         -> réduire la dimension des vecteurs (UMAP)
    3. Cluster        -> regrouper les articles proches (HDBSCAN, basé densité)
    4. Vectorize      -> compter les mots par cluster (CountVectorizer)
    5. c-TF-IDF       -> pondérer les mots représentatifs de chaque cluster
    6. Keywords       -> extraire automatiquement les mots-clés de chaque topic
    7. Map            -> assigner chaque document à son topic / ses mots-clés

Chaque étape est un composant interchangeable : on peut changer l'embedding,
l'algo de réduction ou de clustering sans toucher au reste.

SORTIE :
    - data/articles_topics.csv      : tout le corpus + colonne "topic" + "topic_label"
    - models/bertopic_model         : le modèle BERTopic sauvegardé (réutilisable)
    - visualizations/bertopic_*.html: cartes interactives des topics

Le Stage 2 (src/train_topic_classifier.py) entraînera ensuite un classifieur
SUPERVISÉ sur ces labels découverts, pour prédire la catégorie d'un NOUVEL article.
================================================================================
"""

import os
import argparse
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

# --- Dépendances ML lourdes (importées ici pour un message d'erreur clair) -----
try:
    from sentence_transformers import SentenceTransformer
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from bertopic.representation import KeyBERTInspired
except ImportError as e:
    raise SystemExit(
        f"\n[ERREUR] Dépendance manquante : {e.name}\n"
        "Installez les dépendances du Stage 1 :\n"
        "    pip install bertopic sentence-transformers umap-learn hdbscan\n"
    )


# =============================================================================
# CONFIGURATION
# =============================================================================
DATA_IN = "data/clean_articles.csv"
DATA_OUT = "data/articles_topics.csv"
MODEL_DIR = "models/bertopic_model"
VIZ_DIR = "visualizations"

# Stop-words spécifiques aux publications médicales (bruit qui pollue les topics)
MEDICAL_STOP_WORDS = [
    "study", "studies", "results", "result", "conclusion", "conclusions",
    "background", "methods", "method", "aim", "aims", "objective", "objectives",
    "patient", "patients", "disease", "diseases", "associated", "significantly",
    "significance", "compared", "versus", "used", "using", "analysis", "reported",
    "abstract", "author", "authors", "article", "published", "journal", "evidence",
    "discussion", "discussions", "group", "groups", "data", "based", "showed",
    "shown", "found", "may", "also", "however", "thus", "respectively", "performed",
]


def build_stop_words():
    return list(ENGLISH_STOP_WORDS.union(MEDICAL_STOP_WORDS))


# =============================================================================
# PIPELINE
# =============================================================================
def run(sample_size=None, min_topic_size=50, embedding_model="all-MiniLM-L6-v2",
        nr_topics="auto", random_state=42):

    # ---- Chargement des données ---------------------------------------------
    if not os.path.exists(DATA_IN):
        raise FileNotFoundError(
            f"'{DATA_IN}' introuvable. Lancez d'abord src/clean_data.py."
        )

    print(f"[INFO] Chargement de {DATA_IN} ...")
    df = pd.read_csv(DATA_IN, encoding="utf-8-sig")

    # Texte = titre + résumé (ce sur quoi on raisonne sémantiquement)
    df["texte"] = (df["titre"].fillna("") + ". " + df["resume"].fillna("")).str.strip()
    df = df[df["texte"].str.len() > 20].reset_index(drop=True)  # on jette les vides
    print(f"[INFO] {len(df)} articles exploitables.")

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=random_state).reset_index(drop=True)
        print(f"[INFO] Échantillonnage à {sample_size} articles (mode rapide).")

    docs = df["texte"].tolist()

    # ---- Étape 1 : EMBED -----------------------------------------------------
    print(f"[1/7] Embedding des documents avec '{embedding_model}' ...")
    embedder = SentenceTransformer(embedding_model)
    embeddings = embedder.encode(docs, show_progress_bar=True, batch_size=64)

    # ---- Étape 2 : REDUCE (UMAP) --------------------------------------------
    print("[2/7] Réduction de dimension (UMAP) ...")
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=random_state,
    )

    # ---- Étape 3 : CLUSTER (HDBSCAN, basé densité) --------------------------
    print("[3/7] Clustering (HDBSCAN) ...")
    # cluster_selection_method="leaf" -> clusters plus fins et plus nombreux
    # (le mode "eom" par defaut a tendance a ne sortir que 2-3 gros blobs sur
    #  des corpus homogenes comme des resumes medicaux).
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_topic_size,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="leaf",
        prediction_data=True,
    )

    # ---- Étapes 4-5 : VECTORIZE + c-TF-IDF ----------------------------------
    print("[4-5/7] Vectorisation + c-TF-IDF ...")
    # NB: dans BERTopic, ce vectoriseur est appliqué au c-TF-IDF sur UN document
    # concaténé PAR TOPIC (et non sur les N articles). min_df compte donc en
    # nombre de topics -> on le garde petit pour ne pas vider le vocabulaire.
    vectorizer_model = CountVectorizer(
        stop_words=build_stop_words(),
        ngram_range=(1, 2),
        min_df=1,
    )
    ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

    # ---- Étape 6 : KEYWORDS (représentation affinée) ------------------------
    representation_model = KeyBERTInspired()

    # ---- Assemblage du pipeline BERTopic ------------------------------------
    topic_model = BERTopic(
        embedding_model=embedder,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        ctfidf_model=ctfidf_model,
        representation_model=representation_model,
        nr_topics=nr_topics,          # "auto" : fusionne les topics trop similaires
        calculate_probabilities=False,
        verbose=True,
    )

    # ---- Étape 7 : MAP (fit + transform) ------------------------------------
    print("[6-7/7] Apprentissage des topics et assignation des documents ...")
    topics, _ = topic_model.fit_transform(docs, embeddings=embeddings)

    # Réassigne les outliers (-1) au topic le plus probable — uniquement s'il y
    # en a (HDBSCAN n'en produit pas toujours).
    if -1 in set(topics):
        print("[INFO] Réduction des outliers ...")
        topics = topic_model.reduce_outliers(docs, topics, strategy="c-tf-idf")
        topic_model.update_topics(docs, topics=topics,
                                  vectorizer_model=vectorizer_model)

    # ---- Construction des labels lisibles -----------------------------------
    # BERTopic génère un label du type "3_treatment_clinical_trial_dose"
    topic_info = topic_model.get_topic_info()
    label_map = dict(zip(topic_info["Topic"], topic_info["Name"]))

    df["topic"] = topics
    df["topic_label"] = df["topic"].map(label_map)

    # ---- Sauvegardes --------------------------------------------------------
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs(VIZ_DIR, exist_ok=True)

    df.drop(columns=["texte"]).to_csv(DATA_OUT, index=False, encoding="utf-8-sig")
    topic_model.save(MODEL_DIR, serialization="safetensors",
                     save_ctfidf=True, save_embedding_model=embedding_model)

    try:
        topic_model.visualize_topics().write_html(f"{VIZ_DIR}/bertopic_topics.html")
        topic_model.visualize_barchart(top_n_topics=12).write_html(
            f"{VIZ_DIR}/bertopic_keywords.html")
    except Exception as e:
        print(f"[WARN] Visualisations non générées : {e}")

    # ---- Bilan --------------------------------------------------------------
    n_topics = len([t for t in set(topics) if t != -1])
    print("\n" + "=" * 70)
    print("           STAGE 1 TERMINÉ - TOPICS DÉCOUVERTS")
    print("=" * 70)
    print(f"Nombre de catégories découvertes automatiquement : {n_topics}")
    print("-" * 70)
    print(topic_info[["Topic", "Count", "Name"]].head(20).to_string(index=False))
    print("=" * 70)
    print(f"[OK] Corpus étiqueté          -> {DATA_OUT}")
    print(f"[OK] Modèle BERTopic          -> {MODEL_DIR}")
    print(f"[OK] Visualisations           -> {VIZ_DIR}/bertopic_*.html")
    print("\n[ACTION] Lancez maintenant : python src/train_topic_classifier.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1 - BERTopic topic discovery")
    parser.add_argument("--sample", type=int, default=None,
                        help="Limiter à N articles (test rapide). Par défaut : tout le corpus.")
    parser.add_argument("--min-topic-size", type=int, default=50,
                        help="Taille minimale d'un cluster/topic (def: 50).")
    parser.add_argument("--embedding-model", type=str, default="all-MiniLM-L6-v2",
                        help="Modèle SentenceTransformer (def: all-MiniLM-L6-v2).")
    parser.add_argument("--nr-topics", default="auto",
                        help="'auto', un entier, ou 'None' (def: auto).")
    args = parser.parse_args()

    nr = args.nr_topics
    if isinstance(nr, str) and nr.isdigit():
        nr = int(nr)
    elif nr == "None":
        nr = None

    run(sample_size=args.sample,
        min_topic_size=args.min_topic_size,
        embedding_model=args.embedding_model,
        nr_topics=nr)
