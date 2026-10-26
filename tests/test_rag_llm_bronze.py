"""Lot D : rapport Bronze (baselines triviales, catégories d'erreurs) et gel du test."""

from math import isclose

from rag_llm import bronze_report as br
from rag_llm import freeze_test


def test_baseline_aleatoire_esperance_exacte():
    # 4 passages, 1 seul pertinent : rang uniforme entre 1 et 4
    m = br.random_retrieval_expectation(4, 1)
    assert m["recall@5"] == 1.0 and isclose(m["hit@1"], 0.25)
    assert isclose(m["mrr"], (1 + 1 / 2 + 1 / 3 + 1 / 4) / 4)
    # 84 passages : Rappel@5 = 5/84 quel que soit le nombre de preuves
    assert isclose(br.random_retrieval_expectation(84, 3)["recall@5"], 5 / 84)


def test_baseline_verdict_majorite_et_abstention():
    claims = [{"gold_label": "faux"}, {"gold_label": "faux"}, {"gold_label": "vrai"}]
    assert br.verdict_baseline(claims, "faux")["accuracy"] == round(2 / 3, 3)
    abst = br.verdict_baseline(claims, br.NEI)
    assert abst["accuracy"] == 0.0 and abst["coverage"] == 0.0


def test_categories_retrieval():
    arabizi = {"lang": "tn", "script": "arabizi"}
    assert br.retrieval_category(arabizi, "ar", None).startswith("arabizi")
    fr = {"lang": "fr", "script": "latin"}
    assert br.retrieval_category(fr, "ar", 7).startswith("langue croisée")
    assert br.retrieval_category(fr, "fr", 7).startswith("même langue")
    assert br.retrieval_category(fr, "fr", None).startswith("paraphrase")


def test_categories_verdict():
    row = {"gold": "faux", "abstained": True, "reason": "preuves_non_decisives"}
    assert "non retrouvée" in br.verdict_category(row, gold_in_top5=False)
    assert "non décisive" in br.verdict_category(row, gold_in_top5=True)
    assert "trompeur" in br.verdict_category({**row, "gold": "trompeur"}, True)


def test_rapport_sur_le_dev_avec_les_regles():
    res = br.evaluate_split("dev", br.DEV_CORPUS, br.DEV_CLAIMS, stance="rules")
    assert res["retrieval"]["bm25"]["recall@5"] > res["retrieval"]["random"]["recall@5"]
    assert res["verdict"]["rules"]["accuracy"] == 0.7  # EXP-D-002, inchangé
    assert all(e["categorie"] and e["claim_id"] for e in res["errors"])


def test_jeu_de_test_gele_intact():
    assert freeze_test.check() == []
