import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

df = pd.read_csv("data/articles_etiquetes.csv", encoding="utf-8-sig")
df = df[df["texte"].notna()].head(100)

vectorizer = TfidfVectorizer(max_features=20, stop_words="english")
X = vectorizer.fit_transform(df["texte"])

df_tfidf = pd.DataFrame(
    X.toarray(),
    columns=vectorizer.get_feature_names_out()
)
df_tfidf["titre"]        = df["titre"].values
df_tfidf["type_contenu"] = df["type_contenu"].values
df_tfidf["maladie"]      = df["maladie"].values

df_tfidf.to_csv("data/tfidf_sample.csv", index=False, encoding="utf-8-sig")
print(" data/tfidf_sample.csv créé")
print(f"Shape : {df_tfidf.shape}")
print("\nAperçu des 5 premiers mots TF-IDF :")
print(df_tfidf.iloc[:3, :5])
