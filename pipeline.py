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
from dataclasses import asdict

from common.schemas import Verdict
from data.loaders import load_evidence_corpus  # Lot A1
from linguistic_analysis.claim_extraction import extract_claims  # Lot B
from models.claim_detector import filter_checkworthy  # Lot C
from models.nli.stance import predict_stances  # Lot C
from normalization.normalize import normalize  # Lot A2
from rag_llm.retrieval.hybrid import retrieve  # Lot D
from rag_llm.verdict import generate_verdict  # Lot D


def check_text(text: str, k: int = 5) -> list[Verdict]:
    doc = normalize(text)
    claims = filter_checkworthy(extract_claims(doc))
    corpus = load_evidence_corpus()
    verdicts = []
    for claim in claims:
        evidences = retrieve(claim, corpus, k=k)
        stances = predict_stances(claim, evidences)
        verdicts.append(generate_verdict(claim, stances))
    return verdicts


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "Le taux de chômage en Tunisie est de 16,4 % en 2023."
    for v in check_text(sample):
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
