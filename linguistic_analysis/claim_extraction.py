"""Lot B — Segmentation et extraction d'affirmations candidates (SPO, modalité).

Enchaînement : segmentation → factualité → SPO → modalité → coréférence.
`extract_claims` (contrat partagé) projette la sortie détaillée vers `common.schemas.Claim`,
sans exclure les opinions : l'information `is_opinion` reste dans la sortie détaillée, le
filtrage éventuel relevant d'une décision d'équipe.
"""

from __future__ import annotations

import re

from common.schemas import Claim, Document
from linguistic_analysis import coreference, factuality, modality, spo
from linguistic_analysis.types import ExtractedClaim

_SENT_SPLIT = re.compile(r"(?<=[.!?؟])\s+")
MIN_TOKENS = 4


def split_sentences(text: str) -> list[tuple[str, tuple[int, int]]]:
    """Découpe en phrases avec leurs positions (début, fin) dans le texte."""
    sentences, start = [], 0
    for part in _SENT_SPLIT.split(text):
        idx = text.find(part, start)
        if part.strip():
            sentences.append((part.strip(), (idx, idx + len(part))))
        start = idx + len(part)
    return sentences


def detect_modality(sentence: str) -> str:
    """Label de modalité seul (voir `modality.detect_modality` pour le score et les indices)."""
    return modality.detect_modality(sentence)[0]


def extract_claims_detailed(doc: Document) -> list[ExtractedClaim]:
    """Sortie détaillée du Lot B (champs internes inclus), opinions comprises."""
    # TODO(Lot B): remplacer split_sentences par preprocessing.analyze(doc) (tokens, POS, arbre).
    candidates = [
        (sentence, span)
        for sentence, span in split_sentences(doc.text)
        if len(sentence.split()) >= MIN_TOKENS
    ]
    resolved = coreference.resolve([sentence for sentence, _ in candidates])
    parser = "rules"  # TODO(Lot B): nom du parseur réellement utilisé une fois analyze() en place

    claims = []
    for (sentence, span), resolved_text in zip(candidates, resolved, strict=True):
        is_opinion, opinion_conf, opinion_triggers = factuality.classify_factuality(sentence)
        triple = spo.extract_spo(sentence) or spo.SPO()
        label, certainty, modality_triggers = modality.detect_modality(sentence)
        claims.append(
            ExtractedClaim(
                text=sentence,
                lang=doc.lang,
                span=span,
                resolved_text=resolved_text,
                subject=triple.subject,
                predicate=triple.predicate,
                obj=triple.obj,
                modality=label,
                certainty=certainty,
                is_opinion=is_opinion,
                confidence=max(triple.confidence, opinion_conf),
                parser=parser,
                triggers=opinion_triggers + modality_triggers,
            )
        )
    return claims


def extract_claims(doc: Document) -> list[Claim]:
    """Point d'entrée du Lot B (contrat partagé) : affirmations candidates à la vérification."""
    return [c.to_claim() for c in extract_claims_detailed(doc)]
