import requests
from bs4 import BeautifulSoup

# On va juste regarder ce que PubMed nous envoie
url = "https://pubmed.ncbi.nlm.nih.gov/?term=cancer"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Chercher les articles avec différents noms possibles
print("=== Test 1 : full-docsum ===")
articles1 = soup.find_all("article", class_="full-docsum")
print(f"Trouvé : {len(articles1)} articles")

print("\n=== Test 2 : tous les <article> ===")
articles2 = soup.find_all("article")
print(f"Trouvé : {len(articles2)} articles")

print("\n=== Test 3 : divs avec 'docsum' ===")
articles3 = soup.find_all("div", class_=lambda c: c and "docsum" in c)
print(f"Trouvé : {len(articles3)} éléments")

# Afficher un bout du HTML pour voir la vraie structure
print("\n=== Début du HTML reçu ===")
print(soup.prettify()[:3000])