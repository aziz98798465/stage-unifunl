
import csv
import json
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


# Configuration
URL = "https://quotes.toscrape.com/js/"
DOSSIER_SORTIE = Path(__file__).parent / "output"


def nettoyer_texte(texte):
    """Nettoyer les espaces et les retours à la ligne."""
    if not texte:
        return None

    texte = " ".join(texte.split())
    return texte or None


def scraper_citations():
    """Ouvrir le navigateur et extraire les citations affichées."""
    citations = []

    with sync_playwright() as playwright:
        navigateur = playwright.chromium.launch(headless=True)

        try:
            page = navigateur.new_page()
            page.set_default_timeout(15000)

            print(f"Ouverture de la page : {URL}")

            response = page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            if response is not None and response.status >= 400:
                raise RuntimeError(
                    f"Erreur HTTP : {response.status}"
                )

            # Attendre que les citations générées par JavaScript
            # apparaissent dans la page.
            page.locator(".quote").first.wait_for(
                state="visible",
                timeout=15000,
            )

            elements = page.locator(".quote").all()

            for element in elements:
                texte_element = element.locator(".text")
                auteur_element = element.locator(".author")
                tags_elements = element.locator(".tags .tag").all()

                texte = nettoyer_texte(
                    texte_element.text_content()
                )

                auteur = nettoyer_texte(
                    auteur_element.text_content()
                )

                tags = [
                    nettoyer_texte(tag.text_content())
                    for tag in tags_elements
                ]

                tags = [tag for tag in tags if tag]

                if texte:
                    citations.append({
                        "citation": texte,
                        "auteur": auteur,
                        "tags": tags,
                    })

            print(
                f"Nombre de citations extraites : "
                f"{len(citations)}"
            )

        finally:
            navigateur.close()

    return citations


def exporter_json(citations, chemin):
    """Enregistrer les citations au format JSON."""
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(
            citations,
            fichier,
            ensure_ascii=False,
            indent=4,
        )


def exporter_csv(citations, chemin):
    """Enregistrer les citations au format CSV."""
    champs = ["citation", "auteur", "tags"]

    with open(
        chemin,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        writer = csv.DictWriter(
            fichier,
            fieldnames=champs,
        )

        writer.writeheader()

        for citation in citations:
            ligne = citation.copy()
            ligne["tags"] = ", ".join(ligne["tags"])
            writer.writerow(ligne)


def main():
    DOSSIER_SORTIE.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        citations = scraper_citations()

        chemin_json = DOSSIER_SORTIE / "citations.json"
        chemin_csv = DOSSIER_SORTIE / "citations.csv"

        exporter_json(citations, chemin_json)
        exporter_csv(citations, chemin_csv)

        print("\n" + "=" * 50)
        print(f"Citations extraites : {len(citations)}")
        print(f"JSON : {chemin_json}")
        print(f"CSV  : {chemin_csv}")
        print("=" * 50)

        for numero, citation in enumerate(citations, start=1):
            print(f"\nCitation {numero}")
            print(f"Texte : {citation['citation']}")
            print(f"Auteur : {citation['auteur']}")
            print(f"Tags : {', '.join(citation['tags'])}")

    except PlaywrightTimeoutError as erreur:
        print(
            "Délai dépassé : les citations ne sont pas apparues. "
            f"Détail : {erreur}"
        )

    except Exception as erreur:
        print(f"Erreur pendant le scraping : {erreur}")


if __name__ == "__main__":
    main()
