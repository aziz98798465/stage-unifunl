"""Petites métriques déterministes pour l'évaluation manuelle du LLM."""


def evaluer_exemple(attendu, resultat):
    texte = " ".join([
        resultat.get("summary", ""),
        resultat.get("category", ""),
        resultat.get("name") or "",
        resultat.get("description") or "",
        " ".join(resultat.get("features", [])),
    ]).casefold()

    categorie_ok = resultat.get("category", "").casefold() == attendu["category"].casefold()
    nom_ok = attendu["name_contains"].casefold() in (resultat.get("name") or "").casefold()
    termes_ok = [terme for terme in attendu["required_terms"] if terme.casefold() in texte]
    champs_ok = all([
        bool(resultat.get("summary")),
        bool(resultat.get("name")),
        bool(resultat.get("description")),
        bool(resultat.get("features")),
    ])

    return {
        "id": attendu["id"],
        "category_match": categorie_ok,
        "name_match": nom_ok,
        "required_term_coverage": len(termes_ok) / len(attendu["required_terms"]),
        "required_terms_found": termes_ok,
        "required_terms_missing": [
            terme for terme in attendu["required_terms"] if terme not in termes_ok
        ],
        "required_fields_present": champs_ok,
    }
