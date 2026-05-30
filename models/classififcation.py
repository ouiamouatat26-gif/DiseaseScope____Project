import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from pathlib import Path
import numpy as np

DATA_PATH = Path("data/raw_articles_final.csv")
VECTORIZED_PATH = Path("data/vectorized_articles.csv")
FINAL_PATH = Path("data/articles_with_predictions.csv")

def load_data():
    """Load the raw data from CSV"""
    print("Loading data...")
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    print(f"Total articles: {len(df)}")
    return df

def combine_text_features(df):
    """Combine title, abstract, and keywords for text vectorization"""
    df["combined_text"] = (
        df["titre"].fillna("") + " " +
        df["resume"].fillna("") + " " +
        df["mots_cles"].fillna("")
    )
    return df

def apply_tfidf_vectorization(df):
    """Apply TF-IDF vectorization to combined text"""
    print("Applying TF-IDF vectorization...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )
    
    tfidf_matrix = vectorizer.fit_transform(df["combined_text"])
    feature_names = vectorizer.get_feature_names_out()
    
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
    print(f"Number of features: {len(feature_names)}")
    
    return tfidf_matrix, vectorizer, feature_names

def save_vectorized_data(df, tfidf_matrix, feature_names):
    """Save vectorized data to CSV"""
    print("Saving vectorized data...")
    
    # Convert sparse matrix to dense array for a subset of features
    dense_matrix = tfidf_matrix.toarray()
    
    # Create DataFrame with vectorized features
    vectorized_df = pd.DataFrame(dense_matrix, columns=feature_names)
    
    # Add original columns
    for col in df.columns:
        if col != "combined_text":
            vectorized_df[col] = df[col].values
    
    # Save to CSV
    VECTORIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectorized_df.to_csv(VECTORIZED_PATH, index=False, encoding="utf-8-sig")
    print(f"Vectorized data saved to: {VECTORIZED_PATH}")
    
    return vectorized_df

def prepare_training_data(df):
    """Prepare labeled data for training"""
    print("Preparing training data...")
    
    # Filter labeled data (from Europe PMC and PubMed)
    labeled_mask = (df["source"].isin(["Europe PMC", "PubMed"])) & (df["type_contenu"] != "non_classifie")
    labeled_df = df[labeled_mask].copy()
    
    print(f"Labeled articles: {len(labeled_df)}")
    print(f"Label distribution:")
    print(labeled_df["type_contenu"].value_counts())
    
    # Group rare classes (less than 5 samples) into "other"
    label_counts = labeled_df["type_contenu"].value_counts()
    rare_classes = label_counts[label_counts < 5].index.tolist()
    
    if rare_classes:
        print(f"\nGrouping {len(rare_classes)} rare classes into 'other':")
        print(rare_classes)
        labeled_df["type_contenu"] = labeled_df["type_contenu"].apply(
            lambda x: "other" if x in rare_classes else x
        )
    
    print(f"\nLabel distribution after grouping:")
    print(labeled_df["type_contenu"].value_counts())
    
    return labeled_df

def train_classifier(labeled_df, tfidf_matrix, df):
    """Train Random Forest classifier on labeled data"""
    print("Training Random Forest classifier...")
    
    # Get indices of labeled articles
    labeled_indices = df[(df["source"].isin(["Europe PMC", "PubMed"])) & (df["type_contenu"] != "non_classifie")].index
    
    # Get TF-IDF features for labeled data
    X_labeled = tfidf_matrix[labeled_indices]
    y_labeled = df.loc[labeled_indices, "type_contenu"]
    
    # Split into train/test (without stratification due to rare classes)
    X_train, X_test, y_train, y_test = train_test_split(
        X_labeled, y_labeled, test_size=0.2, random_state=42
    )
    
    print(f"Training set size: {X_train.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")
    
    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    return clf

def predict_unlabeled(clf, df, tfidf_matrix):
    """Predict types for unlabeled articles"""
    print("Predicting types for unlabeled articles...")
    
    # Filter unlabeled data
    unlabeled_mask = df["type_contenu"] == "non_classifie"
    unlabeled_indices = df[unlabeled_mask].index
    
    print(f"Unlabeled articles: {len(unlabeled_indices)}")
    
    if len(unlabeled_indices) == 0:
        print("No unlabeled articles found.")
        return df
    
    # Get TF-IDF features for unlabeled data
    X_unlabeled = tfidf_matrix[unlabeled_indices]
    
    # Predict
    predictions = clf.predict(X_unlabeled)
    probabilities = clf.predict_proba(X_unlabeled)
    
    # Update dataframe with predictions
    df.loc[unlabeled_indices, "type_contenu"] = predictions
    df.loc[unlabeled_indices, "prediction_confidence"] = np.max(probabilities, axis=1)
    
    print(f"Predictions made for {len(unlabeled_indices)} articles")
    
    return df

def save_final_data(df):
    """Save final data with predictions"""
    print("Saving final data with predictions...")
    
    FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FINAL_PATH, index=False, encoding="utf-8-sig")
    print(f"Final data saved to: {FINAL_PATH}")
    
    # Print summary
    print("\n=== FINAL SUMMARY ===")
    print(f"Total articles: {len(df)}")
    print(f"\nType contenu distribution:")
    print(df["type_contenu"].value_counts())
    print(f"\nBy source:")
    print(df.groupby("source")["type_contenu"].value_counts())

def main():
    # Load data
    df = load_data()
    
    # Combine text features
    df = combine_text_features(df)
    
    # Apply TF-IDF vectorization
    tfidf_matrix, vectorizer, feature_names = apply_tfidf_vectorization(df)
    
    # Save vectorized data
    save_vectorized_data(df, tfidf_matrix, feature_names)
    
    # Prepare training data
    labeled_df = prepare_training_data(df)
    
    if len(labeled_df) == 0:
        print("No labeled data found. Cannot train classifier.")
        return
    
    # Train classifier
    clf = train_classifier(labeled_df, tfidf_matrix, df)
    
    # Predict unlabeled articles
    df = predict_unlabeled(clf, df, tfidf_matrix)
    
    # Save final data
    save_final_data(df)
    
    print("\n=== Classification complete ===")

if __name__ == "__main__":
    main()
