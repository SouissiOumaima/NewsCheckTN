"""Point d'entrée du pipeline français à règles du palier Bronze."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

from common.schemas import Evidence, Lang, Verdict
from data.loaders import load_evidence_corpus
from linguistic_analysis.claim_extraction import extract_claims
from models.nli.stance import predict_stances
from normalization.normalize import normalize
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.verdict import generate_verdict


def check_text(text: str, k: int = 5, corpus: list[Evidence] | None = None) -> list[Verdict]:
    """Vérifie un texte français sans classifieur, encodeur ou appel LLM.

    L'extracteur à règles produit les affirmations candidates. Une phrase dont
    la modalité n'est pas assertive est ignorée : la revue Bronze ne traite pas
    les hypothèses, questions et opinions comme des faits à vérifier.
    """
    document = normalize(text)
    if document.lang is not Lang.FR:
        raise ValueError("Le pipeline Bronze est limité au français (lang='fr').")

    claims = [
        claim for claim in extract_claims(document)
        if claim.modality == "assertif"
    ]
    corpus = load_evidence_corpus() if corpus is None else corpus
    verdicts: list[Verdict] = []
    for claim in claims:
        stances = predict_stances(claim, retrieve(claim, corpus, k=k))
        verdicts.append(generate_verdict(claim, stances))
    return verdicts


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "Tunis est la capitale de la Tunisie."
    for verdict in check_text(sample):
        print(json.dumps(asdict(verdict), ensure_ascii=False, indent=2))
