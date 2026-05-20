import re
from pathlib import Path
import pandas as pd

RAW_DATA_PATH = Path("data/raw_articles_final.csv")
CLEAN_DATA_PATH = Path("data/clean_articles.csv")

EXPECTED_COLUMNS = [
    "titre",
    "resume",
    "auteurs",
    "date_publication",
    "journal",
    "mots_cles",
    "maladie",
    "source",
    "lien",
    "type_contenu",
    "date_scraping",
]


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\+?\d[\d\s().-]{7,}\d", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_list_field(value):
    text = clean_text(value)
    if not text:
        return ""
    items = []
    for item in text.split("|"):
        item = clean_text(item)
        if item and item.lower() not in [existing.lower() for existing in items]:
            items.append(item)
    return " | ".join(items)


def clean_url(value):
    return "" if pd.isna(value) else str(value).strip()


def normalize_source(value):
    mapping = {
        "pubmed": "PubMed",
        "europe pmc": "Europe PMC",
        "who": "WHO",
        "clinicaltrials": "ClinicalTrials",
        "clinical trials": "ClinicalTrials",
        "medlineplus": "MedlinePlus",
    }
    cleaned = clean_text(value)
    return mapping.get(cleaned.lower(), cleaned)


def normalize_content_type(value):
    cleaned = clean_text(value).lower()
    if not cleaned:
        return "non_classifie"
    return cleaned.replace(" ", "_")


def main():
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"File not found: {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig")

    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[EXPECTED_COLUMNS]

    for column in ["titre", "resume", "journal", "maladie"]:
        df[column] = df[column].apply(clean_text)
    df["lien"] = df["lien"].apply(clean_url)
    df["auteurs"] = df["auteurs"].apply(clean_list_field)
    df["mots_cles"] = df["mots_cles"].apply(clean_list_field)
    df["source"] = df["source"].apply(normalize_source)
    df["type_contenu"] = df["type_contenu"].apply(normalize_content_type)

    df["maladie"] = df["maladie"].str.lower().str.strip()
    df["date_publication"] = df["date_publication"].fillna("Unknown").astype(str).str.strip()
    df["date_scraping"] = df["date_scraping"].fillna("").astype(str).str.strip()

    df = df[df["titre"] != ""]
    df = df[df["resume"] != ""]
    df = df.drop_duplicates(subset=["titre", "source", "maladie"])
    df = df.sort_values(["maladie", "source", "titre"]).reset_index(drop=True)

    CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_DATA_PATH, index=False, encoding="utf-8-sig")

    print("Cleaning complete.")
    print(f"Output file: {CLEAN_DATA_PATH}")
    print(f"Rows kept: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    missing = (df == "").sum()
    print("\nEmpty values after cleaning:")
    for column in EXPECTED_COLUMNS:
        print(f"  {column}: {missing.get(column, 0)}")


if __name__ == "__main__":
    main()
