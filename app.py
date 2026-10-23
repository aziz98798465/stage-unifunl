
from flask import Flask, jsonify, render_template, request
from requests.exceptions import RequestException

from scraper.first_scraper import scraper_produits

app = Flask(__name__)


@app.get("/")
def accueil():
    """Afficher l'interface web."""
    return render_template("index.html")


@app.get("/api/health")
def verifier_sante():
    """Vérifier que l'API fonctionne."""
    return jsonify({
        "status": "ok",
        "message": "L'API fonctionne correctement."
    }), 200


@app.get("/api/scrape")
def lancer_scraper():
    """Lancer le scraper à partir d'une URL fournie."""
    url = request.args.get("url", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_URL",
                "message": "Le paramètre 'url' est obligatoire."
            }
        }), 400

    try:
        produits = scraper_produits(url, max_pages=3)

        return jsonify({
            "success": True,
            "url": url,
            "count": len(produits),
            "data": produits
        }), 200

    except ValueError as erreur:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_URL",
                "message": str(erreur)
            }
        }), 400

    except RequestException:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRAPING_REQUEST_ERROR",
                "message": "Une erreur réseau est survenue pendant le scraping."
            }
        }), 502

    except Exception:
        app.logger.exception("Erreur inattendue pendant le scraping.")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Une erreur interne est survenue."
            }
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

from flask import Flask, jsonify, render_template, request
from requests.exceptions import RequestException

from scraper.first_scraper import scraper_produits

app = Flask(__name__)


@app.get("/")
def accueil():
    """Afficher l'interface web."""
    return render_template("index.html")


@app.get("/api/health")
def verifier_sante():
    """Vérifier que l'API fonctionne."""
    return jsonify({
        "status": "ok",
        "message": "L'API fonctionne correctement."
    }), 200


@app.get("/api/scrape")
def lancer_scraper():
    """Lancer le scraper à partir d'une URL fournie."""
    url = request.args.get("url", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_URL",
                "message": "Le paramètre 'url' est obligatoire."
            }
        }), 400

    try:
        produits = scraper_produits(url, max_pages=3)

        return jsonify({
            "success": True,
            "url": url,
            "count": len(produits),
            "data": produits
        }), 200

    except ValueError as erreur:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_URL",
                "message": str(erreur)
            }
        }), 400

    except RequestException:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRAPING_REQUEST_ERROR",
                "message": "Une erreur réseau est survenue pendant le scraping."
            }
        }), 502

    except Exception:
        app.logger.exception("Erreur inattendue pendant le scraping.")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Une erreur interne est survenue."
            }
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
