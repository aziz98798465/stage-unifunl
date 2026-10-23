
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
DELAI_ENTRE_REQUETES = 0.5
TIMEOUT = 15
NOMBRE_REQUETES_PARALLELES = 3

DOSSIER_SORTIE = Path(__file__).parent / "output"


def valider_url(url):
    """Vérifier que l'URL possède un schéma HTTP(S) et un hôte."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("L'URL est vide ou invalide.")

    url = url.strip()
    parties = urlparse(url)

    if parties.scheme not in ("http", "https") or not parties.hostname:
        raise ValueError(
            "L'URL doit commencer par http:// ou https://."
        )

    return url


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

    adaptateur = HTTPAdapter(
        max_retries=strategie,
        pool_connections=NOMBRE_REQUETES_PARALLELES,
        pool_maxsize=NOMBRE_REQUETES_PARALLELES,
    )

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


def telecharger_page(session, url):
    """Télécharger une page et vérifier la réponse HTTP."""
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response


def decouvrir_pages(session, url, max_pages):
    """
    Télécharger les pages en suivant la pagination et conserver
    leur contenu HTML pour éviter de les télécharger une seconde fois.
    """
    pages = []
    url_page = url

    for numero_page in range(1, max_pages + 1):
        print(f"\nTéléchargement de la page {numero_page} : {url_page}")

        try:
            response = telecharger_page(session, url_page)
        except requests.RequestException as erreur:
            print(f"Erreur HTTP ou réseau : {erreur}")
            break

        soup = BeautifulSoup(response.content, "html.parser")

        # Conserver le contenu déjà téléchargé.
        pages.append({
            "url": response.url,
            "contenu": response.content,
        })

        lien_suivant = soup.select_one("li.next a")

        if not lien_suivant:
            print("Fin de la pagination.")
            break

        url_page = urljoin(response.url, lien_suivant["href"])

        if numero_page < max_pages:
            time.sleep(DELAI_ENTRE_REQUETES)

    return pages


def extraire_page_telechargee(page):
    """Extraire les produits du HTML déjà téléchargé, sans nouvelle requête."""
    soup = BeautifulSoup(page["contenu"], "html.parser")

    produits = extraire_produits(soup, page["url"])

    return {
        "url": page["url"],
        "produits": produits,
    }


def scraper_produits(url, max_pages=MAX_PAGES):
    """Télécharger chaque page une seule fois et traiter le HTML en parallèle."""
    url = valider_url(url)

    if (
        not isinstance(max_pages, int)
        or isinstance(max_pages, bool)
        or max_pages < 1
    ):
        raise ValueError(
            "max_pages doit être un entier supérieur ou égal à 1."
        )

    with creer_session() as session:
        pages = decouvrir_pages(session, url, max_pages)

    if not pages:
        print("Aucune page n'a pu être récupérée.")
        return []

    print(
        f"\nExtraction des {len(pages)} page(s) déjà téléchargées, "
        f"avec un maximum de {NOMBRE_REQUETES_PARALLELES} tâches simultanées."
    )

    resultats_par_page = {}
    pages_reussies = 0
    erreurs = []

    with ThreadPoolExecutor(
        max_workers=NOMBRE_REQUETES_PARALLELES
    ) as executant:
        futures = {
            executant.submit(extraire_page_telechargee, page): (
                indice,
                page["url"],
            )
            for indice, page in enumerate(pages)
        }

        for future in as_completed(futures):
            indice, url_page = futures[future]

            try:
                resultat = future.result()
                resultats_par_page[indice] = resultat["produits"]
                pages_reussies += 1

                print(
                    f"Page traitée : {url_page} "
                    f"({len(resultat['produits'])} produits)"
                )

            except Exception as erreur:
                erreurs.append((url_page, str(erreur)))
                print(
                    f"Erreur lors du traitement de {url_page} : {erreur}"
                )

    # Restaurer l'ordre des pages, même si les tâches finissent différemment.
    produits = []

    for indice in sorted(resultats_par_page):
        produits.extend(resultats_par_page[indice])

    print(f"\nPages traitées avec succès : {pages_reussies}")

    if erreurs:
        print(f"Pages en erreur : {len(erreurs)}")

    print(f"Total de produits récupérés : {len(produits)}")

    return produits


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
        debut = time.perf_counter()
        produits = scraper_produits(URL)
        duree = time.perf_counter() - debut

        chemin_json = DOSSIER_SORTIE / "produits.json"
        chemin_csv = DOSSIER_SORTIE / "produits.csv"

        exporter_json(produits, chemin_json)
        exporter_csv(produits, chemin_csv)

        print("\n" + "=" * 50)
        print(f"Produits exportés : {len(produits)}")
        print(f"JSON : {chemin_json}")
        print(f"CSV  : {chemin_csv}")
        print(f"Durée du scraping : {duree:.2f} seconde(s)")
        print("=" * 50)

        if not produits:
            print("Attention : aucun produit n'a été exporté.")

    except (ValueError, OSError) as erreur:
        print(f"Erreur : {erreur}")


if __name__ == "__main__":
    main()
