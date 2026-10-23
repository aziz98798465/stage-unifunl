# Vérification de la liste de tâches du stage

Ce document rapproche la liste de 30 tâches envoyée par l’encadrant (`taches_stage_a_verifier-1.docx`) des preuves visibles dans le dépôt et des vérifications de la livraison. Il ne remplit pas le DOCX et ne valide pas les événements personnels du stage. Pour ces lignes, la personne qui a effectué le stage doit confirmer la vérité avant de cocher.

## Tâches 1 à 15

| N° | Tâche de l’encadrant | État selon le dépôt | Correction / vérification nécessaire |
|---:|---|---|---|
| 1 | Accueil dans l'équipe ; présentation du petit projet web annexe ; installation de l'environnement de développement (Python, Node.js, Git). | À vérifier personnellement. | Python et Git sont présents; le projet ne nécessite pas Node.js. Confirmer l’accueil et l’installation réellement effectués. |
| 2 | Compréhension du besoin : développer de petits outils web internes ; définition du périmètre et des fonctionnalités avec le tuteur. | À vérifier personnellement. | Le dépôt contient deux outils web. Il ne prouve pas les échanges ou l’accord du tuteur. |
| 3 | Révision des bases HTML/CSS/JavaScript et des requêtes HTTP ; étude de la structure de pages web à analyser. | À modifier selon le travail réel. | Les technologies sont utilisées dans le projet; le dépôt ne prouve pas les séances de révision. |
| 4 | Prise en main de Git : création du dépôt, branches et commits du projet. | Partiel. | Le dépôt Git contient des commits, mais seule la branche `master` est visible. Confirmer qui a créé le dépôt et si d’autres branches ont été utilisées; ajuster l’intitulé si nécessaire. |
| 5 | Étude des techniques de web scraping (requests, BeautifulSoup) et de leurs limites (pages dynamiques, robots.txt). | Partiel. | Requests et BeautifulSoup sont utilisés; Playwright couvre une page dynamique. Le dépôt ne montre pas de vérification de `robots.txt` ni de compte rendu d’étude. |
| 6 | Premier script de scraping : récupération du titre, du prix et des images d'une page produit. | Oui, côté projet. | Extraction Books to Scrape vérifiée : 20 produits sur une page lors d’un essai réseau limité. |
| 7 | Nettoyage et structuration des données extraites (JSON/CSV) ; gestion des champs manquants. | Oui, côté projet. | Modèles JSON/CSV présents; nettoyage et champs manquants couverts dans le code et tests. |
| 8 | Gestion de la pagination et de plusieurs pages ; ajout de délais entre requêtes et gestion des erreurs. | Oui, implémenté; partiellement vérifié en réseau. | La pagination et les délais existent; le parcours multi-page est testé hors ligne. L’essai réseau de cette livraison s’est limité à une page. |
| 9 | Scraping de pages dynamiques avec Playwright ; comparaison avec la méthode précédente. | Partiel. | Playwright a extrait 10 citations de Quotes to Scrape. Si aucune comparaison écrite Requests/Playwright n’a été faite, remplacer par « scraping d’une page dynamique avec Playwright ». |
| 10 | Tests du scraper sur plusieurs sites ; correction de bugs et amélioration de la robustesse. | Partiel. | Les deux scripts utilisent des sites de démonstration distincts et ont été exécutés. Les tests ne démontrent pas plusieurs sites statiques ni plusieurs structures de produits. Ajuster selon les essais réellement réalisés pendant le stage. |
| 11 | Création d'une petite API (Flask/FastAPI) exposant le scraper : endpoint recevant une URL en entrée. | Oui, côté projet. | Flask expose `/api/scrape` avec URL en entrée. |
| 12 | Validation des entrées, gestion des erreurs et réponses JSON structurées de l'API. | Oui, côté projet. | Validations et erreurs JSON sont couvertes par les tests. |
| 13 | Développement d'une interface web simple (HTML/CSS/JS) pour saisir une URL et afficher les résultats. | Oui, côté projet. | L’interface scraper permet la saisie et l’affichage; une seconde interface sert au vérificateur. |
| 14 | Ajout de l'export des résultats en CSV/Excel depuis l'interface. | À modifier. | L’interface exporte en CSV, lisible par Excel; aucun fichier XLSX natif n’est généré. Écrire « export CSV compatible avec Excel » si cela correspond à l’action réelle. |
| 15 | Revue de code avec le tuteur ; refactorisation et ajout de commentaires. | À vérifier personnellement. | Le code a été modifié et commenté, mais le dépôt ne prouve pas une revue du tuteur. Ne cocher oui que si elle a eu lieu. |

## Tâches 16 à 30

| N° | Tâche de l’encadrant | État selon le dépôt | Correction / vérification nécessaire |
|---:|---|---|---|
| 16 | Découverte des API d'IA (LLM) : tests de prompts pour extraire des informations d'un texte. | Implémentation et tests hors ligne réalisés; découverte personnelle à confirmer. | Le prompt, le schéma et les tests sont dans `llm_analyzer.py` et `test_llm_analyzer.py`. Deux fournisseurs sont pris en charge : OpenAI ou Ollama local. |
| 17 | Intégration d'une API LLM pour résumer et catégoriser le contenu des pages récupérées. | Intégration réalisée; fonctionnement local confirmé par l'utilisateur. | `POST /api/analyze-page` et le bouton d'analyse sont présents. L'utilisateur indique que l'analyse Ollama locale fonctionne. OpenAI n'a pas de clé configurée. |
| 18 | Extraction de données structurées (nom, description, caractéristiques) à partir de texte brut via un prompt dédié. | Implémenté et testé avec mock. | Le schéma de sortie strict comprend `name`, `description`, `features`, `summary` et `category`; `POST /api/analyze-text` accepte le texte brut. |
| 19 | Évaluation de la qualité des réponses de l'IA sur un échantillon de pages ; ajustement des prompts. | Cadre d’évaluation préparé; mesure réelle non exécutée. | Trois exemples de référence et métriques catégorie/nom/couverture sont dans `llm_eval_samples.json`, `llm_eval.py` et `scripts/evaluer_llm.py`. L’exécution réelle coûte des appels et exige une clé; le prompt n’a donc pas été évalué par le modèle. |
| 20 | Gestion de la clé API et limitation du nombre d'appels pour maîtriser le coût. | Gestion implémentée pour OpenAI; Ollama local évite la clé et la facturation API. | La clé OpenAI est lue depuis l’environnement et `.env` est ignoré. OpenAI est limité à 5 appels par heure; le quota se réinitialise au redémarrage. Le mode Ollama n'utilise pas ce quota cloud. |
| 21 | Développement d'un second petit outil : vérificateur de liens cassés d'un site web. | Oui, côté projet. | Module CLI, API Flask et tests présents. |
| 22 | Interface du second outil et affichage du rapport des liens cassés. | Oui, côté projet. | Interface `/liens` testée dans Chromium avec une réponse API simulée. |
| 23 | Amélioration de l'interface : affichage adapté au mobile et messages d'erreur clairs. | Oui, côté projet. | Les deux pages ont été vérifiées à 390 px et 1280 px sans débordement; messages d’erreur présents. |
| 24 | Écriture de tests simples (pytest) pour le scraper et l'API. | Oui, côté projet. | Suite exécutée : 64 tests réussis, 0 échec. |
| 25 | Optimisation : exécution de requêtes en parallèle pour accélérer le scraping. | Implémenté pour les URL indépendantes; pagination suivie reste séquentielle. | `POST /api/scrape-batch` et `scraper_urls_en_parallele` chargent 1 à 10 URL connues avec au plus 3 workers et restaurent l’ordre d’entrée. Tests simulés et essai réseau réel sur 3 pages de Books to Scrape : 60 produits récupérés. |
| 26 | Correction des bugs remontés par l'équipe lors des essais des outils. | À vérifier personnellement. | Les corrections et tests de cette finalisation sont visibles; aucun rapport d’essai ou retour de l’équipe n’est fourni. |
| 27 | Mise en ligne des outils sur un petit serveur de test. | Non réalisé; publication externe laissée en attente d’autorisation et d’un hébergeur. | L’application démarre localement sur `127.0.0.1`. Aucun compte ou hébergeur n’est configuré. Render est proposé pour une démonstration; aucun déploiement ni publication n’a eu lieu. |
| 28 | Rédaction de la documentation : README, installation et utilisation. | Oui, côté projet. | README complet, rapport technique et checklist présents. |
| 29 | Préparation de la démonstration des outils et de la présentation des résultats. | Préparé en local; présentation réelle à confirmer. | Procédure et plan de diaporama sont dans `docs/presentation-demo.md`. Confirmer si la présentation formelle a eu lieu. |
| 30 | Présentation des outils à l'équipe ; bilan du stage et rédaction du rapport de stage. | Trame préparée; reste à compléter et à confirmer personnellement. | `docs/rapport-de-stage-a-completer.md` est une trame, pas un rapport final. Confirmer la présentation, remplir les dates réelles et écrire le bilan personnel. |

## Dates et règle de remplissage

La période réelle du stage n’est pas déductible du dépôt. Les dates des commits Git ne sont pas des dates fiables de début et de fin de stage. Inscrire les dates réelles à partir des documents de stage ou des informations confirmées par l’encadrant.

Les statuts « oui » ci-dessus décrivent uniquement des éléments prouvés dans le projet. Pour les activités, échanges et présentations, confirmer avec son propre journal. Les tâches LLM sont intégrées; le modèle Ollama n'est pas encore installe et l'appel OpenAI réel n'a pas ete teste.
