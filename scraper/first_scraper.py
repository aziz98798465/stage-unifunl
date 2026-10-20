
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Site de test conçu pour apprendre le web scraping
URL = "https://books.toscrape.com/catalogue/category/books_1/index.html"

def scraper_produits(url):
    headers = {
        "User-Agent": "StageUnifunlScraper/1.0"
    }

    # Envoyer la requête HTTP
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"

    # Analyser le HTML
    soup = BeautifulSoup(response.text, "html.parser")

    produits = soup.select("article.product_pod")

    resultats = []

    for produit in produits[:5]:
        titre_element = produit.select_one("h3 a")
        prix_element = produit.select_one(".price_color")
        image_element = produit.select_one("img")

        titre = (
            titre_element.get("title", "").strip()
            if titre_element else "Titre indisponible"
        )

        prix = (
            prix_element.get_text(strip=True)
            if prix_element else "Prix indisponible"
        )

        image_url = (
            urljoin(url, image_element.get("src", ""))
            if image_element else None
        )

        resultats.append({
            "titre": titre,
            "prix": prix,
            "image_url": image_url
        })

    return resultats


if __name__ == "__main__":
    try:
        produits = scraper_produits(URL)

        print(f"Nombre de produits extraits : {len(produits)}\n")

        for numero, produit in enumerate(produits, start=1):
            print(f"Produit {numero}")
            print(f"Titre : {produit['titre']}")
            print(f"Prix : {produit['prix']}")
            print(f"Image : {produit['image_url']}")
            print("-" * 50)

    except requests.RequestException as erreur:
        print(f"Erreur HTTP ou réseau : {erreur}")
