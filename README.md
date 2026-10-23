# Stage d'immersion - Unifunl

Application Flask qui regroupe un scraper adapte a Books to Scrape et un verificateur de liens HTTP(S). Le depot contient aussi un exemple Playwright pour une page JavaScript.

## Fonctionnalites

- Extraction des titres, prix, devises et images avec Requests et BeautifulSoup.
- Pagination jusqu'a 10 pages, erreurs gerees, et telechargement HTML parallele limite a trois workers.
- Scraping parallele de 1 a 10 URL independantes, avec au plus trois telechargements simultanes et ordre d'entree conserve.
- Scraping de citations JavaScript avec Playwright.
- Verification des liens relatifs et absolus, avec rapports JSON/CSV et interface web.
- Analyse LLM facultative par OpenAI ou Ollama local : resume, categorie, nom, description et caracteristiques en JSON structure.
- Export CSV compatible avec Excel; cellules pouvant declencher une formule sont neutralisees.
- Validation HTTP(S), redirections controlees, protection contre les adresses locales et limite de 2 Mio par page HTML.

Le scraper de livres est adapte a la structure de Books to Scrape, pas a tous les sites. L'analyse LLM n'envoie le texte au fournisseur qu'apres une action explicite dans l'interface.

## Fichiers principaux

- `app.py` : application Flask et routes API.
- `scraper/first_scraper.py` : scraper statique et exports.
- `scraper/playwright_scraper.py` : exemple pour le contenu JavaScript.
- `broken-links-checker/` et `broken_links_checker/` : outil CLI, integration Flask et tests.
- `templates/`, `static/` : interfaces HTML, CSS et JavaScript.
- `llm_analyzer.py` : fournisseurs OpenAI/Ollama et validation de sortie.
- `llm_eval_samples.json`, `llm_eval.py`, `scripts/evaluer_llm.py` : exemples et evaluation facultative.
- `docs/` : rapport technique, checklist des 30 taches et documents de demonstration.

## Installation (Windows PowerShell)

Python 3.13 a ete utilise pour la verification. Node.js n'est pas necessaire.

```powershell
cd C:\Users\pc\Documents\stage-unifunl
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pour le scraper Playwright, installer Chromium une fois :

```powershell
python -m playwright install chromium
```

## Analyse IA facultative

Le scraper et le verificateur n'exigent aucune cle. L'analyse LLM necessite `OPENAI_API_KEY`; `.env.example` documente les noms, mais le fichier n'est pas charge automatiquement. Dans PowerShell :

```powershell
$env:OPENAI_API_KEY = "votre-cle"
$env:OPENAI_MODEL = "gpt-5-mini" # facultatif
```

Ne partagez pas la cle et ne la commitez pas. En mode OpenAI, l'application limite les appels a cinq par heure dans le processus courant, le texte a 12 000 caracteres, la sortie a 500 tokens et le timeout a 20 secondes. Le quota en memoire est remis a zero au redemarrage; configurez aussi une limite de depenses chez le fournisseur. Le texte envoye au fournisseur peut contenir des donnees sensibles; n'analyser que du contenu autorise. Des frais OpenAI peuvent s'appliquer.

### Mode local sans cle API

Pour utiliser un modele local au lieu d'OpenAI, installer [Ollama pour Windows](https://ollama.com/download). Dans PowerShell, telecharger le modele une fois :

```powershell
ollama pull gemma3:4b
```

Ollama doit rester lance sur ce PC. Dans le terminal qui demarre Flask, choisir le fournisseur local :

```powershell
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "gemma3:4b"
python .\app.py
```

Cette option n'a besoin ni de cle ni de credits API; le texte reste sur le PC. Le modele telecharge environ 3.4 Go et la vitesse depend du processeur et de la carte graphique. Pour revenir a OpenAI, definir `$env:LLM_PROVIDER = "openai"` et configurer `OPENAI_API_KEY`.

## Demarrage et demonstration locale

```powershell
python .\app.py
```

Le serveur local ecoute sur `127.0.0.1:5000`. Ouvrir `http://127.0.0.1:5000` pour le scraper et `http://127.0.0.1:5000/liens` pour le verificateur. Essai conseille : scraper Books to Scrape, puis verifier un petit nombre de liens sur `https://books.toscrape.com`. Ces actions font des requetes Internet.

Le bouton « Analyser avec l'IA » envoie explicitement le texte de la page au fournisseur choisi. En mode local, l'analyse requiert Ollama lance sur ce PC. Sans fournisseur configure, les autres fonctions restent utilisables.

Scripts autonomes :

```powershell
python .\scraper\first_scraper.py
python .\scraper\playwright_scraper.py
python .\broken-links-checker\broken_links_checker.py https://books.toscrape.com --max-liens 10
```

Les scrapers ecrivent leurs exports sous `scraper/output/`; le CLI du verificateur ecrit dans `broken-links-checker/output/`. Les CSV utilisent un BOM UTF-8.

## API

| Methode | Route | Description |
|---|---|---|
| GET | `/` | Interface scraper |
| GET | `/liens` | Interface verificateur |
| GET | `/api/health` | Etat de l'API |
| GET | `/api/scrape?url=<URL>` | Scrape jusqu'a trois pages |
| POST | `/api/scrape-batch` | `{"urls": [...]}` : 1 a 10 URL publiques independantes, concurrence maximale de 3 |
| POST | `/api/check-links` | `{"url": "...", "max_liens": 10}`; limite de 1 a 500 liens |
| POST | `/api/analyze-page` | `{"url": "https://..."}` : recupere au plus 2 Mio puis analyse si la cle est configuree |
| POST | `/api/analyze-text` | `{"text": "..."}` : analyse du texte brut si la cle est configuree |

Les erreurs d'entree sont renvoyees en JSON. Les erreurs amont renvoient une erreur de passerelle, et les erreurs internes un message generique.

## Tests

```powershell
python -m compileall -q app.py scraper broken_links_checker broken-links-checker scripts
python -m pytest -v
```

La suite utilise des mocks pour les appels reseau et LLM. Lors de la finalisation, 64 tests ont reussi. `python .\scripts\evaluer_llm.py` effectue trois appels au fournisseur configure; en mode OpenAI, ils peuvent etre facturables. Ce script n'est pas lance par pytest. La qualite reelle n'a pas ete mesuree.

## Hebergement de demonstration

Aucun hebergeur ni compte n'est configure et le projet n'a pas ete publie. Render est une option a evaluer : build `pip install -r requirements.txt`, demarrage `gunicorn app:app`. Verifier les limites et tarifs de l'offre. Une offre gratuite peut suspendre le service apres inactivite et ne fournit pas un disque persistant. Configurer les secrets dans son tableau de bord. La protection SSRF/DNS rebinding actuelle ne suffit pas pour presenter le projet comme service public multi-utilisateur.

## Limites de securite

- Le controle DNS avant la connexion ne neutralise pas completement le DNS rebinding; Requests resout le nom au moment de la connexion.
- Respecter les conditions d'acces et les limites des sites. Aucun CAPTCHA ni controle d'acces n'est contourne.
- Les textes affiches par les interfaces sont rendus en texte brut, et les exports CSV protegent les cellules de formule.
- Playwright exige l'installation du navigateur Chromium.

La liste des taches du stage et leur statut sont dans [docs/verification-taches-stage.md](docs/verification-taches-stage.md). Les dates, activites personnelles, retours d'equipe, presentation et bilan doivent etre confirmes par la stagiaire.
