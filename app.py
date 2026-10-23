
from flask import Flask, jsonify, render_template, request
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

from scraper.first_scraper import scraper_produits, scraper_urls_en_parallele
from broken_links_checker import (
    creer_session,
    effectuer_requete_securisee,
    lire_contenu_limite,
    valider_url,
    verifier_liens_page,
)
from llm_analyzer import (
    LLMError,
    analyser_texte,
    cle_configuree,
)


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


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


@app.post("/api/scrape-batch")
def lancer_scraper_parallele():
    """Scraper en parallèle une liste bornée d'URL indépendantes."""
    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_JSON", "message": "Le corps JSON doit être un objet."},
        }), 400

    urls = donnees.get("urls")
    if not isinstance(urls, list) or not urls:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_URLS", "message": "Fournissez une liste d’URL à scraper."},
        }), 400

    try:
        produits = scraper_urls_en_parallele(urls)
        return jsonify({
            "success": True,
            "count": len(produits),
            "data": produits,
        }), 200
    except ValueError as erreur:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_URLS", "message": str(erreur)},
        }), 400
    except RequestException:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRAPING_REQUEST_ERROR",
                "message": "Une erreur réseau est survenue pendant le scraping.",
            },
        }), 502
    except Exception:
        app.logger.exception("Erreur inattendue pendant le scraping parallèle.")
        return jsonify({
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "Une erreur interne est survenue."},
        }), 500


@app.post("/api/analyze-page")
def analyser_page_avec_ia():
    """Extraire le texte d'une page publique puis l'analyser avec le LLM."""
    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_JSON", "message": "Le corps JSON doit être un objet."},
        }), 400

    url = donnees.get("url")
    if not isinstance(url, str) or not url.strip():
        return jsonify({
            "success": False,
            "error": {"code": "MISSING_URL", "message": "Veuillez saisir l’URL de la page."},
        }), 400

    if not cle_configuree():
        return jsonify({
            "success": False,
            "error": {
                "code": "LLM_NOT_CONFIGURED",
                "message": "Configurez OPENAI_API_KEY ou sélectionnez Ollama local avec LLM_PROVIDER=ollama.",
            },
        }), 503

    try:
        url = valider_url(url)
        with creer_session() as session:
            reponse = effectuer_requete_securisee(session, url)
            try:
                reponse.raise_for_status()
                url_finale = reponse.url
                contenu = lire_contenu_limite(reponse)
            finally:
                reponse.close()

        soup = BeautifulSoup(contenu, "html.parser")
        for element in soup.select("script, style, noscript, template, svg"):
            element.decompose()
        texte = soup.get_text(" ", strip=True)[:12_000]
        if not texte:
            return jsonify({
                "success": False,
                "error": {"code": "EMPTY_PAGE", "message": "La page ne contient pas de texte à analyser."},
            }), 422

        analyse = analyser_texte(texte)
        return jsonify({
            "success": True,
            "url": url_finale,
            "data": analyse,
        }), 200
    except ValueError as erreur:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_URL", "message": str(erreur)},
        }), 400
    except LLMError as erreur:
        return jsonify({
            "success": False,
            "error": {"code": erreur.code, "message": str(erreur)},
        }), erreur.http_status
    except RequestException:
        return jsonify({
            "success": False,
            "error": {
                "code": "PAGE_FETCH_ERROR",
                "message": "Impossible de récupérer la page à analyser.",
            },
        }), 502
    except Exception:
        app.logger.exception("Erreur inattendue pendant l’analyse IA.")
        return jsonify({
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "Une erreur interne est survenue."},
        }), 500


@app.post("/api/analyze-text")
def analyser_texte_avec_ia():
    """Analyser un texte fourni directement, sans téléchargement de page."""
    donnees = request.get_json(silent=True)
    if not isinstance(donnees, dict):
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_JSON", "message": "Le corps JSON doit être un objet."},
        }), 400
    texte = donnees.get("text")
    if not isinstance(texte, str) or not texte.strip():
        return jsonify({
            "success": False,
            "error": {"code": "MISSING_TEXT", "message": "Le champ text est obligatoire."},
        }), 400
    if not cle_configuree():
        return jsonify({
            "success": False,
            "error": {
                "code": "LLM_NOT_CONFIGURED",
                "message": "Configurez OPENAI_API_KEY ou sélectionnez Ollama local avec LLM_PROVIDER=ollama.",
            },
        }), 503
    try:
        analyse = analyser_texte(texte)
        return jsonify({"success": True, "data": analyse}), 200
    except ValueError as erreur:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_TEXT", "message": str(erreur)},
        }), 400
    except LLMError as erreur:
        return jsonify({
            "success": False,
            "error": {"code": erreur.code, "message": str(erreur)},
        }), erreur.http_status


@app.errorhandler(413)
def payload_trop_volumineux(_erreur):
    return jsonify({
        "success": False,
        "error": {"code": "REQUEST_TOO_LARGE", "message": "La requête dépasse la limite autorisée."},
    }), 413


@app.post("/api/check-links")
def lancer_verification_liens():
    """Vérifier les liens d'une page web et renvoyer un rapport JSON."""
    donnees = request.get_json(silent=True) or {}

    if not isinstance(donnees, dict):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_JSON",
                "message": "Le corps JSON doit être un objet.",
            }
        }), 400

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
