import pandas as pd

df = pd.read_csv("data/raw_articles_final.csv", encoding="utf-8-sig")

total = len(df)
print("=" * 60)
print("  QUALITY REPORT — DiseaseScope")
print("=" * 60)
print(f"Total articles : {total}")
print(f"Columns        : {df.shape[1]}")

print("\n--- MISSING VALUES (15% threshold) ---")
important_columns = [
    "titre", "resume", "auteurs",
    "date_publication", "journal",
    "mots_cles", "maladie", "source",
]
all_ok = True
for col in important_columns:
    empty = (df[col] == "").sum() + df[col].isna().sum()
    pct = round(empty / total * 100, 1)
    if pct <= 15:
        status = "OK      "
    else:
        status = "EXCEEDS "
        all_ok = False
    print(f"{status} | {col:20} : {pct}% empty ({empty}/{total})")

print()
if all_ok:
    print("All columns pass the 15% threshold.")
else:
    print("Some columns exceed the 15% threshold. See details above.")

print("\n--- DUPLICATES ---")
duplicates = df.duplicated(subset=["titre"]).sum()
pct_dup = round(duplicates / total * 100, 1)
status = "OK" if pct_dup < 15 else "EXCEEDS"
print(f"{status} | Duplicates: {duplicates} ({pct_dup}%)")

print("\n--- BY SOURCE ---")
print(df["source"].value_counts().to_string())

print("\n--- BY DISEASE ---")
print(df["maladie"].value_counts().to_string())
