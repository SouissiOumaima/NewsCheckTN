"""Lot D — Rapport du palier Bronze : scores, baselines triviales, langues et erreurs (EXP-D-007).

Composants classiques uniquement : retrieval BM25 et verdict par gabarit. La position des preuves
vient du NLI Bronze du Lot C (`models.nli.stance`, règles par lexique) ou, pour comparaison, du
NLI provisoire du Lot D (`--stance rules`).

Baselines triviales (exigées par la revue Bronze) :
- retrieval : passages tirés au hasard. Les scores donnés sont l'**espérance exacte** du tirage
  (calcul combinatoire), pas un tirage particulier : aucun effet de graine.
  Pour N passages et g preuves attendues : Rappel@k = k / N ; Hit@k = 1 − C(N−g, k) / C(N, k) ;
  MRR = Σ_{r ≤ 10} (1/r) · C(N−r, g−1) / C(N, g).
- verdict : « classe majoritaire » (label le plus fréquent du jeu de **dev**, appliqué partout)
  et « toujours s'abstenir » (`preuves_insuffisantes`).

Erreurs : (1) retrieval — chaque preuve attendue absente du top 5 ; (2) verdict — chaque
affirmation dont le verdict diffère de la référence. Une catégorie par erreur, attribuée par une
règle fixe (voir `retrieval_category` et `verdict_category`), à relire à la main.

Usage (depuis la racine du dépôt) :
    python -m rag_llm.build_tunifact_eval        # corpus de test (non versionné)
    python -m rag_llm.bronze_report              # NLI Bronze du Lot C (défaut)
    python -m rag_llm.bronze_report --stance rules
Sorties :
- evaluation/results/lot-d_bronze_<stance>_<AAAAMMJJ>.json   (scores, non versionné)
- evaluation/results/lot-d_erreurs_<stance>.csv              (avec les textes : non versionné)
- docs/lot-d_erreurs_bronze.csv                              (sans texte de preuve : versionné)
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from math import comb
from pathlib import Path

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from evaluation.metrics import macro_f1
from rag_llm import evaluate_verdict
from rag_llm.evaluate_retrieval import FIXTURES, RESULTS_DIR, ROOT, load_claims
from rag_llm.evaluate_retrieval import compute_metrics as retrieval_metrics
from rag_llm.retrieval.bm25 import BM25Index
from rag_llm.retrieval.hybrid import retrieve

K = 5
NEI = "preuves_insuffisantes"
TEST_CORPUS = ROOT / "data" / "interim" / "lot_d" / "evidence_tunifact_v1.jsonl"
TEST_CLAIMS = FIXTURES / "claims_tunifact_v1.jsonl"
DEV_CORPUS = FIXTURES / "evidence_dev.jsonl"
DEV_CLAIMS = FIXTURES / "claims_dev.jsonl"
DOCS_CSV = ROOT / "docs" / "lot-d_erreurs_bronze.csv"
GROUPS = ("fr-latin", "ar-arabic", "tn-arabic", "tn-arabizi")


# ---------------------------------------------------------------------------
# Baselines triviales
# ---------------------------------------------------------------------------


def random_retrieval_expectation(n: int, g: int, k: int = K, max_rank: int = 10) -> dict:
    """Espérance exacte des métriques pour un classement aléatoire de n passages, g pertinents."""
    if g == 0 or n == 0:
        return {}
    hit = lambda kk: 1 - comb(n - g, kk) / comb(n, kk)  # noqa: E731
    first_at = lambda r: comb(n - r, g - 1) / comb(n, g)  # noqa: E731  P(1er pertinent au rang r)
    return {
        "recall@1": min(1, n) / n,
        "recall@5": min(k, n) / n,
        "hit@1": hit(1),
        "hit@5": hit(min(k, n)),
        "mrr": sum(first_at(r) / r for r in range(1, min(max_rank, n) + 1)),
    }


def random_baseline(claims: list[dict], n_passages: int) -> dict:
    rows = [random_retrieval_expectation(n_passages, len(c["gold_doc_ids"])) for c in claims]
    rows = [r for r in rows if r]
    out = {m: round(sum(r[m] for r in rows) / len(rows), 3) for m in rows[0]} if rows else {}
    out["n"] = len(rows)
    return out


def verdict_baseline(claims: list[dict], label: str) -> dict:
    gold = [c["gold_label"] for c in claims]
    pred = [label] * len(gold)
    return {
        "n": len(gold),
        "accuracy": round(sum(a == b for a, b in zip(gold, pred, strict=True)) / len(gold), 3),
        "macro_f1": round(macro_f1(gold, pred), 3),
        "coverage": 0.0 if label == NEI else 1.0,
    }


# ---------------------------------------------------------------------------
# Catégories d'erreurs (règles fixes, à relire)
# ---------------------------------------------------------------------------


def _family(lang: str | None) -> str:
    return "fr" if lang == "fr" else "ar"  # tunisien et arabe standard partagent l'écriture arabe


def retrieval_category(claim: dict, evidence_lang: str | None, rank: int | None) -> str:
    if claim.get("script") == "arabizi":
        return "arabizi (aucun mot commun avec l'écriture arabe)"
    if claim["lang"] == "tn":
        return "tunisien en lettres arabes (vocabulaire dialectal)"
    if _family(claim["lang"]) != _family(evidence_lang):
        return "langue croisée (affirmation et preuve dans deux langues)"
    if rank is None:
        return "paraphrase : aucun mot commun avec la preuve"
    return "même langue, classé après le top 5"


def verdict_category(row: dict, gold_in_top5: bool) -> str:
    if row["gold"] == "trompeur":
        return "« trompeur » : label que le gabarit ne produit pas"
    if row["gold"] == NEI:
        return "verdict émis alors que le corpus n'a pas de preuve"
    if not gold_in_top5:
        return "bonne preuve non retrouvée (retrieval)"
    if not row["abstained"]:
        return "position inversée par le NLI (vrai ↔ faux)"
    if row["reason"] == "preuves_contradictoires":
        return "preuves jugées contradictoires"
    return "preuve retrouvée mais jugée non décisive (NLI)"


# ---------------------------------------------------------------------------
# Évaluation d'un jeu
# ---------------------------------------------------------------------------


def _langs(corpus_path: Path) -> dict[str, str]:
    with corpus_path.open(encoding="utf-8") as f:
        return {r["doc_id"]: r.get("lang") for r in map(json.loads, filter(str.strip, f))}


def _by_group(rows: list[dict], metric_fn) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)
    return {g: metric_fn(groups[g]) for g in GROUPS if g in groups}


def evaluate_split(name: str, corpus_path: Path, claims_path: Path, stance: str) -> dict:
    corpus = load_evidence_corpus(corpus_path)
    claims = load_claims(claims_path)
    langs = _langs(corpus_path)
    texts = {e.doc_id: e.text for e in corpus}
    index = BM25Index(corpus)

    # Retrieval BM25 (top 10 pour le MRR, top 5 pour le verdict et les erreurs)
    r_rows, errors = [], []
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        top = [e.doc_id for e in retrieve(claim, corpus, k=10, method="bm25")]
        group = f"{c['lang']}-{c.get('script', '?')}"
        r_rows.append({"claim_id": c["claim_id"], "group": group,
                       "gold": c.get("gold_doc_ids", []), "retrieved": top})
        ranking = [e.doc_id for e in index.search(c["text"], k=len(corpus))]
        for gold_id in c.get("gold_doc_ids", []):
            if gold_id in top[:K]:
                continue
            rank = ranking.index(gold_id) + 1 if gold_id in ranking else None
            errors.append({
                "jeu": name, "composant": "retrieval BM25", "claim_id": c["claim_id"],
                "groupe": group, "entree": c["text"], "sortie": " ".join(top[:K]) or "(aucun)",
                "reference": gold_id, "texte_reference": texts.get(gold_id, ""),
                "detail": f"rang BM25 {rank}" if rank else "score BM25 nul",
                "categorie": retrieval_category(c, langs.get(gold_id), rank),
            })

    # Verdict par gabarit, NLI choisi
    v_rows = evaluate_verdict.run(corpus, claims, stance=stance, k=K, method="bm25")
    top5 = {r["claim_id"]: set(r["retrieved"][:K]) for r in r_rows}
    for c, row in zip(claims, v_rows, strict=True):
        if row["pred"] == row["gold"]:
            continue
        gold_in_top5 = bool(set(c.get("gold_doc_ids", [])) & top5[c["claim_id"]])
        sortie = row["pred"] + (f" ({row['reason']})" if row["reason"] else "")
        if row["citations"]:
            sortie += " — cite " + " ".join(row["citations"])
        errors.append({
            "jeu": name, "composant": "verdict (gabarit + NLI)", "claim_id": c["claim_id"],
            "groupe": row["group"], "entree": c["text"], "sortie": sortie,
            "reference": row["gold"], "texte_reference": "",
            "detail": ("preuve attendue dans le top 5" if gold_in_top5
                       else "aucune preuve attendue dans le top 5"),
            "categorie": verdict_category(row, gold_in_top5),
        })

    def group_of(c: dict) -> str:
        return f"{c['lang']}-{c.get('script')}"

    majority = Counter(c["gold_label"] for c in load_claims(DEV_CLAIMS)).most_common(1)[0][0]
    return {
        "n_passages": len(corpus),
        "n_claims": len(claims),
        "retrieval": {
            "bm25": {**retrieval_metrics(r_rows), "by_group": _by_group(r_rows, retrieval_metrics)},
            "random": {**random_baseline(claims, len(corpus)),
                       "by_group": {
                           g: random_baseline([c for c in claims if group_of(c) == g], len(corpus))
                           for g in GROUPS}},
        },
        "verdict": {
            stance: {**evaluate_verdict.compute_metrics(v_rows),
                     "by_group": _by_group(v_rows, evaluate_verdict.compute_metrics)},
            f"majorite ({majority})": verdict_baseline(claims, majority),
            "toujours abstention": verdict_baseline(claims, NEI),
        },
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Sorties
# ---------------------------------------------------------------------------

FIELDS = ["jeu", "composant", "claim_id", "groupe", "entree", "sortie", "reference",
          "texte_reference", "detail", "categorie"]


def write_csv(path: Path, errors: list[dict], with_text: bool) -> None:
    fields = FIELDS if with_text else [f for f in FIELDS if f != "texte_reference"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig : lisible par Excel
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(errors)


def _fmt(v) -> str:
    return "—" if v is None else f"{v:.3f}"


def print_report(res: dict, stance: str) -> None:
    for split in ("dev", "test"):
        r = res[split]
        print(f"\n=== {split.upper()} — {r['n_claims']} affirmations, {r['n_passages']} passages")
        rb, rr = r["retrieval"]["bm25"], r["retrieval"]["random"]
        print(f"Retrieval  BM25    Rappel@5 {_fmt(rb['recall@5'])}  Hit@5 {_fmt(rb['hit@5'])}  "
              f"MRR {_fmt(rb['mrr'])}  (n={rb['n']})")
        print(f"           aléat.  Rappel@5 {_fmt(rr['recall@5'])}  Hit@5 {_fmt(rr['hit@5'])}  "
              f"MRR {_fmt(rr['mrr'])}")
        for name, m in r["verdict"].items():
            print(f"Verdict    {name:<22} exactitude {_fmt(m['accuracy'])}  macro-F1 "
                  f"{_fmt(m['macro_f1'])}  couverture {_fmt(m['coverage'])}")
    t = res["test"]
    print("\n=== TEST par langue / écriture")
    print(f"{'groupe':<12}{'n':>4}{'R@5 BM25':>11}{'R@5 aléat.':>12}{'exact. verdict':>16}")
    for g in GROUPS:
        b = t["retrieval"]["bm25"]["by_group"].get(g, {})
        a = t["retrieval"]["random"]["by_group"].get(g, {})
        v = t["verdict"][stance]["by_group"].get(g, {})
        print(f"{g:<12}{v.get('n', 0):>4}{_fmt(b.get('recall@5')):>11}"
              f"{_fmt(a.get('recall@5')):>12}{_fmt(v.get('accuracy')):>16}")
    errors = res["dev"]["errors"] + t["errors"]
    print("\n=== Erreurs (dev + test)")
    for comp in ("retrieval BM25", "verdict (gabarit + NLI)"):
        cats = Counter(e["categorie"] for e in errors if e["composant"] == comp)
        n_test = sum(1 for e in t["errors"] if e["composant"] == comp)
        print(f"{comp} : {sum(cats.values())} erreurs (dont {n_test} sur le test)")
        for cat, n in cats.most_common():
            print(f"   {n:>3}  {cat}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--stance", choices=["lot-c", "rules"], default="lot-c")
    p.add_argument("--test-corpus", type=Path, default=TEST_CORPUS)
    args = p.parse_args()
    if not args.test_corpus.exists():
        raise SystemExit(
            f"{args.test_corpus} absent : lancer d'abord python -m rag_llm.build_tunifact_eval"
        )

    res = {
        "dev": evaluate_split("dev", DEV_CORPUS, DEV_CLAIMS, args.stance),
        "test": evaluate_split("test", args.test_corpus, TEST_CLAIMS, args.stance),
    }
    print_report(res, args.stance)

    errors = res["dev"]["errors"] + res["test"]["errors"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    full_csv = RESULTS_DIR / f"lot-d_erreurs_{args.stance}.csv"
    write_csv(full_csv, errors, with_text=True)
    if args.stance == "lot-c":
        write_csv(DOCS_CSV, errors, with_text=False)
    out = RESULTS_DIR / f"lot-d_bronze_{args.stance}_{date.today():%Y%m%d}.json"
    payload = {
        "exp_id": "EXP-D-007", "lot": "D", "task": "retrieval+verdict (Bronze)",
        "model": f"bm25 + gabarit + NLI {args.stance}", "split": "dev-fictif-v2 / tunifact-v1",
        "metrics": {s: {k: v for k, v in res[s].items() if k != "errors"} for s in res},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRésultats : {out.relative_to(ROOT)}\nErreurs   : {full_csv.relative_to(ROOT)}"
          + (f" et {DOCS_CSV.relative_to(ROOT)}" if args.stance == "lot-c" else ""))


if __name__ == "__main__":
    main()
