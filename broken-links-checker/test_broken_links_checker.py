
import importlib.util
from pathlib import Path

import pytest
import requests


# Charger le module dont le dossier contient des tirets.
CHEMIN_SCRIPT = (
    Path(__file__).parent / "broken_links_checker.py"
)

spec = importlib.util.spec_from_file_location(
    "broken_links_checker",
    CHEMIN_SCRIPT,
)

checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_valider_url_valide():
    """Une URL HTTPS valide doit être acceptée."""
    url = "https://example.com"

    assert checker.valider_url(url) == url


def test_valider_url_invalide():
    """Une URL sans schéma HTTP(S) doit être rejetée."""
    with pytest.raises(ValueError):
        checker.valider_url("adresse-invalide")


def test_extraire_liens_relatifs_et_absolus():
    """Les liens relatifs doivent devenir des URL absolues."""
    html = """
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="#section">Section</a>
            <a href="/page1">Page 1 en double</a>
            <a href="mailto:test@example.com">Email</a>
        </body>
    </html>
    """

    liens = checker.extraire_liens(
        html,
        "https://example.com",
    )

    assert "https://example.com/page1" in liens
    assert "https://example.com/page2" in liens
    assert "https://example.com" in liens
    assert "mailto:test@example.com" not in liens
    assert len(liens) == 3


def test_verifier_lien_sans_requete_reseau():
    """Simuler une réponse HTTP 200 sans accéder à Internet."""

    class FausseReponse:
        status_code = 200
        ok = True
        url = "https://example.com/page"

        def close(self):
            pass

    class FausseSession:
        def get(self, *args, **kwargs):
            return FausseReponse()

    resultat = checker.verifier_lien(
        FausseSession(),
        "https://example.com/page",
    )

    assert resultat["status"] == "ok"
    assert resultat["status_code"] == 200
    assert resultat["erreur"] is None


def test_verifier_lien_erreur_reseau():
    """Vérifier la gestion d'une erreur réseau simulée."""
    import requests

    class FausseSession:
        def get(self, *args, **kwargs):
            raise requests.ConnectionError(
                "Connexion simulée impossible"
            )

    resultat = checker.verifier_lien(
        FausseSession(),
        "https://example.com/page",
    )

    assert resultat["status"] == "error"
    assert resultat["status_code"] is None
    assert "Connexion simulée impossible" in resultat["erreur"]


def test_max_liens_invalide():
    """Les limites hors plage sont rejetées avant toute requête réseau."""
    for nombre in (0, 501):
        with pytest.raises(ValueError):
            checker.verifier_liens_page(
                "https://example.com",
                max_liens=nombre,
            )


def test_session_borne_delai_retry_after():
    session = checker.creer_session()
    try:
        assert session.get_adapter("https://example.com").max_retries.retry_after_max == 5
    finally:
        session.close()


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://[::1]/",
        "file:///etc/passwd",
        "http://user:password@example.com/",
        "https://example.com/\nheader",
    ],
)
def test_valider_url_refuse_destinations_et_schemas_dangereux(url):
    with pytest.raises(ValueError):
        checker.valider_url(url)


def test_redirection_vers_adresse_locale_bloquee_avant_requete(monkeypatch):
    """La destination privée ne doit jamais être transmise à la session."""
    import socket

    monkeypatch.setattr(
        checker.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    class Redirection:
        status_code = 302
        url = "https://example.com/start"
        headers = {"Location": "http://127.0.0.1/admin"}

        def close(self):
            pass

    class FausseSession:
        def __init__(self):
            self.urls_contactees = []

        def get(self, url, **kwargs):
            self.urls_contactees.append(url)
            return Redirection()

    session = FausseSession()
    with pytest.raises(requests.RequestException):
        checker.effectuer_requete_securisee(session, "https://example.com/start")

    assert session.urls_contactees == ["https://example.com/start"]


def test_lire_contenu_refuse_depassement_de_taille():
    class FausseReponse:
        headers = {}

        def iter_content(self, chunk_size):
            yield b"1234"

    with pytest.raises(requests.RequestException, match="dépasse"):
        checker.lire_contenu_limite(FausseReponse(), limite=3)


def test_export_csv_neutralise_les_formules(tmp_path):
    chemin = tmp_path / "rapport.csv"
    checker.exporter_csv({
        "resultats": [{
            "url": "=HYPERLINK(\"https://malicious.example\")",
            "status_code": 200,
            "status": "ok",
            "url_finale": "+cmd",
            "erreur": None,
        }]
    }, chemin)

    contenu = chemin.read_text(encoding="utf-8-sig")
    assert "'=HYPERLINK" in contenu
    assert "'+cmd" in contenu
