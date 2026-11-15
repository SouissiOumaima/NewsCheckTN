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

`check_text_detail()` fait la même chaîne mais renvoie chaque étape et son temps de calcul
(mode détail de la plateforme, pour la démo : texte normalisé, langue, affirmations, passages,
verdict, latence, moteurs réellement utilisés).
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict

from common.schemas import Document, Verdict
from data.loaders import corpus_origin, load_evidence_corpus  # Lot A1
from linguistic_analysis.claim_extraction import extract_claims  # Lot B
from models.claim_detector import filter_checkworthy, model_status  # Lot C
from models.nli.stance import backend_info, predict_stances  # Lot C
from normalization.normalize import normalize  # Lot A2
from rag_llm.retrieval.hybrid import retrieve  # Lot D
from rag_llm.verdict import generate_verdict  # Lot D


def _claims_for_model1(text: str):
    """Extrait les claims normalisés et leurs phrases brutes pour Model 1.

    Lot B et les étapes aval conservent le document normalisé. Model 1 est
    cependant entraîné en ``raw`` : il reçoit donc les phrases provenant d'un
    document brut parallèle. Si les segmentations diffèrent, on retombe sans
    risque sur le texte normalisé plutôt que d'associer deux phrases fausses.
    """
    return _claims_from_doc(text, normalize(text))


def _claims_from_doc(text: str, doc: Document):
    claims = extract_claims(doc)
    raw_doc = Document(raw_text=text, text=text, lang=doc.lang, script=doc.script)
    raw_claims = extract_claims(raw_doc)
    raw_texts = [claim.text for claim in raw_claims] if len(raw_claims) == len(claims) else None
    return claims, raw_texts


def check_text(text: str, k: int = 5) -> list[Verdict]:
    claims, raw_texts = _claims_for_model1(text)
    claims = filter_checkworthy(claims, classification_texts=raw_texts)
    corpus = load_evidence_corpus()
    verdicts = []
    for claim in claims:
        evidences = retrieve(claim, corpus, k=k)
        stances = predict_stances(claim, evidences)
        verdicts.append(generate_verdict(claim, stances))
    return verdicts


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def components() -> dict:
    """Moteurs réellement utilisés à chaque étape, et s'ils sont tous classiques (Bronze)."""
    detector = model_status()["backend"]
    retrieval = os.getenv("RETRIEVAL_METHOD", "bm25").lower()
    nli = backend_info()["backend"]
    neural = [
        name
        for name, ok in (
            (f"détecteur {detector}", detector in {"tfidf-char-logreg", "heuristic-fallback"}),
            (f"recherche {retrieval}", retrieval == "bm25"),
            (f"NLI {nli}", nli in {"bronze", "stub"}),
        )
        if not ok
    ]
    return {
        "normalisation": "règles (Lot A2)",
        "extraction": "règles (Lot B)",
        "detecteur": detector,
        "recherche": retrieval,
        "nli": nli,
        "verdict": "gabarit + règles d'abstention (Lot D)",
        "classique": not neural,
        "neuronal": neural,
    }


def check_text_detail(text: str, k: int = 5) -> dict:
    """Même chaîne que `check_text`, avec chaque étape visible et chronométrée (en ms)."""
    timings: dict[str, float] = {}
    start = step = time.perf_counter()
    doc = normalize(text)
    timings["normalisation"] = _ms(step)

    step = time.perf_counter()
    claims, raw_texts = _claims_from_doc(text, doc)
    timings["extraction"] = _ms(step)

    step = time.perf_counter()
    kept = filter_checkworthy(claims, classification_texts=raw_texts)
    kept_ids = {id(claim) for claim in kept}
    timings["filtrage"] = _ms(step)

    detail = {
        "input": text,
        "normalized": {"text": doc.text, "lang": doc.lang.value, "script": doc.script},
        "claims": [{**asdict(claim), "kept": id(claim) in kept_ids} for claim in claims],
        "results": [],
        "components": components(),
        "out_of_scope": not kept,
        "message": None,
        "timings_ms": timings,
    }
    if not kept:
        detail["message"] = (
            "Aucune affirmation détectée dans ce texte : rien à vérifier, aucun verdict n'est émis."
            if not claims
            else "Aucune affirmation vérifiable (opinion, question ou autre) : "
            "le système s'abstient, aucun verdict n'est émis."
        )
        timings["total"] = _ms(start)
        return detail

    step = time.perf_counter()
    corpus = load_evidence_corpus()
    timings["corpus"] = _ms(step)
    detail["corpus"] = {**corpus_origin(), "size": len(corpus)}

    timings.update(recherche=0.0, nli=0.0, verdict=0.0)
    for claim in kept:
        step = time.perf_counter()
        evidences = retrieve(claim, corpus, k=k)
        timings["recherche"] += _ms(step)
        step = time.perf_counter()
        stances = predict_stances(claim, evidences)
        timings["nli"] += _ms(step)
        step = time.perf_counter()
        verdict = generate_verdict(claim, stances)
        timings["verdict"] += _ms(step)
        detail["results"].append(
            {
                "claim": asdict(claim),
                "evidences": [
                    {
                        **asdict(item.evidence),
                        "rank": rank,
                        "stance": item.stance.value,
                        "confidence": item.confidence,
                    }
                    for rank, item in enumerate(stances, start=1)
                ],
                "verdict": asdict(verdict),
            }
        )
    for key in ("recherche", "nli", "verdict"):
        timings[key] = round(timings[key], 1)
    timings["total"] = _ms(start)
    return detail


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "Le taux de chômage en Tunisie est de 16,4 % en 2023."
    for v in check_text(sample):
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
