
import importlib.util
from pathlib import Path

import pytest


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
    """Un nombre maximal de liens inférieur à 1 est rejeté."""
    with pytest.raises(ValueError):
        checker.verifier_liens_page(
            "https://example.com",
            max_liens=0,
        )
