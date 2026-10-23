
import pytest

from app import app


@pytest.fixture
def client():
    """Créer un client de test Flask sans démarrer de serveur."""
    app.config["TESTING"] = True

    with app.test_client() as client_test:
        yield client_test


def test_page_accueil(client):
    """Vérifier que la page d'accueil est accessible."""
    reponse = client.get("/")

    assert reponse.status_code == 200
    assert b"Unifunl" in reponse.data


def test_api_health(client):
    """Vérifier l'état de santé de l'API."""
    reponse = client.get("/api/health")

    assert reponse.status_code == 200

    donnees = reponse.get_json()

    assert donnees["status"] == "ok"
    assert "message" in donnees


def test_scraping_sans_url(client):
    """Vérifier qu'une URL manquante renvoie une erreur 400."""
    reponse = client.get("/api/scrape")

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "MISSING_URL"


def test_scraping_url_invalide(client):
    """Vérifier qu'une URL invalide est rejetée."""
    reponse = client.get(
        "/api/scrape",
        query_string={"url": "adresse-invalide"},
    )

    assert reponse.status_code == 400

    donnees = reponse.get_json()

    assert donnees["success"] is False
    assert donnees["error"]["code"] == "INVALID_URL"
