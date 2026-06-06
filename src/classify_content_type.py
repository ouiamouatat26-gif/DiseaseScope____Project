"""
================================================================================
 CLASSIFICATION AUTOMATIQUE DU TYPE DE CONTENU
================================================================================

Ce script analyse le titre et le résumé de chaque article pour déduire
automatiquement le type de publication scientifique (type_contenu).

Les scrapers originaux mettent tous "non_classifie" — ce script corrige ça
en appliquant des règles à base de mots-clés et de la source.

ENTRÉE  : data/articles_topics.csv  (avec type_contenu = "non_classifie")
SORTIE  : data/articles_topics.csv  (type_contenu reclassifié)
================================================================================
"""

import os
import sys
import re
import pandas as pd

DATA_PATH = "data/articles_topics.csv"

# =============================================================================
# RÈGLES DE CLASSIFICATION (par ordre de priorité)
# =============================================================================
# Chaque règle est un tuple (type_contenu, patterns)
# patterns = liste de regex compilées à chercher dans titre+résumé
# La première règle qui matche est retenue.

CLASSIFICATION_RULES = [
    # --- Méta-analyse (priorité haute car très spécifique) ---
    ("Méta-analyse", [
        re.compile(r"\bmeta[\s-]?analy", re.IGNORECASE),
        re.compile(r"\bpooled\s+analy", re.IGNORECASE),
        re.compile(r"\bnetwork\s+meta", re.IGNORECASE),
    ]),

    # --- Revue systématique ---
    ("Revue systématique", [
        re.compile(r"\bsystematic\s+review", re.IGNORECASE),
        re.compile(r"\bscoping\s+review", re.IGNORECASE),
        re.compile(r"\bliterature\s+review", re.IGNORECASE),
        re.compile(r"\bumbrella\s+review", re.IGNORECASE),
        re.compile(r"\bnarrative\s+review", re.IGNORECASE),
        re.compile(r"\bintegrative\s+review", re.IGNORECASE),
    ]),

    # --- Recommandation clinique / Guideline ---
    ("Recommandation clinique", [
        re.compile(r"\bguideline", re.IGNORECASE),
        re.compile(r"\bclinical\s+practice\s+guideline", re.IGNORECASE),
        re.compile(r"\bconsensus\s+statement", re.IGNORECASE),
        re.compile(r"\bposition\s+statement", re.IGNORECASE),
        re.compile(r"\brecommendation(?:s)?\b", re.IGNORECASE),
        re.compile(r"\bexpert\s+consensus", re.IGNORECASE),
    ]),

    # --- Essai clinique ---
    ("Essai clinique", [
        re.compile(r"\bclinical\s+trial", re.IGNORECASE),
        re.compile(r"\brandomized\s+controlled", re.IGNORECASE),
        re.compile(r"\brandomised\s+controlled", re.IGNORECASE),
        re.compile(r"\bdouble[\s-]blind", re.IGNORECASE),
        re.compile(r"\bplacebo[\s-]controlled", re.IGNORECASE),
        re.compile(r"\bphase\s+[IiVv1-4]+\b", re.IGNORECASE),
        re.compile(r"\b(?:RCT|rct)\b"),
        re.compile(r"\brandomized\b", re.IGNORECASE),
        re.compile(r"\brandomised\b", re.IGNORECASE),
        re.compile(r"\bopen[\s-]label", re.IGNORECASE),
        re.compile(r"\bcrossover\s+(?:study|trial|design)", re.IGNORECASE),
        re.compile(r"\bsingle[\s-](?:arm|center|centre)", re.IGNORECASE),
        re.compile(r"\bmulticenter\s+(?:study|trial)", re.IGNORECASE),
        re.compile(r"\bmulticentre\s+(?:study|trial)", re.IGNORECASE),
    ]),

    # --- Étude de cas ---
    ("Étude de cas", [
        re.compile(r"\bcase\s+report", re.IGNORECASE),
        re.compile(r"\bcase\s+series", re.IGNORECASE),
        re.compile(r"\bcase\s+study\b", re.IGNORECASE),
        re.compile(r"\brare\s+case", re.IGNORECASE),
    ]),

    # --- Étude génomique ---
    ("Étude génomique", [
        re.compile(r"\bgenome[\s-]wide", re.IGNORECASE),
        re.compile(r"\bGWAS\b"),
        re.compile(r"\bwhole[\s-]genome\s+sequencing", re.IGNORECASE),
        re.compile(r"\bwhole[\s-]exome", re.IGNORECASE),
        re.compile(r"\btranscriptom", re.IGNORECASE),
        re.compile(r"\bproteomi", re.IGNORECASE),
        re.compile(r"\bmetabolomi", re.IGNORECASE),
        re.compile(r"\bepigenome", re.IGNORECASE),
        re.compile(r"\bnext[\s-]generation\s+sequencing", re.IGNORECASE),
        re.compile(r"\bRNA[\s-]seq\b", re.IGNORECASE),
    ]),

    # --- Recherche fondamentale ---
    ("Recherche fondamentale", [
        re.compile(r"\bin\s+vitro\b", re.IGNORECASE),
        re.compile(r"\bin\s+vivo\b", re.IGNORECASE),
        re.compile(r"\banimal\s+model", re.IGNORECASE),
        re.compile(r"\bmouse\s+model", re.IGNORECASE),
        re.compile(r"\bmurine\b", re.IGNORECASE),
        re.compile(r"\bxenograft", re.IGNORECASE),
        re.compile(r"\bcell\s+line", re.IGNORECASE),
        re.compile(r"\bcell\s+culture", re.IGNORECASE),
        re.compile(r"\bknockout\b", re.IGNORECASE),
        re.compile(r"\btransgenic\b", re.IGNORECASE),
        re.compile(r"\brat\s+model", re.IGNORECASE),
        re.compile(r"\bzebrafish\b", re.IGNORECASE),
        re.compile(r"\bdrosophila\b", re.IGNORECASE),
        re.compile(r"\bex\s+vivo\b", re.IGNORECASE),
    ]),

    # --- Étude observationnelle ---
    ("Étude observationnelle", [
        re.compile(r"\bcohort\s+study", re.IGNORECASE),
        re.compile(r"\bcross[\s-]sectional", re.IGNORECASE),
        re.compile(r"\bobservational\s+study", re.IGNORECASE),
        re.compile(r"\bretrospective\s+(?:study|analysis|cohort|review)", re.IGNORECASE),
        re.compile(r"\bprospective\s+(?:study|analysis|cohort)", re.IGNORECASE),
        re.compile(r"\bcase[\s-]control", re.IGNORECASE),
        re.compile(r"\blongitudinal\s+study", re.IGNORECASE),
        re.compile(r"\bpopulation[\s-]based\s+study", re.IGNORECASE),
        re.compile(r"\bregistry[\s-]based", re.IGNORECASE),
        re.compile(r"\bnationwide\s+(?:study|cohort|analysis)", re.IGNORECASE),
        re.compile(r"\bsurvey\b", re.IGNORECASE),
    ]),
]

# Sources spécifiques → type par défaut si aucune règle ne matche
SOURCE_DEFAULTS = {
    "ClinicalTrials": "Essai clinique",
    "MedlinePlus": "Information santé",
    "WHO": "Information santé",
}


def classify_one(titre, resume, source):
    """Classifie un article en analysant son texte et sa source."""
    text = f"{titre} {resume}".lower()

    # Appliquer les règles de mots-clés (dans l'ordre de priorité)
    for type_contenu, patterns in CLASSIFICATION_RULES:
        for pattern in patterns:
            if pattern.search(text):
                return type_contenu

    # Fallback basé sur la source
    if source in SOURCE_DEFAULTS:
        return SOURCE_DEFAULTS[source]

    return "Autre"


def run():
    if not os.path.exists(DATA_PATH):
        print(f"[ERREUR] Fichier '{DATA_PATH}' introuvable.")
        sys.exit(1)

    print(f"[INFO] Chargement de {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    # --- Classification ---
    print("[INFO] Classification du type de contenu en cours ...")
    df["type_contenu"] = df.apply(
        lambda row: classify_one(
            str(row.get("titre", "")),
            str(row.get("resume", "")),
            str(row.get("source", ""))
        ),
        axis=1,
    )

    # --- Bilan ---
    type_counts = df["type_contenu"].value_counts()
    total = len(df)
    print(f"\n{'='*60}")
    print("  TYPES DE CONTENU CLASSIFIÉS")
    print(f"{'='*60}")
    print(f"Total articles : {total}")
    print(f"{'-'*60}")
    for t, count in type_counts.items():
        pct = count / total * 100
        print(f"  {t:<30} {count:>6} ({pct:>5.1f}%)")
    print(f"{'='*60}")

    # --- Sauvegarde ---
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Colonne 'type_contenu' mise a jour -> {DATA_PATH}")


if __name__ == "__main__":
    run()
