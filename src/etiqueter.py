import pandas as pd

df = pd.read_csv("data/raw_articles_final.csv", encoding="utf-8-sig")
df["texte"] = (df["titre"].fillna("") + " " + df["resume"].fillna("")).str.lower()

def classifier(texte):
    treatment = ["treatment","therapy","drug","surgery","chemotherapy","immunotherapy","medication","clinical trial","intervention","dose","efficacy"]
    prevention = ["prevention","prevent","vaccine","vaccination","risk factor","screening","lifestyle","protect","reduce risk"]
    diagnosis  = ["diagnosis","diagnose","detection","biomarker","imaging","biopsy","mri","symptom","early detection","marker"]
    
    t = sum(1 for w in treatment  if w in texte)
    p = sum(1 for w in prevention if w in texte)
    d = sum(1 for w in diagnosis  if w in texte)
    
    if max(t,p,d) == 0: return "research"
    if t >= p and t >= d: return "treatment"
    if d >= p:            return "diagnosis"
    return "prevention"

df["type_contenu"] = df["texte"].apply(classifier)

print("=== Répartition ===")
print(df["type_contenu"].value_counts())
print(f"Total : {len(df)}")

df.to_csv("data/articles_etiquetes.csv", index=False, encoding="utf-8-sig")
print("data/articles_etiquetes.csv créé")