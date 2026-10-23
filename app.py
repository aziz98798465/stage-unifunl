
from flask import Flask, jsonify, render_template, request
from requests.exceptions import RequestException

from scraper.first_scraper import scraper_produits
from broken_links_checker import verifier_liens_page


app = Flask(__name__)


@app.get("/")
def accueil():
    """Afficher l'interface du scraper."""
    return render_template("index.html")


@app.get("/liens")
def interface_verificateur():
    """Afficher l'interface du vérificateur de liens."""
    return render_template("broken_links.html")


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
                "message": (
                    "Une erreur réseau est survenue pendant le scraping."
                )
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


@app.post("/api/check-links")
def lancer_verification_liens():
    """Vérifier les liens d'une page web et renvoyer un rapport JSON."""
    donnees = request.get_json(silent=True) or {}

    url = donnees.get("url", "")
    max_liens = donnees.get("max_liens", 100)

    if not isinstance(url, str) or not url.strip():
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_URL",
                "message": "Veuillez saisir l'URL du site à analyser."
            }
        }), 400

    if (
        not isinstance(max_liens, int)
        or isinstance(max_liens, bool)
        or max_liens < 1
        or max_liens > 500
    ):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_MAX_LINKS",
                "message": (
                    "Le nombre de liens doit être compris entre 1 et 500."
                )
            }
        }), 400

    try:
        rapport = verifier_liens_page(
            url.strip(),
            max_liens=max_liens
        )

        return jsonify({
            "success": True,
            "data": rapport
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
                "code": "LINK_CHECK_REQUEST_ERROR",
                "message": (
                    "Impossible de récupérer la page à analyser."
                )
            }
        }), 502

    except Exception:
        app.logger.exception(
            "Erreur inattendue pendant la vérification des liens."
        )
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Une erreur interne est survenue."
            }
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
