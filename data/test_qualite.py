import pandas as pd

df = pd.read_csv("data/raw_articles_final.csv", encoding="utf-8-sig")

total = len(df)
print("=" * 60)
print("   RAPPORT QUALITÉ — DiseaseScope")
print("=" * 60)
print(f"📊 Total articles : {total}")
print(f"📋 Colonnes : {df.shape[1]}")

print("\n--- SEUIL 15% VALEURS MANQUANTES ---")
colonnes_importantes = ["titre", "resume", "auteurs", 
                        "date_publication", "journal", 
                        "mots_cles", "maladie", "source"]
tous_ok = True
for col in colonnes_importantes:
    vides = (df[col] == "").sum() + df[col].isna().sum()
    pct = round(vides / total * 100, 1)
    if pct <= 15:
        statut = "✅ OK"
    else:
        statut = "❌ DÉPASSE"
        tous_ok = False
    print(f"{statut} | {col:20} : {pct}% vide ({vides}/{total})")

print()
if tous_ok:
    print("✅ DONNÉES VALIDÉES — Prêtes pour le nettoyage")
else:
    print("⚠️  CERTAINS CHAMPS DÉPASSENT 15% — Voir détails ci-dessus")

print("\n--- DOUBLONS ---")
doublons = df.duplicated(subset=["titre"]).sum()
pct_doublons = round(doublons / total * 100, 1)
print(f"{'✅' if pct_doublons < 15 else '❌'} Doublons : {doublons} ({pct_doublons}%)")

print("\n--- PAR SOURCE ---")
print(df["source"].value_counts().to_string())

print("\n--- PAR MALADIE ---")
print(df["maladie"].value_counts().to_string())