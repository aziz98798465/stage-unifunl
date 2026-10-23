
import csv
import json
import re
import time
from pathlib import Path
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# Configuration du scraper
URL = "https://books.toscrape.com/catalogue/category/books_1/index.html"
MAX_PAGES = 3
DELAI_ENTRE_REQUETES = 1
DOSSIER_SORTIE = Path(__file__).parent / "output"


def nettoyer_texte(texte):
    """Supprimer les espaces inutiles et gérer les valeurs manquantes."""
    if not texte:
        return None

    texte = " ".join(texte.split())
    return texte or None


def convertir_prix(prix_texte):
    """Convertir un prix comme £51.77 en nombre décimal."""
    if not prix_texte:
        return None

    valeur = re.sub(r"[^\d.,]", "", prix_texte)
    valeur = valeur.replace(",", ".")

    try:
        return float(Decimal(valeur))
    except (InvalidOperation, ValueError):
        return None


def scraper_produits(url, max_pages=MAX_PAGES):
    """Extraire les produits de plusieurs pages du catalogue."""
    headers = {
        "User-Agent": "StageUnifunlScraper/1.0"
    }

    resultats = []
    page_url = url

    with requests.Session() as session:
        session.headers.update(headers)

        for numero_page in range(1, max_pages + 1):
            print(f"\nScraping de la page {numero_page} : {page_url}")

            try:
                response = session.get(page_url, timeout=15)
                response.raise_for_status()
                response.encoding = "utf-8"

            except requests.RequestException as erreur:
                print(f"Erreur sur la page {numero_page} : {erreur}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            produits_html = soup.select("article.product_pod")

            if not produits_html:
                print("Aucun produit trouvé sur cette page.")
                break

            for produit in produits_html:
                titre_element = produit.select_one("h3 a")
                prix_element = produit.select_one(".price_color")
                image_element = produit.select_one("img")

                titre = nettoyer_texte(
                    titre_element.get("title")
                    if titre_element else None
                )

                prix_texte = nettoyer_texte(
                    prix_element.get_text(strip=True)
                    if prix_element else None
                )

                image_url = None

                if image_element and image_element.get("src"):
                    image_url = urljoin(
                        response.url,
                        image_element["src"]
                    )

                resultats.append({
                    "titre": titre,
                    "prix": convertir_prix(prix_texte),
                    "devise": "GBP" if prix_texte else None,
                    "image_url": image_url
                })

            # Rechercher le lien vers la page suivante
            lien_suivant = soup.select_one("li.next a")

            if not lien_suivant:
                print("Dernière page atteinte.")
                break

            page_url = urljoin(
                response.url,
                lien_suivant["href"]
            )

            # Attendre avant la prochaine requête
            if numero_page < max_pages:
                time.sleep(DELAI_ENTRE_REQUETES)

    return resultats


def exporter_json(produits, chemin):
    """Enregistrer les produits au format JSON."""
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(
            produits,
            fichier,
            ensure_ascii=False,
            indent=4
        )


def exporter_csv(produits, chemin):
    """Enregistrer les produits au format CSV compatible avec Excel."""
    champs = ["titre", "prix", "devise", "image_url"]

    with open(
        chemin,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as fichier:
        writer = csv.DictWriter(
            fichier,
            fieldnames=champs
        )

        writer.writeheader()
        writer.writerows(produits)


def main():
    """Point d'entrée principal du programme."""
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    try:
        produits = scraper_produits(URL)

        chemin_json = DOSSIER_SORTIE / "produits.json"
        chemin_csv = DOSSIER_SORTIE / "produits.csv"

        exporter_json(produits, chemin_json)
        exporter_csv(produits, chemin_csv)

        print("\n" + "=" * 50)
        print(f"Nombre total de produits extraits : {len(produits)}")
        print(f"Fichier JSON : {chemin_json}")
        print(f"Fichier CSV  : {chemin_csv}")
        print("=" * 50)

        for numero, produit in enumerate(produits, start=1):
            print(f"\nProduit {numero}")
            print(f"Titre : {produit['titre']}")
            print(f"Prix : {produit['prix']} {produit['devise']}")
            print(f"Image : {produit['image_url']}")

    except requests.RequestException as erreur:
        print(f"Erreur réseau : {erreur}")

    except OSError as erreur:
        print(f"Erreur lors de l'écriture des fichiers : {erreur}")


if __name__ == "__main__":
    main()
