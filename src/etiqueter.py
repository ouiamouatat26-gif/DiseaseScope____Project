import pandas as pd
import numpy as np
import os

print("[INFO] Chargement du dataset complet unifié depuis data/clean_articles.csv...")
if not os.path.exists("data/clean_articles.csv"):
    raise FileNotFoundError(
        "Le fichier data/clean_articles.csv est introuvable. "
        "Veuillez vérifier que vos scripts de scraping et de fusion ont bien été exécutés."
    )

df = pd.read_csv("data/clean_articles.csv", encoding="utf-8-sig")

# =========================================================================
# 🎯 CONFIGURATION DES LISTES DE MOTS-CLÉS RICHES ET EXCLUSIFS (8 CLASSES)
# =========================================================================

# 1. RECHERCHE FONDAMENTALE (Mécanismes biologiques, labo, modèles in vivo/vitro)
mots_basic_research = [
    "in vitro", "in vivo", "western blot", "transgenic mice", "cell culture", 
    "signaling pathway", "molecular mechanism", "receptor binding", "phosphorylation",
    "mrna expression", "recombinant", "assay", "murine model", "purified", "cloned", 
    "enzyme activity", "cellular", "protein kinase", "downregulation", "upregulation",
    "knockdown", "knockout mice", "cell viability", "apoptosis induction", "rabbits",
    "antagonist", "agonist", "inhibitor", "gene expression", "transfection", "signal transduction"
]

# 2. TRAITEMENTS ET ESSAIS CLINIQUES (Interventions, molécules, protocoles thérapeutiques)
mots_treatment = [
    "clinical trial", "phase iii", "randomized controlled", "efficacy and safety", 
    "adverse events", "chemotherapy", "surgical resection", "pharmacokinetics",
    "therapeutic", "dosage", "treatment outcome", "patients treated", "monotherapy", 
    "combination therapy", "dose-limiting", "toxicity profile", "placebo-controlled",
    "double-blind", "radiation therapy", "immunotherapy", "regimen", "drug administration",
    "tolerability", "adverse effects", "clinical efficacy", "standard of care"
]

# 3. DIAGNOSTIC ET IMAGERIE (Outils de détection, examens hospitaliers, biomarqueurs)
mots_diagnosis = [
    "diagnostic accuracy", "biomarker detection", "magnetic resonance imaging", "mri scan", 
    "computed tomography", "sensitivity and specificity", "biopsy confirmed", "ultrasound",
    "differential diagnosis", "radiological", "histopathological confirmation", "early detection",
    "positron emission", "pet scan", "diagnostic criteria", "imaging modalities", 
    "serum levels", "antibody testing", "false positive", "false negative", "electrocardiogram"
]

# 4. PRÉVENTION AND SANTÉ PUBLIQUE (Vaccins, hygiène de vie, protection)
mots_prevention = [
    "vaccination", "preventive", "risk reduction", "prophylaxis", "lifestyle intervention", 
    "dietary habits", "screening program", "protective factor", "chemoprevention", 
    "physical activity", "smoking cessation", "immunization", "public health intervention",
    "awareness campaign", "prophylactic", "healthy diet", "obesity prevention", "risk avoidance"
]

# 5. ÉCONOMIE DE LA SANTÉ (Coûts, efficacité financière, dépenses - expressions strictes)
mots_health_economics = [
    "cost-effectiveness", "health expenditure", "economic evaluation", "medical insurance", 
    "financial burden", "hospital costs", "reimbursement", "willingness to pay",
    "incremental cost", "qaly", "resource allocation", "budget impact", "direct medical costs",
    "cost-utility", "cost-benefit", "out-of-pocket", "healthcare financing", "economic cost"
]

# 6. BIO-INFORMATIQUE ET CALCUL (Séquençage, algorithmes, analyses in silico)
mots_bioinformatics = [
    "bioinformatics", "sequencing", "genome-wide", "rna-seq", "computational biology", 
    "microarray", "phylogenetic", "sequence alignment", "in silico", "data mining", 
    "machine learning algorithm", "molecular docking", "genomic data", "proteomic analysis",
    "transcriptomics", "metabolomics", "structural biology", "biostatistical", "pipeline analysis"
]

# 7. ÉPIDÉMIOLOGIE (Statistiques de populations, cohortes, prévalences)
mots_epidemiology = [
    "prevalence", "incidence rate", "cohort study", "mortality rate", "epidemiological", 
    "odds ratio", "confidence interval", "population-based", "case-control study", 
    "cross-sectional", "survival rate", "hazard ratio", "geographical distribution", 
    "risk factors analysis", "demographic characteristics", "global burden of disease"
]

# 8. CAS CLINIQUES (Rapports isolés, descriptions narratives de patients uniques)
mots_clinical_case = [
    "case report", "patient presented with", "clinical case", "rare case of", 
    "history of a 32-year-old", "a 45-year-old man", "a 60-year-old woman", 
    "physical examination revealed", "unusual presentation", "admitted to our hospital",
    "chief complaint", "symptoms persisted", "successfully treated with", "postoperative follow-up"
]

# Dictionnaire principal ordonné stratégiquement (des classes restrictives aux classes larges)
dictionnaire_8_classes = {
    "clinical_case": mots_clinical_case,
    "bioinformatics": mots_bioinformatics,
    "health_economics": mots_health_economics,
    "epidemiology": mots_epidemiology,
    "prevention": mots_prevention,
    "diagnosis": mots_diagnosis,
    "treatment": mots_treatment,
    "basic_research": mots_basic_research
}


def appliquer_mots_cles_riches(text):
    text = str(text).lower()
    
    # Étape 1 : Vérification des listes de mots-clés riches
    for score_class, keywords in dictionnaire_8_classes.items():
        if any(kw in text for kw in keywords):
            return score_class
            
    # Étape 2 : Secours sémantique pour la recherche fondamentale (mots génériques de labo)
    termes_labo = ["protein", "gene", "expression", "cell", "mouse", "rat", "dna", "rna", "antibody"]
    if any(w in text for w in termes_labo):
        return "basic_research"
        
    # Étape 3 : Valeur par défaut si aucun pattern n'est détecté
    return "basic_research"


# =========================================================================
# ⚙️ LOGIQUE DU PIPELINE D'ÉTIQUETAGE
# =========================================================================

# Fusion du titre et du résumé pour l'analyse textuelle globale
df["texte_complet"] = (df["titre"].fillna("") + " " + df["resume"].fillna("")).str.lower()

print("[INFO] Application de l'étiquetage par mots-clés riches...")
df["type_contenu"] = df["texte_complet"].apply(appliquer_mots_cles_riches)

# Extraction d'un échantillon d'entraînement élargi (3500 articles) pour nourrir le TF-IDF
SAMPLE_SIZE = min(3500, len(df))
print(f"[INFO] Extraction de l'échantillon d'entraînement (Taille : {SAMPLE_SIZE} articles)...")
df_sample = df.sample(n=SAMPLE_SIZE, random_state=42)

# Sauvegarde des fichiers dans le dossier data/
os.makedirs("data", exist_ok=True)

# Sauvegarde de la version brute pour le pipeline
df_sample.drop(columns=["texte_complet"]).to_csv("data/articles_etiquetes.csv", index=False, encoding="utf-8-sig")

print(f"\n==================================================================")
print(f"[OK] Fichier 'data/articles_etiquetes.csv' généré avec succès !")
print(f"==================================================================")
print("Répartition de vos 8 classes dans le nouveau dataset d'entraînement :")
print(df_sample["type_contenu"].value_counts().to_string())
print("==================================================================\n")
print("[ACTION] Tu peux maintenant exécuter ton script 'python src/train_model.py' !")