# Rapport technique et etat de finalisation

Version PDF : [rapport technique du projet](rapport-technique-stage-unifunl.pdf). Le fichier source HTML est `rapport-technique.html` et peut etre regenere avec `python .\scripts\generer_rapport_technique_pdf.py`.

Mis a jour le 24 octobre 2026. La liste des 30 taches de l'encadrant est suivie dans [verification-taches-stage.md](verification-taches-stage.md). Ce rapport separe les preuves du projet des faits personnels a confirmer.

## Resultats verifies

- Environnement : Python 3.13.14 dans `.venv`; `pip check` ne signale aucune dependance incoherente.
- Tests : **64 reussis, 0 echec** avec `.venv\Scripts\python.exe -m pytest -q`.
- Compilation : `compileall` termine sans erreur pour Flask, scrapers, verificateurs et scripts.
- L'application a demarre localement et repondu HTTP 200 sur `/`, `/liens` et `/api/health`. Chromium a verifie les interfaces a 390 px et 1280 px; les appels des formulaires etaient simules.
- Essais reseau : Books to Scrape a fourni 20 produits sur une page lors d'un essai precedent. Le scraper parallele a recupere 60 produits depuis 3 pages independantes. Playwright a extrait 10 citations de Quotes to Scrape. Les sorties n'ont pas ete exportees.
- OpenAI est le fournisseur par defaut; Ollama local est aussi integre. L'utilisateur confirme que le modele local fonctionne sur son PC. Les tests automatises utilisent des mocks; aucune cle API OpenAI n'est configuree et aucun appel cloud n'a ete effectue.

## Travaux realises

- Renforcement du scraper et du verificateur de liens : validation HTTP(S), controle des redirections, limites de taille, erreurs structurees et protection des exports CSV contre les formules.
- Scraping parallele d'URL independantes, avec un maximum de trois requetes simultanees. La pagination reste sequentielle car chaque page suivante est decouverte a partir de la precedente.
- Analyse LLM facultative par OpenAI Responses API ou Ollama sur `127.0.0.1:11434`, avec sortie structuree et declenchement explicite. Les routes acceptent l'URL d'une page ou du texte brut.
- Le quota local de cinq appels par heure ne s'applique qu'a OpenAI; les appels OpenAI ont un timeout de 20 secondes et Ollama local un timeout de lecture de 180 secondes.
- Tests simules, trois exemples de reference et outil de notation facultatif. `scripts/evaluer_llm.py` effectue trois appels au fournisseur configure; ceux d'OpenAI peuvent etre facturables.
- Documentation du lancement local, demonstration et rapprochement des 30 taches. Une trame de rapport et un plan de presentation sont dans `docs/`.

## Lancement local

```powershell
cd C:\Users\pc\Documents\stage-unifunl
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m compileall -q app.py scraper broken_links_checker broken-links-checker scripts
python -m pytest -v
python .\app.py
```

Ouvrir `http://127.0.0.1:5000` pour le scraper et `/liens` pour le verificateur. OpenAI demande une cle. Le mode local Ollama requiert l'installation et le telechargement du modele; suivre la section correspondante du README.

## Hebergement

Aucun compte ni fournisseur n'est configure et aucun deploiement n'a eu lieu. Render est une option a evaluer pour un serveur de demonstration : commande de build `pip install -r requirements.txt`, commande de demarrage `gunicorn app:app`. Verifier les limites et tarifs de l'offre. Un plan gratuit peut suspendre le service et son disque n'est pas persistant. Configurer les secrets dans le tableau de bord et tenir compte du risque SSRF/DNS rebinding avant toute exposition publique.

## Limites et informations a completer

- L'analyse OpenAI reelle demande une cle et peut etre facturable. L'utilisateur confirme que le mode Ollama local fonctionne; l'evaluation de qualite sur les trois exemples reste a lancer.
- Le quota de cinq appels par heure est garde en memoire et revient a zero au redemarrage; il ne remplace pas la limite de depenses du fournisseur.
- Le controle DNS avant Requests ne ferme pas entierement le risque DNS rebinding. Garder le projet en demonstration locale tant que la protection reseau n'est pas renforcee.
- Les dates exactes du stage et les faits personnels (accueil, echanges, revue du tuteur, retours de l'equipe, presentation et bilan) doivent etre confirmes par la stagiaire. Git ne permet pas de les deduire.
- Le choix d'hebergeur et l'autorisation de publication restent necessaires. Aucun site public n'a ete cree.
- Le DOCX original n'est pas modifie; le rapprochement des taches est dans `docs/verification-taches-stage.md`.
