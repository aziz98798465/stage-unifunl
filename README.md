# Stage d'immersion — Unifunl

## 1. Présentation du projet

Ce projet a été réalisé dans le cadre du stage d'immersion chez Unifunl. Il consiste à développer de petits outils web permettant de récupérer des données depuis des pages web, de les structurer et de vérifier les liens d'un site.

Le projet utilise Python pour le scraping et le développement de l'API, ainsi que HTML, CSS et JavaScript pour l'interface web.

## 2. Objectifs

- Découvrir les techniques de web scraping.
- Extraire et nettoyer des données depuis des pages web.
- Exporter les données aux formats JSON et CSV.
- Développer une API avec Flask.
- Créer une interface web pour afficher les résultats.
- Utiliser Playwright pour extraire des données de pages dynamiques.
- Développer un outil de vérification des liens cassés.
- Écrire et exécuter des tests automatisés.
- Améliorer les performances du scraper.

## 3. Technologies utilisées

- **Python** : langage principal.
- **Requests** : requêtes HTTP.
- **BeautifulSoup** : analyse du HTML.
- **Playwright** : navigation et scraping de pages dynamiques.
- **Flask** : création de l'API web.
- **HTML, CSS et JavaScript** : interface utilisateur.
- **pytest** : tests automatisés.
- **Git** : gestion des versions.
- **CSV et JSON** : stockage des données extraites.

## 4. Structure du projet

```text
stage-unifunl/
├── app.py
├── requirements.txt
├── test_app.py
├── scraper/
│   ├── first_scraper.py
│   ├── playwright_scraper.py
│   └── output/
│       ├── produits.csv
│       ├── produits.json
│       ├── citations.csv
│       └── citations.json
├── broken-links-checker/
│   ├── broken_links_checker.py
│   ├── test_broken_links_checker.py
│   └── output/
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── docs/
├── .gitignore
└── README.md
```

## 5. Prérequis

- Python installé.
- Git installé.
- Visual Studio Code ou un éditeur équivalent.
- Une connexion Internet pour les opérations de scraping.
- Node.js installé pour l'environnement général du projet, si nécessaire.

## 6. Installation

Ouvrir un terminal PowerShell à la racine du projet.

Créer l'environnement virtuel :

```powershell
python -m venv .venv
```

Activer l'environnement :

```powershell
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
python -m pip install -r requirements.txt
```

Si PowerShell bloque l'activation de l'environnement, consulter la documentation de Python ou utiliser directement l'interpréteur situé dans `.venv\Scripts\python.exe`.

## 7. Lancer le scraper

Depuis la racine du projet :

```powershell
python .\scraper\first_scraper.py
```

Le scraper récupère les données des livres du site de démonstration Books to Scrape. La configuration actuelle traite jusqu'à trois pages.

Les résultats sont enregistrés dans :

- `scraper/output/produits.json`
- `scraper/output/produits.csv`

Les données comprennent le titre, le prix, la devise et l'URL de l'image.

## 8. Scraping avec Playwright

Le second scraper permet de tester l'extraction de données depuis une page qui utilise JavaScript.

```powershell
python .\scraper\playwright_scraper.py
```

Les résultats sont enregistrés au format JSON et CSV dans `scraper/output/`.

## 9. Lancer l'API et l'interface web

Démarrer l'application Flask :

```powershell
python .\app.py
```

Ouvrir ensuite l'adresse suivante dans le navigateur :

http://127.0.0.1:5000

### Endpoints disponibles

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Afficher l'interface web |
| GET | `/api/health` | Vérifier l'état de l'API |
| GET | `/api/scrape?url=URL` | Lancer le scraping d'une URL compatible |

Exemple d'URL pour l'API :

```text
http://127.0.0.1:5000/api/scrape?url=https%3A%2F%2Fbooks.toscrape.com%2Fcatalogue%2Fcategory%2Fbooks_1%2Findex.html
```

L'API renvoie des données au format JSON. Elle gère notamment les URL manquantes ou invalides et les erreurs de requête.

**Important :** le scraper actuel utilise des sélecteurs adaptés à Books to Scrape. Il ne peut pas nécessairement extraire correctement les données d'un site quelconque.

## 10. Vérificateur de liens cassés

Exemple d'exécution :

```powershell
python .\broken-links-checker\broken_links_checker.py https://books.toscrape.com --max-liens 10
```

Le paramètre `--max-liens` permet de limiter le nombre de liens vérifiés.

Les rapports sont générés dans le dossier `broken-links-checker/output/`.

## 11. Tests automatisés

Depuis la racine du projet :

```powershell
python -m pytest -v
```

Les tests vérifient notamment les endpoints de l'API, la validation des URL et plusieurs fonctionnalités du vérificateur de liens.

Dernier résultat observé pendant le développement : **10 tests réussis**. Le résultat doit être confirmé après toute modification du code.

## 12. Optimisation

Le scraper a été amélioré afin de conserver le contenu HTML des pages déjà téléchargées et d'éviter les téléchargements en double.

Lors du dernier essai, 60 produits ont été récupérés sur trois pages. Une mesure de temps d'exécution complète a donné environ 3,10 secondes. Cette durée dépend notamment des conditions du réseau.

## 13. Limites et améliorations possibles

- Ajouter une interface web dédiée au vérificateur de liens.
- Tester le scraper sur plusieurs sites autorisés.
- Intégrer une API de modèle de langage (LLM), si les accès nécessaires sont disponibles.
- Ajouter des mécanismes de limitation des appels et de protection des clés API.
- Compléter les tests et la documentation.
- Déployer les outils sur un serveur de test.

## 14. Bonnes pratiques

- Respecter les conditions d'utilisation et les règles d'accès des sites consultés.
- Ne pas publier de clés API ou de données sensibles.
- Conserver les dépendances dans `requirements.txt`.
- Exécuter les tests avant de valider les modifications.
- Utiliser Git pour conserver l'historique du projet.

## 15. Statut du document

Ce README décrit l'état du projet au moment de sa rédaction. Les fonctionnalités non encore réalisées doivent être indiquées comme telles dans le rapport final du stage.
