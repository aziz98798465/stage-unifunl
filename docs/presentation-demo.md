# Support de démonstration — projet Unifunl

Plan à adapter pour la présentation réelle. Ce document prépare le contenu, mais ne prétend pas que la présentation à l’équipe a eu lieu.

## Diapositive 1 — Objectif

- Deux outils web pédagogiques : extraction de données et vérification de liens.
- Application locale Python/Flask avec interfaces HTML, CSS et JavaScript.

## Diapositive 2 — Scraper statique

- Requests récupère le HTML; BeautifulSoup extrait titre, prix et image.
- Pagination bornée; JSON et CSV.
- Démonstration prévue sur une page de Books to Scrape.

## Diapositive 3 — Pages dynamiques

- Playwright ouvre Quotes to Scrape, attend les éléments rendus et extrait citations, auteurs et tags.
- Requests suffit aux pages statiques; Playwright est utilisé pour le contenu généré par JavaScript.

## Diapositive 4 — API et interface

- `/api/scrape` reçoit une URL.
- `/api/scrape-batch` traite jusqu’à 10 URL indépendantes avec au plus 3 téléchargements simultanés.
- L’interface montre les résultats et permet un export CSV.

## Diapositive 5 — Vérificateur de liens

- `/liens` présente les liens analysés, les statuts et les erreurs.
- Vérification des URL, redirections, limites de requêtes et export CSV.

## Diapositive 6 — Analyse IA optionnelle

- Action volontaire : le texte de page est transmis à OpenAI.
- Le modèle renvoie résumé, catégorie, nom, description et caractéristiques selon un schéma contrôlé.
- Démontrer uniquement après configuration d’une clé autorisée; aucun secret ne doit apparaître à l’écran.

## Diapositive 7 — Qualité, limites et bilan

- Résultats réellement observés à compléter après validation finale.
- Tests hors ligne, limites SSRF/DNS rebinding et dépendances externes.
- Aucun déploiement public effectué; date du stage et bilan personnel à compléter.

## Script de démonstration locale

1. Lancer `python .\app.py` puis ouvrir `http://127.0.0.1:5000`.
2. Lancer le scraper Books to Scrape et télécharger le CSV.
3. Cliquer sur l’analyse IA seulement si une clé API autorisée est configurée; sinon expliquer que l’analyse requiert la configuration du fournisseur.
4. Ouvrir `/liens`, saisir le site de démonstration et analyser une limite de 10 liens.
5. Présenter les tests avec `python -m pytest -v` et l’export généré par l’interface.

La démonstration réseau dépend de l’accès Internet et des règles des sites ciblés.
