
import argparse
import csv
import ipaddress
import json
import socket
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


TIMEOUT = 10
DELAI_ENTRE_REQUETES = 0.3
MAX_LIENS = 100
MAX_REDIRECTIONS = 10
MAX_TAILLE_PAGE = 2 * 1024 * 1024

DOSSIER_SORTIE = Path(__file__).parent / "output"


def valider_url(url):
    """Valider une URL HTTP(S) et bloquer les destinations non publiques."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("L'URL est obligatoire.")

    url = url.strip()

    if any(ord(caractere) < 32 for caractere in url):
        raise ValueError("L'URL contient des caractères de contrôle.")

    try:
        parties = urlparse(url)
    except ValueError as erreur:
        raise ValueError("L'URL est mal formée.") from erreur

    if parties.scheme.lower() not in ("http", "https") or not parties.hostname:
        raise ValueError("L'URL doit commencer par http:// ou https://.")

    if parties.username or parties.password:
        raise ValueError("Les URL contenant des identifiants sont interdites.")

    try:
        port = parties.port
    except ValueError as erreur:
        raise ValueError("Le port de l'URL est invalide.") from erreur

    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Le port doit être compris entre 1 et 65535.")

    hote = parties.hostname.lower().rstrip(".")

    if hote == "localhost" or hote.endswith(".localhost"):
        raise ValueError("Les adresses locales ne sont pas autorisées.")

    try:
        ip = ipaddress.ip_address(hote)
    except ValueError:
        ip = None

    if ip is not None:
        if not ip.is_global:
            raise ValueError(
                "Les adresses IP privées, locales ou réservées sont interdites."
            )
    else:
        try:
            adresses = socket.getaddrinfo(
                hote,
                port or (443 if parties.scheme.lower() == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError as erreur:
            raise ValueError(
                "Le nom de domaine ne peut pas être résolu."
            ) from erreur

        if not adresses:
            raise ValueError(
                "Le nom de domaine ne possède aucune adresse IP valide."
            )

        for adresse in adresses:
            ip_resolue = ipaddress.ip_address(adresse[4][0])

            if not ip_resolue.is_global:
                raise ValueError(
                    "Le domaine pointe vers une adresse IP privée, "
                    "locale ou réservée."
                )

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
        retry_after_max=5,
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

        if parties.scheme.lower() in ("http", "https") and parties.hostname:
            # Supprimer les fragments (#section) pour éviter les doublons.
            url_sans_fragment = parties._replace(fragment="").geturl()
            liens.add(url_sans_fragment)

    return sorted(liens)


def effectuer_requete_securisee(
    session,
    url,
    max_redirections=MAX_REDIRECTIONS,
    timeout=TIMEOUT,
):
    """Effectuer une requête en validant chaque destination de redirection."""
    url_courante = valider_url(url)
    historique = set()

    for _ in range(max_redirections + 1):
        if url_courante in historique:
            raise requests.RequestException(
                "Une boucle de redirection a été détectée."
            )

        historique.add(url_courante)

        reponse = session.get(
            url_courante,
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )

        if reponse.status_code not in (301, 302, 303, 307, 308):
            return reponse

        emplacement = reponse.headers.get("Location")
        url_precedente = reponse.url
        reponse.close()

        if not emplacement:
            raise requests.RequestException(
                "Redirection reçue sans en-tête Location."
            )

        url_suivante = urljoin(url_precedente, emplacement)

        try:
            url_courante = valider_url(url_suivante)
        except ValueError as erreur:
            raise requests.RequestException(
                f"Redirection bloquée pour des raisons de sécurité : {erreur}"
            ) from erreur

    raise requests.RequestException(
        f"Nombre maximal de redirections dépassé ({max_redirections})."
    )


def lire_contenu_limite(reponse, limite=MAX_TAILLE_PAGE):
    """Lire une réponse sans dépasser la taille maximale autorisée."""
    longueur = reponse.headers.get("Content-Length")
    if longueur:
        try:
            if int(longueur) > limite:
                raise requests.RequestException(
                    f"La réponse dépasse la limite de {limite} octets."
                )
        except ValueError:
            pass

    contenu = bytearray()
    for morceau in reponse.iter_content(chunk_size=65536):
        contenu.extend(morceau)
        if len(contenu) > limite:
            raise requests.RequestException(
                f"La réponse dépasse la limite de {limite} octets."
            )
    return bytes(contenu)


def verifier_lien(session, url):
    """Tester un lien et retourner son statut."""
    try:
        reponse = effectuer_requete_securisee(session, url)

        try:
            return {
                "url": url,
                "status_code": reponse.status_code,
                "status": "ok" if reponse.ok else "broken",
                "url_finale": reponse.url,
                "erreur": None,
            }
        finally:
            reponse.close()

    except (requests.RequestException, ValueError) as erreur:
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

    if (
        not isinstance(max_liens, int)
        or isinstance(max_liens, bool)
        or max_liens < 1
        or max_liens > 500
    ):
        raise ValueError("max_liens doit être compris entre 1 et 500.")

    with creer_session() as session:
        reponse = effectuer_requete_securisee(session, url)

        try:
            reponse.raise_for_status()
            url_finale = reponse.url
            contenu = lire_contenu_limite(reponse)
            liens = extraire_liens(contenu, url_finale)
        finally:
            reponse.close()

        liens_a_verifier = liens[:max_liens]
        resultats = []

        for numero, lien in enumerate(liens_a_verifier, start=1):
            print(
                f"[{numero}/{len(liens_a_verifier)}] "
                f"Vérification : {lien}"
            )

            resultats.append(verifier_lien(session, lien))

            if numero < len(liens_a_verifier):
                time.sleep(DELAI_ENTRE_REQUETES)

    return {
        "url_analysee": url,
        "url_finale": url_finale,
        "nombre_liens_trouves": len(liens),
        "nombre_liens_verifies": len(resultats),
        "nombre_liens_casses": sum(
            resultat["status"] == "broken"
            for resultat in resultats
        ),
        "nombre_erreurs_reseau": sum(
            resultat["status"] == "error"
            for resultat in resultats
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
        writer = csv.DictWriter(
            fichier,
            fieldnames=champs,
            delimiter=";",
        )
        writer.writeheader()
        for resultat in rapport["resultats"]:
            ligne = resultat.copy()
            for champ in champs:
                valeur = ligne.get(champ)
                if isinstance(valeur, str) and valeur.lstrip().startswith(
                    ("=", "+", "-", "@", "\t", "\r")
                ):
                    ligne[champ] = "'" + valeur
            writer.writerow(ligne)


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
