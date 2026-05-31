# DiseaseScope 🏥

**Système de Veille Intelligente sur les Maladies Chroniques via la Presse Médicale Mondiale**

---

## Description du projet

DiseaseScope est un agrégateur intelligent d'articles médicaux qui :

- **Collecte** des articles depuis 5 sources médicales majeures (PubMed, Europe PMC, ClinicalTrials, WHO, MedlinePlus)
- **Stocke** les données dans MongoDB avec fusion et dédoublonnage automatiques
- **Nettoie** et normalise les données (textes, URLs, noms de sources, dates)
- **Classifie** automatiquement le type de contenu de chaque article grâce à un modèle de Machine Learning (Random Forest + TF-IDF)
- **Visualise** les tendances et statistiques dans un dashboard web interactif avec graphiques et filtres avancés

> **5 704 articles** collectés et classifiés couvrant **10 catégories de maladies** depuis **5 sources** différentes.

---

## Technologies utilisées

| Catégorie | Technologies |
| :--- | :--- |
| **Langage** | Python 3 |
| **Scraping** | BeautifulSoup, Requests |
| **Base de données** | MongoDB (via PyMongo) |
| **Traitement des données** | Pandas, SciPy |
| **Machine Learning** | Scikit-learn (TF-IDF, Random Forest, LinearSVC, Logistic Regression, Naive Bayes) |
| **Interface Web** | Flask, HTML/CSS/JavaScript, Chart.js |
| **Gestion de données** | DVC (Data Version Control) |
| **Sérialisation des modèles** | Joblib |

---

## Architecture du projet

```
DiseaseScope____Project-main/
│
├── scrapers/                      # Scripts de collecte de données
│   ├── pubmed_scraper.py          # Scraper PubMed (API E-utilities)
│   ├── europepmc_scraper.py       # Scraper Europe PMC
│   ├── who_scraper.py             # Scraper WHO (OMS)
│   ├── clinicaltrials_scraper.py  # Scraper ClinicalTrials.gov
│   ├── medlineplus_scraper.py     # Scraper MedlinePlus
│   ├── fusionner.py               # Fusion, dédoublonnage et export MongoDB
│   └── validation_quality.py      # Validation qualité post-fusion
│
├── data/                          # Jeux de données
│   ├── raw_articles_final.csv     # Articles bruts fusionnés (5 704 articles)
│   ├── clean_articles.csv         # Articles nettoyés et classifiés
│   ├── articles_etiquetes.csv     # Articles étiquetés (méthode par mots-clés)
│   └── test_qualite.py            # Script de contrôle qualité des données
│
├── src/                           # Scripts de traitement et ML
│   ├── clean_data.py              # Nettoyage et normalisation des données
│   ├── etiqueter.py               # Étiquetage initial par mots-clés
│   ├── vectorization.py           # Vectorisation TF-IDF
│   ├── exporter_tfidf.py          # Export de la matrice TF-IDF
│   ├── classification.py          # Classification SVM linéaire
│   ├── train_model.py             # Entraînement Random Forest (type de contenu)
│   ├── train_disease_classifier.py    # Comparaison de modèles (prédiction maladie)
│   ├── train_content_type_classifier.py # Comparaison de modèles (type de contenu)
│   ├── predire.py                 # Prédiction sur l'ensemble du dataset
│   ├── test_inference.py          # Tests d'inférence en direct
│   └── verify_predictions.py      # Validation finale des prédictions ML
│
├── models/                        # Modèles entraînés sauvegardés
│   ├── random_forest.joblib       # Modèle Random Forest (type de contenu)
│   ├── tfidf.joblib               # Vectoriseur TF-IDF associé
│   ├── label_encoder.joblib       # Encodeur de labels
│   ├── best_disease_model.joblib  # Meilleur modèle (prédiction maladie)
│   ├── best_disease_vectorizer.joblib
│   ├── best_content_type_model.joblib # Meilleur modèle (type de contenu)
│   ├── best_content_type_vectorizer.joblib
│   └── metrics.json               # Métriques du modèle (accuracy, classes)
│
├── templates/                     # Templates HTML (Flask)
│   └── index.html                 # Dashboard principal
│
├── visualizations/                # Graphiques statiques exportés
│   ├── 1_articles_by_disease.png
│   ├── 2_articles_by_source.png
│   ├── 3_publication_timeline.png
│   ├── 4_top_keywords.png
│   ├── 5_disease_source_coverage.png
│   └── 6_content_types.png
│
├── app.py                         # Serveur Flask (API + Dashboard)
├── requirements.txt               # Dépendances Python
└── README.md
```

---

## Pipeline de données

```
[Scrapers]  →  [MongoDB]  →  [Fusion & Dédoublonnage]  →  [CSV brut]
                                                              ↓
                                                     [Nettoyage & Normalisation]
                                                              ↓
                                                     [Vectorisation TF-IDF]
                                                              ↓
                                                     [Entraînement ML]
                                                              ↓
                                                     [Classification automatique]
                                                              ↓
                                                     [Dashboard Streamlit]
```

---

## Classification par Machine Learning

### Scénario 1 — Prédiction de la maladie
Le modèle prédit la catégorie de maladie associée à chaque article à partir du titre et du résumé. Quatre algorithmes sont comparés (Naive Bayes, Logistic Regression, LinearSVC, Random Forest) et le meilleur est automatiquement sélectionné.

### Scénario 2 — Prédiction du type de contenu
Le modèle classe chaque article dans l'une des 4 catégories suivantes :

| Type de contenu | Description | % du dataset |
| :--- | :--- | :---: |
| **Treatment** | Traitements, essais cliniques, médicaments | 41,8 % |
| **Research** | Recherche fondamentale, analyses épidémiologiques | 31,4 % |
| **Diagnosis** | Diagnostic, imagerie, biomarqueurs, détection | 16,4 % |
| **Prevention** | Prévention, vaccination, facteurs de risque | 10,4 % |

**Performance du modèle :** Accuracy de **83,87 %** (Random Forest, TF-IDF avec 5 000 features, n-grams (1,2)).

---

## Installation et lancement

### 1. Cloner le projet

```bash
git clone https://github.com/ton-compte/DiseaseScope___Project.git
cd DiseaseScope___Project
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
pip install flask pandas scikit-learn scipy joblib
```

### 4. Lancer les scrapers (optionnel — données déjà incluses)

```bash
python scrapers/pubmed_scraper.py
python scrapers/europepmc_scraper.py
python scrapers/who_scraper.py
python scrapers/clinicaltrials_scraper.py
python scrapers/medlineplus_scraper.py
```

### 5. Fusionner et nettoyer les données

```bash
python scrapers/fusionner.py
python src/clean_data.py
```

### 6. Entraîner les modèles ML

```bash
python src/train_model.py
python src/train_disease_classifier.py
python src/train_content_type_classifier.py
```

### 7. Classifier et valider les articles

```bash
python src/verify_predictions.py
```

### 8. Lancer le dashboard web

```bash
streamlit run streamlit_app.py

```


> **Note :** Le dashboard fonctionne même sans MongoDB grâce au mode de secours CSV automatique. Si MongoDB est disponible, il sera utilisé automatiquement.

---
## 📊 Fonctionnalités du Dashboard

L'interface de **DiseaseScope** est une application web interactive et moderne développée avec **Streamlit**, arborant un design épuré et professionnel adapté à l'intelligence de recherche médicale. Elle s'articule autour de 3 modules principaux accessibles depuis la barre latérale :

### 1. 📊 Dashboard Analytics (Vue d'ensemble)
Cette page offre une vision macroscopique et statistique immédiate sur l'ensemble du corpus de données extrait (scraping et APIs).
* **KPIs Dynamiques :** Suivi en temps réel des indicateurs clés (Nombre total d'articles indexés, diversité des sources médicales, volume de pathologies traitées et typologies de contenu).
* **Visualisations Avancées (Plotly) :**
  * **Distribution par Pathologie :** Histogramme interactif des volumes de publications par maladie.
  * **Répartition par Source :** Graphique de type *Donut* affichant la part de marché de chaque base de données ou journal.
  * **Évolution Temporelle :** Graphique d'aire (*Area Chart Spline*) lissant la chronologie des publications.
  * **Matrices Croisées (Heatmaps) :** Deux matrices de corrélation interactives (`Pathologie × Type de contenu` et `Pathologie × Source`) pour détecter instantanément les axes de recherche les plus denses.

### 2. 🔍 Recherche Scientifique & Filtrage Multi-Critères
Un moteur de recherche à facettes pour explorer chirurgicalement la base de données d'articles indexés.
* **Filtres Nominatifs :** Tri instantané par *Pathologie*, *Type de contenu* (essais cliniques, articles scientifiques, rapports de l'OMS), et *Source*.
* **Curseur Temporel :** Un composant *Slider* pour restreindre la recherche à une plage d'années spécifique.
* **Recherche Textuelle Libre :** Analyse de chaîne de caractères en temps réel isolant des mots-clés au sein des **titres** ou des **résumés** (abstracts).
* **Pagination Optimisée :** Segmentation fluide de l'affichage des résultats par blocs d'articles pour garantir des performances optimales de l'interface.

### 3. 🧪 Test Modèle ML (Inférence en direct)
Une interface de test d'intelligence artificielle permettant de simuler l'évaluation et la classification de nouveaux textes médicaux en direct.
* **Saisie Intuitive :** Formulaire de saisie pour soumettre le titre et le résumé d'une nouvelle étude clinique ou d'un rapport de santé.
* **Inférence Multi-Tâches :** Requêtage instantané des modèles de Machine Learning entraînés en arrière-plan (`Random Forest` + vectorisation `TF-IDF`).
* **Double Prédiction :** Génération automatique de deux badges de classification indépendants :
  1. La **Pathologie** suspectée (ex: *Alzheimer*, *Cancer*, *Diabète*).
  2. Le **Type de publication** sémantique (ex: *Clinical Trial*, *Scientific Article*, *Report Guideline*).

---