import pandas as pd
import os

# Configuration de la taille de l'échantillon pour validation humaine
SAMPLE_SIZE = 100
RANDOM_STATE = 42

print(f"[INFO] Chargement des articles depuis data/clean_articles.csv...")
if not os.path.exists("data/clean_articles.csv"):
    raise FileNotFoundError("Le fichier data/clean_articles.csv est introuvable. Veuillez exécuter le nettoyage des données d'abord.")

df = pd.read_csv("data/clean_articles.csv", encoding="utf-8-sig")
print(f"[INFO] Total d'articles disponibles : {len(df)}")

# Sélection de l'échantillon pour validation humaine (Human-in-the-loop)
print(f"[INFO] Sélection d'un échantillon aléatoire de {SAMPLE_SIZE} articles...")
sample_df = df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=RANDOM_STATE).copy()

# Préparation du texte pour la classification par mots-clés
sample_df["texte"] = (sample_df["titre"].fillna("") + " " + sample_df["resume"].fillna("")).str.lower()

def classifier(texte):
    # Dictionnaire de mots-clés enrichi
    treatment = [
        "treatment", "therapy", "therapeutic", "drug", "medication", 
        "surgery", "surgical", "chemotherapy", "radiotherapy", 
        "immunotherapy", "clinical trial", "dose", "dosage", "efficacy", 
        "intervention", "patient", "treated", "pharmacology"
    ]
    
    prevention = [
        "prevention", "preventive", "prevent", "vaccine", "vaccination", 
        "risk factor", "screening", "lifestyle", "protect", "diet", 
        "exercise", "prophylaxis", "reduce risk", "public health", 
        "epidemiology", "hygiene"
    ]
    
    diagnosis = [
        "diagnosis", "diagnose", "diagnostic", "detection", "biomarker", 
        "imaging", "biopsy", "mri", "symptom", "early detection", 
        "marker", "sensitivity", "specificity", "scan", "ultrasound", 
        "screening tool", "assay"
    ]
    
    research = [
        "mechanism", "molecular", "pathway", "in vitro", "in vivo", 
        "animal model", "mouse", "mice", "cellular", "gene expression", 
        "protein structure", "hypothesis", "investigate", "characterize", 
        "fundamental", "basic research", "scientific", "regulation", 
        "cellular signaling", "interaction", "expression levels", 
        "inhibit", "activation", "cloning", "crystallography", 
        "spectrometry", "recombinant"
    ]
    
    t = sum(1 for w in treatment  if w in texte)
    p = sum(1 for w in prevention if w in texte)
    d = sum(1 for w in diagnosis  if w in texte)
    r = sum(1 for w in research   if w in texte)
    
    counts = {"treatment": t, "prevention": p, "diagnosis": d, "research": r}
    max_val = max(counts.values())
    
    # Si aucun mot-clé ne correspond, on classe dans 'other'
    if max_val == 0:
        return "other"
    
    # Résolution des égalités par ordre de priorité
    priority = ["treatment", "diagnosis", "prevention", "research"]
    candidates = [k for k, v in counts.items() if v == max_val]
    for cat in priority:
        if cat in candidates:
            return cat
            
    return candidates[0]

# Application de la classification
sample_df["type_contenu"] = sample_df["texte"].apply(classifier)

print("\n=== Répartition initiale de l'échantillon ===")
print(sample_df["type_contenu"].value_counts())
print(f"Taille finale de l'échantillon : {len(sample_df)}")

# Sauvegarde de l'échantillon pour validation humaine
os.makedirs("data", exist_ok=True)
sample_df.to_csv("data/articles_etiquetes.csv", index=False, encoding="utf-8-sig")

print("\n[OK] data/articles_etiquetes.csv a été créé avec succès !")
print("[ACTION REQUISE] Veuillez ouvrir 'data/articles_etiquetes.csv' et vérifier / corriger manuellement")
print("                 la colonne 'type_contenu' avant de lancer 'python src/train_model.py'.")