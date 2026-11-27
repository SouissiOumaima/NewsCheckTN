"""Lot D — EXP-D-021 : incertitude du verdict calculée à partir du NLI.

Protocole : `docs/lot-d_protocole_reranker_incertitude.md`, section 4 (fixé avant la mesure).

Formule (aucun paramètre réglé) : soutien `s` des passages au verdict, puis u = 1 − s.
- vrai : plus haute confiance « soutient » parmi les passages cités (0 s'il n'y en a pas) ;
- faux : plus haute confiance « contredit » parmi les passages cités ;
- trompeur : plus haute confiance « soutient » ou « contredit » parmi les passages cités ;
- preuves insuffisantes : moyenne, sur les 5 passages proposés, de la confiance s'il est neutre,
  0 sinon.

Aucune nouvelle génération de Falcon : verdicts relus dans les résultats enregistrés
(dev : EXP-D-018, graine 42 ; test : EXP-D-015, graine 42). La recherche et le NLI affiné sont
recalculés (déterministes) ; chaque passage cité doit faire partie des 5 retrouvés.

Cibles : principale = verdict faux ; secondaire = verdict faux ou jugé infidèle (annotation
humaine). Mesures : AUROC (IC 95 % par bootstrap), Brier, ECE à 5 classes.
Décision (dev seulement) : adoptée si la borne basse de l'IC 95 % de l'AUROC principale > 0.5.

Usage : `rag_llm/exp_d_021_incertitude.ps1 -Split dev`, puis `-Split test` (descriptif).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date
from pathlib import Path

from data.loaders import load_evidence_corpus
from rag_llm.bronze_report import NEI
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, load_claims
from rag_llm.silver_retrieval import SPLITS
from rag_llm.silver_verdict import K, prepare

EXP_ID = "EXP-D-021"
NLI_REQUIRED = "fine-tuned"
REPLICATIONS = 10_000
SEED = 42
N_BINS = 5
EXPECTED = {"vrai": {"supports"}, "faux": {"refutes"}, "trompeur": {"supports", "refutes"}}
SOURCES = {
    "dev": "lot-d_gold_abstention_dev_*_20261122.json",
    "test": "lot-d_silver_verdict_test_*_exp-d-015.json",
}
ANNOTATIONS = {
    "dev": "lot-d_annotation_hadil_dev_annote.csv",
    "test": "lot-d_annotation_hadil_test_v1_annote.csv",
}


# ---------------------------------------------------------------------------
# Formule
# ---------------------------------------------------------------------------


def uncertainty(pred: str, citations: list[str], stances: dict[str, tuple[str, float]]) -> float:
    """u = 1 − soutien ; `stances` : doc_id → (position, confiance) des 5 passages proposés."""
    if pred == NEI:
        if not stances:
            return 1.0
        s = sum(conf if st == "neutral" else 0.0 for st, conf in stances.values()) / len(stances)
    else:
        want = EXPECTED.get(pred, set())
        s = max(
            (stances[d][1] for d in citations if d in stances and stances[d][0] in want),
            default=0.0,
        )
    return round(1.0 - s, 4)


# ---------------------------------------------------------------------------
# Mesures
# ---------------------------------------------------------------------------


def auroc(scores: list[float], labels: list[int]) -> float | None:
    """P(score d'un cas positif > score d'un cas négatif), égalités comptées 1/2."""
    pos = [s for s, y in zip(scores, labels, strict=True) if y]
    neg = [s for s, y in zip(scores, labels, strict=True) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def auroc_ci(scores, labels, replications=REPLICATIONS, seed=SEED) -> list[float] | None:
    n, rng, vals = len(scores), random.Random(seed), []
    for _ in range(replications):
        idx = [rng.randrange(n) for _ in range(n)]
        a = auroc([scores[i] for i in idx], [labels[i] for i in idx])
        if a is not None:
            vals.append(a)
    if not vals:
        return None
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def brier(scores, labels) -> float:
    return round(sum((s - y) ** 2 for s, y in zip(scores, labels, strict=True)) / len(scores), 4)


def ece(scores, labels, n_bins: int = N_BINS) -> float:
    total, out = len(scores), 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        idx = [i for i, s in enumerate(scores) if lo <= s < hi or (b == n_bins - 1 and s == 1.0)]
        if idx:
            gap = abs(
                sum(labels[i] for i in idx) / len(idx) - sum(scores[i] for i in idx) / len(idx)
            )
            out += gap * len(idx) / total
    return round(out, 4)


def measure(scores, labels) -> dict:
    a = auroc(scores, labels)
    return {
        "n": len(labels),
        "positifs": sum(labels),
        "auroc": None if a is None else round(a, 3),
        "auroc_ci95": auroc_ci(scores, labels) if a is not None else None,
        "brier": brier(scores, labels),
        "ece": ece(scores, labels),
    }


def decide(primary: dict) -> dict:
    ci = primary.get("auroc_ci95")
    adopted = bool(ci) and ci[0] > 0.5
    return {"rule": "borne basse IC95 AUROC (verdict faux) > 0.5 sur le dev", "adopted": adopted}


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------


def find_one(pattern: str) -> Path:
    files = sorted(RESULTS_DIR.glob(pattern))
    files = [f for f in files if "_vs_ref" not in f.name and "limit" not in f.name]
    if len(files) != 1:
        raise SystemExit(
            f"Un seul fichier attendu pour {pattern}, trouvé : {[f.name for f in files]}"
        )
    return files[0]


def load_verdicts(split: str) -> tuple[Path, list[dict]]:
    path = find_one(SOURCES[split])
    payload = json.loads(path.read_text(encoding="utf-8"))
    if split == "dev":
        rows = payload["per_seed"]["42"]["llm_rows"]
    else:
        rows = payload["systems"]["LLM"]["per_claim"]
    return path, rows


def load_infidele(split: str) -> dict[str, bool] | None:
    path = RESULTS_DIR / ANNOTATIONS[split]
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r["claim_id"]: r["fidelite"].strip() == "infidele" for r in csv.DictReader(f)}


def load_split_claims(split: str) -> list[dict]:
    if split == "dev":
        from rag_llm.gold_abstention import load_dev_claims

        return load_dev_claims()
    return load_claims(SPLITS["test"][1])


def stance_table(prepared: dict) -> dict[str, dict[str, tuple[str, float]]]:
    return {
        cid: {s.evidence.doc_id: (s.stance.value, s.confidence) for s in stances[:K]}
        for cid, (_, _, stances) in prepared.items()
    }


def build_rows(verdicts, stances, infidele) -> list[dict]:
    out = []
    for v in verdicts:
        table = stances[v["claim_id"]]
        missing = [d for d in v["citations"] if d not in table]
        if missing:
            raise SystemExit(f"Recherche non reproduite : {v['claim_id']} cite {missing}")
        wrong = v["pred"] != v["gold"]
        row = {
            "claim_id": v["claim_id"],
            "pred": v["pred"],
            "gold": v["gold"],
            "u": uncertainty(v["pred"], v["citations"], table),
            "faux": int(wrong),
        }
        if infidele is not None and v["claim_id"] in infidele:
            row["mauvais"] = int(wrong or infidele[v["claim_id"]])
        out.append(row)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--split", required=True, choices=["dev", "test"])
    args = p.parse_args()

    from models.nli.stance import backend_info, predict_stances

    nli = backend_info()
    if nli.get("backend") != NLI_REQUIRED or nli.get("status") != "loaded":
        raise SystemExit(f"NLI attendu : {NLI_REQUIRED} chargé ; obtenu : {nli}")

    source, verdicts = load_verdicts(args.split)
    claims = {c["claim_id"]: c for c in load_split_claims(args.split)}
    claims = [claims[v["claim_id"]] for v in verdicts]
    corpus = load_evidence_corpus(SPLITS[args.split][0])
    prepared = prepare(corpus, claims, "hybrid", predict_stances)
    rows = build_rows(verdicts, stance_table(prepared), load_infidele(args.split))

    u = [r["u"] for r in rows]
    res = {"principale (verdict faux)": measure(u, [r["faux"] for r in rows])}
    with_bad = [r for r in rows if "mauvais" in r]
    if with_bad:
        res["secondaire (faux ou infidèle)"] = measure(
            [r["u"] for r in with_bad], [r["mauvais"] for r in with_bad]
        )
    payload = {
        "exp_id": EXP_ID,
        "date": date.today().isoformat(),
        "split": args.split,
        "source_verdicts": source.name,
        "nli": nli,
        "results": res,
        "decision": decide(res["principale (verdict faux)"]) if args.split == "dev" else None,
        "per_claim": rows,
    }
    print(f"\n{EXP_ID} — {args.split} — {len(rows)} verdicts (source : {source.name})")
    for name, m in res.items():
        print(
            f"  {name:<30} n={m['n']:<3} positifs={m['positifs']:<3} AUROC {m['auroc']}"
            f" {m['auroc_ci95']}  Brier {m['brier']}  ECE {m['ece']}"
        )
    if payload["decision"]:
        print(f"  Décision : {payload['decision']}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-d_incertitude_{args.split}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
