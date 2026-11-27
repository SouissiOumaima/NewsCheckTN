"""Lot D — EXP-D-020 : re-ranker cross-encoder après la recherche hybride.

Protocole : `docs/lot-d_protocole_reranker_incertitude.md`, section 3 (fixé avant la mesure).

- `--split dev` : contrôle et vitesse ; choisit le modèle (principal, ou repli si plus de 15 s
  par affirmation en moyenne) et l'enregistre ; aucune décision de qualité.
- `--split test` : mesure **unique** sur Tunifact v1 avec le modèle choisi sur le dev ; refuse de
  tourner si le dev n'a pas été fait, ou si la mesure du test existe déjà.
- Rappel@5 et MRR avant / après, en tout et par langue ; bootstrap apparié (10 000 tirages,
  graine 42) sur le rappel@5 par affirmation ; temps par affirmation.

Sorties non versionnées : `evaluation/results/lot-d_reranker_<split>.json`.
Usage : `rag_llm/exp_d_020_reranker.ps1 -Split dev`, puis `-Split test`.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import date

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, compute_metrics, load_claims
from rag_llm.retrieval import hybrid
from rag_llm.retrieval.rerank import (
    CANDIDATES,
    FALLBACK_MODEL,
    PRIMARY_MODEL,
    CrossEncoderScorer,
    candidates,
    rerank,
)
from rag_llm.silver_retrieval import SPLITS, lang_family, paired_bootstrap

EXP_ID = "EXP-D-020"
K = 5
MAX_SECONDS_PER_CLAIM = 15.0


def out_path(split: str):
    return RESULTS_DIR / f"lot-d_reranker_{split}.json"


def claim_recall(gold: list[str], retrieved: list[str], k: int = K) -> float:
    rel = set(gold)
    return len(rel & set(retrieved[:k])) / len(rel) if rel else 0.0


def evaluate(claims: list[dict], corpus, scorer) -> dict:
    base_rows, rr_rows, seconds = [], [], []
    for c in claims:
        if not c.get("gold_doc_ids"):
            continue
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        base = hybrid.retrieve(claim, corpus, k=K, method="hybrid")
        pool = candidates(claim, corpus, n=CANDIDATES)
        t = time.perf_counter()
        top = rerank(claim, pool, scorer, k=K)
        seconds.append(time.perf_counter() - t)
        common = {"claim_id": c["claim_id"], "lang": lang_family(c), "gold": c["gold_doc_ids"]}
        base_rows.append({**common, "retrieved": [e.doc_id for e in base]})
        rr_rows.append({**common, "retrieved": [e.doc_id for e in top], "pool": len(pool)})
    return {"base": base_rows, "rerank": rr_rows, "seconds": seconds}


def summarize(res: dict) -> dict:
    by_lang = defaultdict(lambda: {"base": [], "rerank": []})
    for b, r in zip(res["base"], res["rerank"], strict=True):
        by_lang[b["lang"]]["base"].append(b)
        by_lang[b["lang"]]["rerank"].append(r)
    base_r = [claim_recall(r["gold"], r["retrieved"]) for r in res["base"]]
    rr_r = [claim_recall(r["gold"], r["retrieved"]) for r in res["rerank"]]
    secs = res["seconds"]
    return {
        "hybride": compute_metrics(res["base"]),
        "hybride + re-ranker": compute_metrics(res["rerank"]),
        "par_langue": {
            lang: {"hybride": compute_metrics(v["base"]), "re-ranker": compute_metrics(v["rerank"])}
            for lang, v in sorted(by_lang.items())
        },
        "bootstrap_recall@5": paired_bootstrap(base_r, rr_r) if base_r else None,
        "seconds_per_claim": round(sum(secs) / len(secs), 2) if secs else None,
        "changed_claims": [
            b["claim_id"]
            for b, r in zip(res["base"], res["rerank"], strict=True)
            if b["retrieved"] != r["retrieved"]
        ],
    }


def choose_model(seconds_per_claim: float, primary: str = PRIMARY_MODEL) -> str:
    """Règle de repli du protocole : décidée sur la vitesse du dev seulement."""
    return FALLBACK_MODEL if seconds_per_claim > MAX_SECONDS_PER_CLAIM else primary


def decide(test: dict, dev: dict) -> dict:
    boot = test["bootstrap_recall@5"]
    up = boot is not None and boot["diff"] > 0 and boot["p_one_sided"] < 0.05
    dev_ok = dev["hybride + re-ranker"]["recall@5"] >= dev["hybride"]["recall@5"]
    return {
        "condition_1_test_recall_up_p<0.05": up,
        "condition_2_dev_recall_not_down": dev_ok,
        "adopted": up and dev_ok,
    }


def print_summary(split: str, model: str, s: dict) -> None:
    print(f"\n{EXP_ID} — {split} — re-ranker {model} — {s['hybride']['n']} affirmations")
    for name in ("hybride", "hybride + re-ranker"):
        m = s[name]
        print(f"  {name:<22} rappel@5 {m['recall@5']:.3f}  MRR {m['mrr']:.3f}")
    for lang, v in s["par_langue"].items():
        print(
            f"  {lang:<4} n={v['hybride']['n']:<3} rappel@5 {v['hybride']['recall@5']:.3f}"
            f" → {v['re-ranker']['recall@5']:.3f}"
        )
    b = s["bootstrap_recall@5"]
    if b:
        print(f"  bootstrap rappel@5 : {b['diff']:+.3f} {b['ci95']} p={b['p_one_sided']}")
    print(f"  temps du re-ranking : {s['seconds_per_claim']} s par affirmation")
    print(f"  affirmations dont le top 5 change : {s['changed_claims']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--split", required=True, choices=["dev", "test"])
    p.add_argument(
        "--model",
        choices=["principal", "repli"],
        default="principal",
        help="dev seulement : le repli ne sert que si le principal est trop lent",
    )
    args = p.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.split == "dev":
        model = PRIMARY_MODEL if args.model == "principal" else FALLBACK_MODEL
    else:
        dev_file = out_path("dev")
        if not dev_file.exists():
            raise SystemExit("Lancer d'abord --split dev (choix du modèle sur la vitesse).")
        if out_path("test").exists():
            raise SystemExit(
                "La mesure du test existe déjà : mesure unique (protocole, section 6)."
            )
        dev = json.loads(dev_file.read_text(encoding="utf-8"))
        model = dev["chosen_model"]
        if dev["model"] != model:
            raise SystemExit(
                f"Le dev n'a pas été contrôlé avec {model} : relancer --split dev --model repli."
            )

    corpus_path, claims_path = SPLITS[args.split]
    claims, corpus = load_claims(claims_path), load_evidence_corpus(corpus_path)
    scorer = CrossEncoderScorer(model)
    s = summarize(evaluate(claims, corpus, scorer))
    print_summary(args.split, model, s)

    payload = {
        "exp_id": EXP_ID,
        "date": date.today().isoformat(),
        "split": args.split,
        "model": model,
        "candidates": CANDIDATES,
        "k": K,
        "results": s,
    }
    if args.split == "dev":
        chosen = (
            FALLBACK_MODEL
            if model == FALLBACK_MODEL
            else choose_model(s["seconds_per_claim"] or 0.0)
        )
        payload["chosen_model"] = chosen
        print(
            f"\nModèle retenu pour le test (vitesse, > {MAX_SECONDS_PER_CLAIM} s → repli) :"
            f" {chosen}"
        )
        if chosen != model:
            print(
                "  → principal trop lent : relancer --split dev --model repli (contrôle du repli)."
            )
            payload["note"] = (
                "repli choisi sur la vitesse ; contrôle du dev à refaire avec le repli"
            )
    else:
        payload["decision"] = decide(s, dev["results"])
        print(f"\nDécision : {payload['decision']}")
    out = out_path(args.split)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
