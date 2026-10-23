from llm_eval import evaluer_exemple


def test_evaluer_exemple_mesure_categorie_nom_et_termes():
    attendu = {
        "id": "sample",
        "category": "Article",
        "name_contains": "Urban Gardens",
        "required_terms": ["garden", "rainwater"],
    }
    resultat = {
        "summary": "An article about community rainwater projects.",
        "category": "Article",
        "name": "Urban Gardens in Dry Cities",
        "description": "A community guide.",
        "features": ["Garden planning"],
    }

    score = evaluer_exemple(attendu, resultat)

    assert score["category_match"] is True
    assert score["name_match"] is True
    assert score["required_term_coverage"] == 1
    assert score["required_fields_present"] is True


def test_evaluer_exemple_signale_termes_et_champs_manquants():
    attendu = {
        "id": "sample",
        "category": "Product",
        "name_contains": "Trail Bottle",
        "required_terms": ["steel", "750 ml"],
    }
    score = evaluer_exemple(attendu, {
        "summary": "A bottle.",
        "category": "Other",
        "name": None,
        "description": None,
        "features": [],
    })
    assert score["category_match"] is False
    assert score["name_match"] is False
    assert score["required_term_coverage"] == 0
    assert score["required_fields_present"] is False
