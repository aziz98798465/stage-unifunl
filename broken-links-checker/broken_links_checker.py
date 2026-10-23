
import argparse
import csv
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


TIMEOUT = 10
DELAI_ENTRE_REQUETES = 0.3
MAX_LIENS = 100

DOSSIER_SORTIE = Path(__file__).parent / "output"


def valider_url(url):
    """Vérifier qu'une URL est une adresse HTTP ou HTTPS valide."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("L'URL est obligatoire.")

    url = url.strip()
    parties = urlparse(url)

    if parties.scheme not in ("http", "https") or not parties.hostname:
        raise ValueError("L'URL doit commencer par http:// ou https://.")

    return url


def creer_session():
    """Créer une session HTTP avec une gestion des erreurs temporaires."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "UnifunlBrokenLinksChecker/1.0"
    })

    strategie = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adaptateur = HTTPAdapter(max_retries=strategie)
    session.mount("http://", adaptateur)
    session.mount("https://", adaptateur)

    return session


def extraire_liens(html, url_base):
    """Extraire les liens HTTP(S) uniques d'une page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    liens = set()

    for element in soup.select("a[href]"):
        href = element.get("href", "").strip()

        if not href:
            continue

        url_complete = urljoin(url_base, href)
        parties = urlparse(url_complete)

        if parties.scheme in ("http", "https") and parties.hostname:
            # Supprimer les fragments (#section) pour éviter les doublons.
            url_sans_fragment = parties._replace(fragment="").geturl()
            liens.add(url_sans_fragment)

    return sorted(liens)


def verifier_lien(session, url):
    """Tester un lien et retourner son statut."""
    try:
        # GET est utilisé pour éviter les faux résultats liés à HEAD.
        reponse = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True,
        )

        resultat = {
            "url": url,
            "status_code": reponse.status_code,
            "status": "ok" if reponse.ok else "broken",
            "url_finale": reponse.url,
            "erreur": None,
        }

        reponse.close()
        return resultat

    except requests.RequestException as erreur:
        return {
            "url": url,
            "status_code": None,
            "status": "error",
            "url_finale": None,
            "erreur": str(erreur),
        }


def verifier_liens_page(url, max_liens=MAX_LIENS):
    """Télécharger une page et vérifier ses liens."""
    url = valider_url(url)

    if not isinstance(max_liens, int) or isinstance(max_liens, bool) or max_liens < 1:
        raise ValueError("max_liens doit être un entier positif.")

    with creer_session() as session:
        reponse = session.get(url, timeout=TIMEOUT)
        reponse.raise_for_status()

        url_finale = reponse.url
        liens = extraire_liens(reponse.text, url_finale)

        liens_a_verifier = liens[:max_liens]
        resultats = []

        for numero, lien in enumerate(liens_a_verifier, start=1):
            print(f"[{numero}/{len(liens_a_verifier)}] Vérification : {lien}")

            resultats.append(verifier_lien(session, lien))

            if numero < len(liens_a_verifier):
                time.sleep(DELAI_ENTRE_REQUETES)

    return {
        "url_analysee": url,
        "url_finale": url_finale,
        "nombre_liens_trouves": len(liens),
        "nombre_liens_verifies": len(resultats),
        "nombre_liens_casses": sum(
            resultat["status"] == "broken" for resultat in resultats
        ),
        "nombre_erreurs_reseau": sum(
            resultat["status"] == "error" for resultat in resultats
        ),
        "resultats": resultats,
    }


def exporter_json(rapport, chemin):
    """Enregistrer le rapport en JSON."""
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(rapport, fichier, ensure_ascii=False, indent=4)


def exporter_csv(rapport, chemin):
    """Enregistrer les résultats détaillés en CSV."""
    champs = [
        "url",
        "status_code",
        "status",
        "url_finale",
        "erreur",
    ]

    with open(chemin, "w", newline="", encoding="utf-8-sig") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs)
        writer.writeheader()
        writer.writerows(rapport["resultats"])


def main():
    parser = argparse.ArgumentParser(
        description="Vérifier les liens cassés d'une page web."
    )

    parser.add_argument(
        "url",
        help="URL HTTP(S) de la page à analyser",
    )

    parser.add_argument(
        "--max-liens",
        type=int,
        default=MAX_LIENS,
        help=f"Nombre maximal de liens à vérifier (défaut : {MAX_LIENS})",
    )

    arguments = parser.parse_args()

    try:
        rapport = verifier_liens_page(
            arguments.url,
            max_liens=arguments.max_liens,
        )

        DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

        chemin_json = DOSSIER_SORTIE / "rapport_liens.json"
        chemin_csv = DOSSIER_SORTIE / "rapport_liens.csv"

        exporter_json(rapport, chemin_json)
        exporter_csv(rapport, chemin_csv)

        print("\n===== RAPPORT =====")
        print(f"URL analysée : {rapport['url_analysee']}")
        print(f"Liens trouvés : {rapport['nombre_liens_trouves']}")
        print(f"Liens vérifiés : {rapport['nombre_liens_verifies']}")
        print(f"Liens cassés : {rapport['nombre_liens_casses']}")
        print(f"Erreurs réseau : {rapport['nombre_erreurs_reseau']}")
        print(f"Rapport JSON : {chemin_json}")
        print(f"Rapport CSV : {chemin_csv}")

    except (ValueError, requests.RequestException, OSError) as erreur:
        print(f"Erreur : {erreur}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
