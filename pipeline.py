"""Pipeline bout-en-bout NewsCheck TN (Lot E).

Enchaînement :
    texte brut
      -> [A2] normalize()              : normalisation + langue
      -> [B]  extract_claims()         : affirmations candidates (SPO, modalité)
      -> [C]  filter_checkworthy()     : garde les affirmations vérifiables
      -> [A1] load_evidence_corpus()   : corpus de preuves
      -> [D]  retrieve()               : preuves (BM25 + dense + re-ranking)
      -> [C]  predict_stances()        : NLI soutient / contredit / neutre
      -> [D]  generate_verdict()       : verdict argumenté + citations + abstention

Chaque lot ne modifie QUE sa propre fonction ; ce fichier n'est modifié que par le Lot E
(ou via PR relue par le Lot E).

Usage : python pipeline.py "Le taux de chômage en Tunisie est de 16,4 % en 2023."
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict

from common.schemas import Document, Verdict
from common.verdict_runtime import resolve_verdict
from data.loaders import load_evidence_corpus  # Lot A1
from linguistic_analysis.claim_extraction import extract_claims  # Lot B
from models.claim_detector import filter_checkworthy, model_status  # Lot C
from models.nli.stance import backend_info, predict_stances  # Lot C
from normalization.normalize import normalize  # Lot A2
from rag_llm.retrieval.hybrid import get_method, retrieve  # Lot D


def _claims_for_model1(text: str):
    """Extrait les claims normalisés et leurs phrases brutes pour Model 1.

    Lot B et les étapes aval conservent le document normalisé. Model 1 est
    cependant entraîné en ``raw`` : il reçoit donc les phrases provenant d'un
    document brut parallèle. Si les segmentations diffèrent, on retombe sans
    risque sur le texte normalisé plutôt que d'associer deux phrases fausses.
    """
    doc = normalize(text)
    claims = extract_claims(doc)
    raw_doc = Document(raw_text=text, text=text, lang=doc.lang, script=doc.script)
    raw_claims = extract_claims(raw_doc)
    raw_texts = [claim.text for claim in raw_claims] if len(raw_claims) == len(claims) else None
    return claims, raw_texts


def check_text_detailed(text: str, k: int = 5) -> dict:
    """Trace Silver : mêmes fonctions que /check, avec moteurs et temps mesurés."""
    started = time.perf_counter()
    claims, raw_texts = _claims_for_model1(text)
    extraction_ms = (time.perf_counter() - started) * 1000
    candidates = len(claims)
    stage = time.perf_counter()
    claims = filter_checkworthy(claims, classification_texts=raw_texts)
    filter_ms = (time.perf_counter() - stage) * 1000
    corpus = load_evidence_corpus() if claims else []
    traces = []
    for claim in claims:
        stage = time.perf_counter()
        evidences = retrieve(claim, corpus, k=k)
        retrieval_ms = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        stances = predict_stances(claim, evidences)
        nli_ms = (time.perf_counter() - stage) * 1000
        stage = time.perf_counter()
        verdict, engine = resolve_verdict(claim, evidences, stances)
        verdict_ms = (time.perf_counter() - stage) * 1000
        traces.append({
            "claim": asdict(claim),
            "evidences": [asdict(item) for item in stances],
            "verdict": asdict(verdict),
            "verdict_engine": engine,
            "timings_ms": {"retrieval": retrieval_ms, "nli": nli_ms, "verdict": verdict_ms},
        })
    return {
        "engines": {
            "model1": model_status(),
            "retrieval": get_method(),
            "nli": backend_info() if any(t["evidences"] for t in traces) else {"status": "not_run"},
        },
        "candidates": candidates,
        "retained": len(claims),
        "claims": traces,
        "timings_ms": {
            "extraction": extraction_ms,
            "filter": filter_ms,
            "total": (time.perf_counter() - started) * 1000,
        },
    }


def check_text(text: str, k: int = 5) -> list[Verdict]:
    # Conserver le type public historique : les objets Verdict ne sont pas reconstruits
    # depuis les dictionnaires de la route détaillée.
    claims, raw_texts = _claims_for_model1(text)
    claims = filter_checkworthy(claims, classification_texts=raw_texts)
    corpus = load_evidence_corpus() if claims else []
    verdicts = []
    for claim in claims:
        evidences = retrieve(claim, corpus, k=k)
        stances = predict_stances(claim, evidences)
        verdicts.append(resolve_verdict(claim, evidences, stances)[0])
    return verdicts


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "Le taux de chômage en Tunisie est de 16,4 % en 2023."
    for v in check_text(sample):
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
