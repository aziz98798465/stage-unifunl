
import pytest

from app import app


@pytest.fixture
def client():
    """Crée un client de test Flask sans démarrer le serveur."""
    app.config["TESTING"] = True

    with app.test_client() as client_test:
        yield client_test


# =========================================================
# Tests existants : application principale et API scraper
# =========================================================

def test_page_accueil(client):
    reponse = client.get("/")

    assert reponse.status_code == 200
    assert reponse.content_type.startswith("text/html")


def test_api_health(client):
    reponse = client.get("/api/health")

    assert reponse.status_code == 200

    donnees = reponse.get_json()

    assert donnees["status"] == "ok"


def test_scraping_sans_url(client):
    reponse = client.get("/api/scrape")

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "MISSING_URL"


def test_scraping_url_invalide(client):
    reponse = client.get("/api/scrape?url=adresse-invalide")

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "INVALID_URL"


# =========================================================
# Nouveaux tests : interface du vérificateur de liens
# =========================================================

def test_page_verificateur_liens(client):
    """Vérifie que la page du vérificateur s'affiche."""
    reponse = client.get("/liens")

    assert reponse.status_code == 200
    assert reponse.content_type.startswith("text/html")
    assert b"V\xc3\xa9rificateur de liens cass\xc3\xa9s" in reponse.data


# =========================================================
# Nouveaux tests : validation de l'API du vérificateur
# =========================================================

def test_verification_liens_sans_url(client):
    """L'API doit refuser une requête sans URL."""
    reponse = client.post(
        "/api/check-links",
        json={"max_liens": 10}
    )

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "MISSING_URL"


def test_verification_liens_url_invalide(client):
    """L'API doit refuser une URL invalide."""
    reponse = client.post(
        "/api/check-links",
        json={
            "url": "adresse-invalide",
            "max_liens": 10
        }
    )

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "INVALID_URL"


@pytest.mark.parametrize(
    "max_liens",
    [0, -1, 501, True, 10.5, "10"]
)
def test_verification_liens_nombre_invalide(client, max_liens):
    """L'API doit refuser un nombre de liens hors limites ou mal typé."""
    reponse = client.post(
        "/api/check-links",
        json={
            "url": "https://books.toscrape.com",
            "max_liens": max_liens
        }
    )

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "INVALID_MAX_LINKS"


def test_verification_liens_sans_donnees_json(client):
    """L'API doit traiter proprement une requête sans données JSON."""
    reponse = client.post("/api/check-links")

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "MISSING_URL"


def test_verification_liens_succes(client, monkeypatch):
    """Simule une vérification réussie sans requête Internet."""

    rapport_fictif = {
        "url_analysee": "https://books.toscrape.com",
        "url_finale": "https://books.toscrape.com",
        "nombre_liens_trouves": 1,
        "nombre_liens_verifies": 1,
        "nombre_liens_casses": 0,
        "nombre_erreurs_reseau": 0,
        "resultats": [
            {
                "url": "https://books.toscrape.com",
                "status_code": 200,
                "status": "ok",
                "url_finale": "https://books.toscrape.com",
                "erreur": None
            }
        ]
    }

    def faux_verificateur(url, max_liens=100):
        assert url == "https://books.toscrape.com"
        assert max_liens == 10
        return rapport_fictif

    monkeypatch.setattr(
        "app.verifier_liens_page",
        faux_verificateur
    )

    reponse = client.post(
        "/api/check-links",
        json={
            "url": "https://books.toscrape.com",
            "max_liens": 10
        }
    )

    assert reponse.status_code == 200

    donnees = reponse.get_json()

    assert donnees["success"] is True
    assert donnees["data"]["nombre_liens_verifies"] == 1
    assert donnees["data"]["nombre_liens_casses"] == 0
    assert donnees["data"]["resultats"][0]["status_code"] == 200


def test_verification_liens_erreur_reseau(client, monkeypatch):
    """Vérifie que l'API gère une erreur réseau du vérificateur."""
    import requests

    def faux_verificateur(url, max_liens=100):
        raise requests.ConnectionError("Erreur réseau simulée")

    monkeypatch.setattr(
        "app.verifier_liens_page",
        faux_verificateur
    )

    reponse = client.post(
        "/api/check-links",
        json={
            "url": "https://books.toscrape.com",
            "max_liens": 10
        }
    )

    assert reponse.status_code == 502

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "LINK_CHECK_REQUEST_ERROR"
