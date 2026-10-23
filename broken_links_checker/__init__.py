
from pathlib import Path
import importlib.util


# Charger le module existant situé dans le dossier avec un tiret.
CHEMIN_MODULE = (
    Path(__file__).resolve().parent.parent
    / "broken-links-checker"
    / "broken_links_checker.py"
)

spec = importlib.util.spec_from_file_location(
    "broken_links_checker_original",
    CHEMIN_MODULE,
)

if spec is None or spec.loader is None:
    raise ImportError(
        f"Impossible de charger le module : {CHEMIN_MODULE}"
    )

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

verifier_liens_page = module.verifier_liens_page
creer_session = module.creer_session
valider_url = module.valider_url
effectuer_requete_securisee = module.effectuer_requete_securisee
lire_contenu_limite = module.lire_contenu_limite
