# DiseaseScope 🏥
Système de Veille Intelligente sur les Maladies Chroniques
via la Presse Médicale Mondiale

---

## C'est quoi ce projet ?
Un agrégateur intelligent qui :
- Scrape des articles médicaux depuis PubMed, WebMD et WHO
- Stocke les données dans MongoDB
- Classifie les articles avec un modèle Machine Learning (Random Forest)
- Visualise les tendances dans une interface web

---

## Technologies utilisées
- Python 3
- BeautifulSoup / Requests (scraping)
- MongoDB (base de données)
- Pandas (nettoyage des données)
- Scikit-learn (modèle ML)
- Streamlit (interface web)

---

## Comment installer le projet sur ta machine

### 1. Cloner le projet
git clone https://github.com/ton-compte/DiseaseScope___Project.git
cd DiseaseScope___Project

### 2. Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate        (Windows)
source venv/bin/activate     (Mac/Linux)

### 3. Installer les bibliothèques
pip install -r requirements.txt

### 4. Lancer le scraper PubMed
python scrapers/pubmed_scraper.py

---



## Avancement du projet

### Semaine 1 — Scraping ✅
- [x] Scraper PubMed via API officielle
- [x] 302 articles stockés dans MongoDB
- [ ] Scraper WebMD 
- [ ] Scraper WHO
### Semaine 2 — Nettoyage 🔜
### Semaine 3 — Qualité des données 🔜
### Semaine 4 — Machine Learning 🔜
### Semaine 5 — Interface Streamlit 🔜
### Semaine 6 — Rapport + Soutenance 🔜
