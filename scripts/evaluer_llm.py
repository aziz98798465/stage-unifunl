"""Évaluer sur trois exemples. Cette commande réalise trois appels payants."""

import json
from pathlib import Path

from llm_analyzer import analyser_texte
from llm_eval import evaluer_exemple


RACINE = Path(__file__).resolve().parents[1]


def main():
    exemples = json.loads(
        (RACINE / "llm_eval_samples.json").read_text(encoding="utf-8")
    )
    rapports = []
    for exemple in exemples:
        resultat = analyser_texte(exemple["text"])
        rapports.append(evaluer_exemple(exemple, resultat))

    print(json.dumps(rapports, ensure_ascii=False, indent=2))
    moyenne_categorie = sum(r["category_match"] for r in rapports) / len(rapports)
    moyenne_nom = sum(r["name_match"] for r in rapports) / len(rapports)
    moyenne_termes = sum(r["required_term_coverage"] for r in rapports) / len(rapports)
    print(
        "Scores — catégorie: {:.0%}; nom: {:.0%}; termes: {:.0%}".format(
            moyenne_categorie,
            moyenne_nom,
            moyenne_termes,
        )
    )


if __name__ == "__main__":
    main()
