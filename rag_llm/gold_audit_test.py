"""Lot D — Gold, EXP-D-016 : fichier d'annotation pour l'audit descriptif du test Tunifact v1.

Protocole : `docs/lot-d_protocole_gold.md`, sections 3 et 8.

- Aucune nouvelle génération : on reprend les 21 verdicts de Falcon (graine 42) déjà produits par
  EXP-D-015 sur le test (fichier de résultats privé `lot-d_silver_verdict_test_*.json`).
- Les passages montrés au système ne sont pas enregistrés dans ce fichier : on refait seulement la
  recherche hybride (déterministe, sans LLM ni NLI) pour retrouver les 5 mêmes passages, et l'on
  vérifie que chaque passage cité par le verdict en fait partie ; sinon, arrêt.
- Sortie privée (`evaluation/results/lot-d_annotation_hadil_test_v1.csv`), même format que pour le
  dev, sans le verdict de référence ; à annoter avec l'outil HTML et le guide.
- Audit descriptif : rien n'est réglé à partir de ce fichier (test déjà vu deux fois).

Usage :
    python -X utf8 -m rag_llm.gold_audit_test --results evaluation/results/<EXP-D-015>.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common.schemas import Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, load_claims
from rag_llm.gold_abstention import annotation_rows, write_csv
from rag_llm.silver_retrieval import SPLITS
from rag_llm.silver_verdict import K, prepare

EXP_ID = "EXP-D-016"
MAIN_SYSTEM = "LLM"  # système principal de silver_verdict (graine 42 dans per_claim)
OUT = RESULTS_DIR / "lot-d_annotation_hadil_test_v1.csv"


def no_stances(claim, evidences):
    """Les positions NLI ne servent pas ici : on ne refait que la recherche."""
    return [StanceResult(evidence=e, stance=Stance.NEUTRAL, confidence=0.0) for e in evidences]


def load_main_rows(results: Path) -> tuple[dict, list[dict]]:
    payload = json.loads(results.read_text(encoding="utf-8"))
    systems = payload.get("systems") or {}
    if MAIN_SYSTEM not in systems:
        raise SystemExit(f"Système « {MAIN_SYSTEM} » absent de {results.name}")
    return payload, systems[MAIN_SYSTEM]["per_claim"]


def check_citations(rows: list[dict], prepared: dict) -> list[str]:
    """Citations absentes des 5 passages retrouvés (doit être vide)."""
    bad = []
    for r in rows:
        top = {e.doc_id for e in prepared[r["claim_id"]][1][:K]}
        bad += [f"{r['claim_id']}:{d}" for d in r["citations"] if d not in top]
    return bad


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--results", type=Path, required=True, help="résultats EXP-D-015 sur le test")
    args = p.parse_args()

    payload, rows = load_main_rows(args.results)
    if payload.get("split") not in (None, "test"):
        raise SystemExit(f"Ce fichier n'est pas un résultat sur le test : {payload.get('split')}")
    print(f"Résultats : {args.results.name} — LLM {payload.get('llm')} — {len(rows)} verdicts")

    corpus_path, claims_path = SPLITS["test"]
    claims = load_claims(claims_path)
    by_id = {c["claim_id"]: c for c in claims}
    claims = [by_id[r["claim_id"]] for r in rows]
    method = payload.get("retrieval") or "hybrid"
    prepared = prepare(load_evidence_corpus(corpus_path), claims, method, no_stances)

    bad = check_citations(rows, prepared)
    if bad:
        raise SystemExit(f"Recherche non reproduite (citations hors des 5 passages) : {bad}")

    lines = annotation_rows(claims, prepared, rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT, lines)
    print(f"{EXP_ID} : {len(lines)} verdicts à annoter → {OUT.relative_to(ROOT)}")
    print(
        "Verdicts :",
        {v: sum(r["pred"] == v for r in rows) for v in sorted({r["pred"] for r in rows})},
    )


if __name__ == "__main__":
    main()
