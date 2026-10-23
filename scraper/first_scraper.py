
import csv
import json
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup


# Configuration
URL = "https://books.toscrape.com/catalogue/category/books_1/index.html"
MAX_PAGES = 3
DELAI_ENTRE_REQUETES = 1
TIMEOUT = 15

DOSSIER_SORTIE = Path(__file__).parent / "output"


def valider_url(url):
    """Vérifier que l'URL possède un schéma HTTP(S) et un hôte."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("L'URL est vide ou invalide.")

    parties = urlparse(url.strip())

    if parties.scheme not in ("http", "https") or not parties.hostname:
        raise ValueError("L'URL doit commencer par http:// ou https://.")

    return url.strip()


def creer_session():
    """Créer une session HTTP avec des tentatives en cas d'erreur temporaire."""
    session = requests.Session()

    session.headers.update({
        "User-Agent": "StageUnifunlScraper/1.0"
    })

    strategie = Retry(
        total=3,
        connect=3,
        read=2,
        status=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adaptateur = HTTPAdapter(max_retries=strategie)
    session.mount("https://", adaptateur)
    session.mount("http://", adaptateur)

    return session


def nettoyer_texte(texte):
    """Nettoyer les espaces et traiter les valeurs manquantes."""
    if texte is None:
        return None

    texte = " ".join(texte.split())
    return texte or None


def convertir_prix(prix_texte):
    """Convertir un prix comme £51.77 en nombre."""
    if not prix_texte:
        return None

    valeur = re.sub(r"[^\d.,]", "", prix_texte)
    valeur = valeur.replace(",", ".")

    try:
        return float(Decimal(valeur))
    except (InvalidOperation, ValueError):
        return None


def extraire_produits(soup, url_page):
    """Extraire les produits présents dans une page HTML."""
    produits = []

    for element in soup.select("article.product_pod"):
        titre_element = element.select_one("h3 a")
        prix_element = element.select_one(".price_color")
        image_element = element.select_one("img")

        titre = nettoyer_texte(
            titre_element.get("title") if titre_element else None
        )

        prix_texte = nettoyer_texte(
            prix_element.get_text(strip=True)
            if prix_element else None
        )

        image_url = None

        if image_element and image_element.get("src"):
            image_url = urljoin(url_page, image_element["src"])

        # Ignorer une fiche sans titre exploitable.
        if not titre:
            print("Attention : produit ignoré car son titre est absent.")
            continue

        produits.append({
            "titre": titre,
            "prix": convertir_prix(prix_texte),
            "devise": "GBP" if prix_texte else None,
            "image_url": image_url,
        })

    return produits


def scraper_produits(url, max_pages=MAX_PAGES):
    """Scraper plusieurs pages avec gestion des erreurs."""
    url = valider_url(url)

    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or max_pages < 1:
        raise ValueError("max_pages doit être un entier supérieur ou égal à 1.")

    resultats = []
    page_url = url
    pages_reussies = 0

    with creer_session() as session:
        for numero_page in range(1, max_pages + 1):
            print(f"\nPage {numero_page} : {page_url}")

            try:
                response = session.get(page_url, timeout=TIMEOUT)
                response.raise_for_status()

            except requests.RequestException as erreur:
                print(f"Erreur HTTP ou réseau : {erreur}")
                print("Arrêt de la pagination.")
                break

            # Laisser Requests détecter l'encodage lorsque c'est possible.
            soup = BeautifulSoup(response.content, "html.parser")
            produits_page = extraire_produits(soup, response.url)

            if not produits_page:
                print("Aucun produit exploitable trouvé sur cette page.")
                break

            resultats.extend(produits_page)
            pages_reussies += 1

            print(f"Produits récupérés sur cette page : {len(produits_page)}")

            lien_suivant = soup.select_one("li.next a")

            if not lien_suivant:
                print("Fin de la pagination.")
                break

            page_url = urljoin(response.url, lien_suivant["href"])

            if numero_page < max_pages:
                time.sleep(DELAI_ENTRE_REQUETES)

    print(f"\nPages traitées avec succès : {pages_reussies}")
    print(f"Total de produits récupérés : {len(resultats)}")

    return resultats


def exporter_json(produits, chemin):
    """Exporter les produits au format JSON."""
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(produits, fichier, ensure_ascii=False, indent=4)


def exporter_csv(produits, chemin):
    """Exporter les produits au format CSV compatible avec Excel."""
    champs = ["titre", "prix", "devise", "image_url"]

    with open(chemin, "w", newline="", encoding="utf-8-sig") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs)
        writer.writeheader()
        writer.writerows(produits)


def main():
    """Lancer le scraping et enregistrer les résultats."""
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    try:
        produits = scraper_produits(URL)

        chemin_json = DOSSIER_SORTIE / "produits.json"
        chemin_csv = DOSSIER_SORTIE / "produits.csv"

        exporter_json(produits, chemin_json)
        exporter_csv(produits, chemin_csv)

        print("\n" + "=" * 50)
        print(f"Produits exportés : {len(produits)}")
        print(f"JSON : {chemin_json}")
        print(f"CSV  : {chemin_csv}")
        print("=" * 50)

        if not produits:
            print("Attention : aucun produit n'a été exporté.")

    except (ValueError, OSError) as erreur:
        print(f"Erreur : {erreur}")


if __name__ == "__main__":
    main()
