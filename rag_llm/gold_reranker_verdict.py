"""Lot D — EXP-D-020 (suite) : effet du re-ranker sur le verdict, sur le dev seulement.

Protocole : `docs/lot-d_protocole_reranker_incertitude.md`, section 3 (règle fixée avant) :
« S'il est adopté, son effet sur le verdict est mesuré sur le dev seulement (Falcon, 30 phrases,
3 graines) : il ne doit pas faire perdre plus d'une bonne réponse (graine 42). Aucun nouveau
verdict n'est généré sur le test v1. »

- Même système qu'EXP-D-018 (Falcon-H1-3B + JSON, prompt v1, NLI affiné, 3 graines), avec les
  5 passages du re-ranker retenu (`lot-d_reranker_dev.json`) au lieu de ceux de la fusion RRF.
- Comparaison avec les verdicts enregistrés d'EXP-D-018 (graine 42), sans les régénérer.
- « Bonne réponse perdue » : juste avant, fausse après (même définition qu'EXP-D-018).

Usage : `rag_llm/exp_d_020_verdict_dev.ps1` (Ollama lancé).
"""

from __future__ import annotations

import json
from datetime import date

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from rag_llm import llm_verdict as lv
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT
from rag_llm.evaluate_verdict import compute_metrics
from rag_llm.gold_abstention import load_dev_claims
from rag_llm.gold_uncertainty import find_one
from rag_llm.retrieval.rerank import CrossEncoderScorer, candidates, rerank
from rag_llm.silver_retrieval import SPLITS
from rag_llm.silver_verdict import MAIN_SEED, SEEDS, CachedGenerator, K, run_llm

EXP_ID = "EXP-D-020"
MAX_LOST = 1
NLI_REQUIRED = "fine-tuned"


def prepare_reranked(corpus, claims, scorer, predict_stances) -> dict:
    out = {}
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        top = rerank(claim, candidates(claim, corpus), scorer, k=K)
        out[c["claim_id"]] = (claim, top, predict_stances(claim, top))
    return out


def compare(base: list[dict], new: list[dict]) -> dict:
    by_id = {r["claim_id"]: r for r in base}
    lost = [
        r["claim_id"]
        for r in new
        if by_id[r["claim_id"]]["pred"] == by_id[r["claim_id"]]["gold"] and r["pred"] != r["gold"]
    ]
    gained = [
        r["claim_id"]
        for r in new
        if by_id[r["claim_id"]]["pred"] != by_id[r["claim_id"]]["gold"] and r["pred"] == r["gold"]
    ]
    return {
        "correct_base": sum(r["pred"] == r["gold"] for r in base),
        "correct_rerank": sum(r["pred"] == r["gold"] for r in new),
        "lost": lost,
        "gained": gained,
        "condition_at_most_one_lost": len(lost) <= MAX_LOST,
    }


def main() -> None:
    from models.nli.stance import backend_info, predict_stances

    nli = backend_info()
    if nli.get("backend") != NLI_REQUIRED or nli.get("status") != "loaded":
        raise SystemExit(f"NLI attendu : {NLI_REQUIRED} chargé ; obtenu : {nli}")
    dev_rr = json.loads((RESULTS_DIR / "lot-d_reranker_dev.json").read_text(encoding="utf-8"))
    test_rr = RESULTS_DIR / "lot-d_reranker_test.json"
    if (
        not test_rr.exists()
        or not json.loads(test_rr.read_text(encoding="utf-8"))["decision"]["adopted"]
    ):
        raise SystemExit("Re-ranker non adopté sur le test : cette étape ne s'applique pas.")

    base_file = find_one("lot-d_gold_abstention_dev_*_20261122.json")
    base = json.loads(base_file.read_text(encoding="utf-8"))["per_seed"]

    claims = load_dev_claims()
    corpus = load_evidence_corpus(SPLITS["dev"][0])
    prepared = prepare_reranked(
        corpus, claims, CrossEncoderScorer(dev_rr["chosen_model"]), predict_stances
    )
    generator = CachedGenerator(lv.get_generator())
    per_seed = {}
    for seed in SEEDS:
        rows = run_llm(claims, prepared, generator, K, False, seed, "hybrid")
        per_seed[seed] = {
            "metrics_rerank": compute_metrics(rows),
            "metrics_base": compute_metrics(base[str(seed)]["llm_rows"]),
            "comparison": compare(base[str(seed)]["llm_rows"], rows),
            "rows": rows,
        }
    decision = per_seed[MAIN_SEED]["comparison"]["condition_at_most_one_lost"]

    print(f"\n{EXP_ID} (suite) — verdict sur le dev avec le re-ranker {dev_rr['chosen_model']}")
    for seed, r in per_seed.items():
        mb, mr, cmp_ = r["metrics_base"], r["metrics_rerank"], r["comparison"]
        print(
            f"  graine {seed:<5} exactitude {mb['accuracy']} → {mr['accuracy']} ; "
            f"couverture {mb['coverage']} → {mr['coverage']} ; "
            f"abst. justifiée {mb['justified_abstention']} → {mr['justified_abstention']} ; "
            f"perdues {cmp_['lost']} ; gagnées {cmp_['gained']}"
        )
    print(f"  Condition (graine {MAIN_SEED}, au plus {MAX_LOST} bonne réponse perdue) : {decision}")
    print(f"  Cache : {generator.hits} réutilisées, {generator.misses} générées")

    payload = {
        "exp_id": EXP_ID,
        "step": "verdict_dev",
        "date": date.today().isoformat(),
        "reranker": dev_rr["chosen_model"],
        "llm": generator.name,
        "nli": nli,
        "base": base_file.name,
        "condition_ok": decision,
        "per_seed": per_seed,
    }
    out = RESULTS_DIR / "lot-d_reranker_verdict_dev.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
