
import pytest

from app import app
from scraper.first_scraper import scraper_produits


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


def test_scraper_refuse_destination_locale_sans_requete():
    with pytest.raises(ValueError):
        scraper_produits("http://127.0.0.1/")


@pytest.mark.parametrize("max_pages", [0, -1, 11, True, 1.5])
def test_scraper_refuse_limite_pages_invalide(max_pages):
    with pytest.raises(ValueError):
        scraper_produits("http://127.0.0.1/", max_pages=max_pages)


def test_api_scrape_batch(client, monkeypatch):
    monkeypatch.setattr(
        "app.scraper_urls_en_parallele",
        lambda urls: [{"titre": f"Résultat {len(urls)}"}],
    )
    reponse = client.post(
        "/api/scrape-batch",
        json={"urls": ["https://books.example/a", "https://books.example/b"]},
    )
    assert reponse.status_code == 200
    assert reponse.get_json()["count"] == 1


def test_api_scrape_batch_refuse_liste_vide(client):
    reponse = client.post("/api/scrape-batch", json={"urls": []})
    assert reponse.status_code == 400


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


def test_verification_liens_json_non_objet(client):
    reponse = client.post("/api/check-links", json=["https://example.com"])
    assert reponse.status_code == 400
    assert reponse.get_json()["error"]["code"] == "INVALID_JSON"


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
