"""
================================================================================
 POST-PROCESSING DES TOPICS — Regroupement en Macro-Catégories
================================================================================

Ce script prend les ~91 topics découverts par BERTopic (Stage 1) et les
regroupe en ~16 macro-catégories lisibles et exploitables dans le dashboard.

Au lieu de relancer BERTopic (coûteux), on applique un mapping statique
    topic_number → macro-catégorie

ENTRÉE  : data/articles_topics.csv  (avec colonnes topic, topic_label)
SORTIE  : data/articles_topics.csv  (+ colonne macro_topic ajoutée)
================================================================================
"""

import os
import sys
import pandas as pd

DATA_PATH = "data/articles_topics.csv"

# =============================================================================
# MAPPING : numéro de topic BERTopic → macro-catégorie en français
# =============================================================================
TOPIC_TO_MACRO = {
    # --- Alzheimer & Démence ---
    0: "Alzheimer & Démence",
    47: "Alzheimer & Démence",       # synuclein / lewy

    # --- COVID-19 & Pandémies ---
    1: "COVID-19 & Pandémies",

    # --- Cardiologie ---
    2: "Cardiologie",                # heart failure
    37: "Cardiologie",               # cholesterol / cardiovascular
    40: "Cardiologie",               # stroke / ischemic
    69: "Cardiologie",               # congenital heart
    81: "Cardiologie",               # ecmo / cardiac arrest
    82: "Cardiologie",               # pulmonary embolism / VTE

    # --- Ophtalmologie ---
    3: "Ophtalmologie",              # retinal / glaucoma
    33: "Ophtalmologie",             # regional eye health

    # --- Oncologie ---
    4: "Oncologie",                  # cancer / chemotherapy
    10: "Oncologie",                 # cancer / tumor / expression
    17: "Oncologie",                 # surgery / gastric
    24: "Oncologie",                 # pancreatic cancer
    29: "Oncologie",                 # hpv / cervical cancer
    34: "Oncologie",                 # prostate cancer
    41: "Oncologie",                 # breast cancer
    52: "Oncologie",                 # tumors / carcinoma

    # --- Diabète & Métabolisme ---
    5: "Diabète & Métabolisme",      # diabetes / insulin
    21: "Diabète & Métabolisme",     # gestational diabetes
    50: "Diabète & Métabolisme",     # diabetic foot
    16: "Diabète & Métabolisme",     # thyroid / hormone

    # --- Maladies Respiratoires ---
    7: "Maladies Respiratoires",     # copd / asthma
    42: "Maladies Respiratoires",    # air pollution
    67: "Maladies Respiratoires",    # allergic rhinitis

    # --- Maladies Auto-immunes ---
    12: "Maladies Auto-immunes",     # rheumatoid arthritis
    13: "Maladies Auto-immunes",     # lupus
    20: "Maladies Auto-immunes",     # vasculitis
    25: "Maladies Auto-immunes",     # crohn / ibd
    35: "Maladies Auto-immunes",     # rheumatic heart
    75: "Maladies Auto-immunes",     # RA (doublon)
    85: "Maladies Auto-immunes",     # ITP / thrombocytopenia
    87: "Maladies Auto-immunes",     # inflammasome

    # --- Neurologie ---
    14: "Neurologie",                # multiple sclerosis
    19: "Neurologie",                # nmosd / encephalitis
    27: "Neurologie",                # transcranial stimulation
    39: "Neurologie",                # brain connectivity
    53: "Neurologie",                # parkinson
    62: "Neurologie",                # epilepsy
    79: "Neurologie",                # ALS
    83: "Neurologie",                # neuropathy
    86: "Neurologie",                # blood-brain barrier

    # --- Maladies Infectieuses ---
    11: "Maladies Infectieuses",     # antibiotic resistance
    22: "Maladies Infectieuses",     # HIV
    28: "Maladies Infectieuses",     # hepatitis B
    43: "Maladies Infectieuses",     # hepatitis C
    48: "Maladies Infectieuses",     # fungal infections
    49: "Maladies Infectieuses",     # HIV / PrEP
    59: "Maladies Infectieuses",     # tuberculosis
    64: "Maladies Infectieuses",     # diarrhea / parasitic
    65: "Maladies Infectieuses",     # herpes
    89: "Maladies Infectieuses",     # syphilis / STI

    # --- Gastro-entérologie & Hépatologie ---
    26: "Gastro-entérologie",        # liver / NAFLD
    44: "Gastro-entérologie",        # reflux / GERD

    # --- Biologie Moléculaire & Génétique ---
    6: "Biologie Moléculaire",       # mitochondrial / oxidative
    23: "Biologie Moléculaire",      # gene / protein
    54: "Biologie Moléculaire",      # mirnas
    56: "Biologie Moléculaire",      # genetic variants
    63: "Biologie Moléculaire",      # crispr
    66: "Biologie Moléculaire",      # autophagy
    74: "Biologie Moléculaire",      # ECM / matrix
    76: "Biologie Moléculaire",      # ferroptosis
    77: "Biologie Moléculaire",      # methylation / epigenetic
    31: "Biologie Moléculaire",      # antioxidant

    # --- Santé Publique & Épidémiologie ---
    8: "Santé Publique",             # cancer screening
    30: "Santé Publique",            # health / care / reporting
    57: "Santé Publique",            # mental health
    61: "Santé Publique",            # burden / global
    84: "Santé Publique",            # frailty / older

    # --- Pharmacologie & Thérapeutique ---
    15: "Pharmacologie",             # pain / anesthesia
    18: "Pharmacologie",             # drug delivery
    36: "Pharmacologie",             # fibromyalgia / chronic pain
    38: "Pharmacologie",             # safety / pharmacokinetics
    46: "Pharmacologie",             # sarcopenia / nutritional
    71: "Pharmacologie",             # vitamin / calcium
    73: "Pharmacologie",             # delirium / ICU

    # --- Imagerie & IA Médicale ---
    51: "Imagerie & IA Médicale",    # machine learning
    58: "Imagerie & IA Médicale",    # artificial intelligence
    70: "Imagerie & IA Médicale",    # CT / PET
    80: "Imagerie & IA Médicale",    # LLMs / large language

    # --- Autres Spécialités ---
    9: "Autres Spécialités",         # gut microbiota
    32: "Autres Spécialités",        # bruit français (la, en, et, des)
    45: "Autres Spécialités",        # rehabilitation
    55: "Autres Spécialités",        # wound / hydrogel
    60: "Autres Spécialités",        # hearing loss
    68: "Autres Spécialités",        # symptoms
    72: "Autres Spécialités",        # periodontal / teeth
    78: "Autres Spécialités",        # sleep / insomnia
    88: "Autres Spécialités",        # skin / dermatitis
}

# Fallback pour les topics non mappés (ex: -1 outliers)
DEFAULT_MACRO = "Autres Spécialités"


def run():
    if not os.path.exists(DATA_PATH):
        print(f"[ERREUR] Fichier '{DATA_PATH}' introuvable.")
        sys.exit(1)

    print(f"[INFO] Chargement de {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    if "topic" not in df.columns:
        print("[ERREUR] Colonne 'topic' absente. Lancez d'abord src/topic_modeling.py.")
        sys.exit(1)

    # --- Mapping topic → macro-catégorie ---
    df["macro_topic"] = df["topic"].map(TOPIC_TO_MACRO).fillna(DEFAULT_MACRO)

    # --- Bilan ---
    macro_counts = df["macro_topic"].value_counts()
    print(f"\n{'='*60}")
    print("  MACRO-CATÉGORIES ASSIGNÉES")
    print(f"{'='*60}")
    print(f"Nombre de macro-catégories : {df['macro_topic'].nunique()}")
    print(f"{'-'*60}")
    for cat, count in macro_counts.items():
        print(f"  {cat:<35} {count:>6} articles")
    print(f"{'='*60}")

    # --- Sauvegarde ---
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Colonne 'macro_topic' ajoutee -> {DATA_PATH}")


if __name__ == "__main__":
    run()
