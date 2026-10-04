"""Lot B — Segmentation et extraction d'affirmations candidates (SPO, modalité).

Enchaînement : segmentation → factualité → SPO → modalité → coréférence.
`extract_claims` (contrat partagé) projette la sortie détaillée vers `common.schemas.Claim`,
sans exclure les opinions : l'information `is_opinion` reste dans la sortie détaillée, le
filtrage éventuel relevant d'une décision d'équipe.
"""

from __future__ import annotations

from common.schemas import Claim, Document
from linguistic_analysis import coreference, factuality, modality, spo
from linguistic_analysis.preprocessing import analyze, split_sentences
from linguistic_analysis.types import ExtractedClaim

__all__ = ["detect_modality", "extract_claims", "extract_claims_detailed", "split_sentences"]

MIN_TOKENS = 4


def detect_modality(sentence: str) -> str:
    """Label de modalité seul (voir `modality.detect_modality` pour le score et les indices)."""
    return modality.detect_modality(sentence)[0]


def extract_claims_detailed(doc: Document) -> list[ExtractedClaim]:
    """Sortie détaillée du Lot B (champs internes inclus), opinions comprises."""
    sentences = [s for s in analyze(doc) if len(s.text.split()) >= MIN_TOKENS]
    resolved = coreference.resolve([s.text for s in sentences])

    claims = []
    for sentence, resolved_text in zip(sentences, resolved, strict=True):
        is_opinion, opinion_conf, opinion_triggers = factuality.classify_factuality(sentence)
        triple = spo.extract_spo(sentence.text) or spo.SPO()
        label, certainty, modality_triggers = modality.detect_modality(sentence.text)
        claims.append(
            ExtractedClaim(
                text=sentence.text,
                lang=doc.lang,  # TODO(Lot B): sentence.lang une fois le point L1 tranché
                span=(sentence.start, sentence.end),
                resolved_text=resolved_text,
                subject=triple.subject,
                predicate=triple.predicate,
                obj=triple.obj,
                modality=label,
                certainty=certainty,
                is_opinion=is_opinion,
                confidence=max(triple.confidence, opinion_conf),
                parser=sentence.parser,
                triggers=opinion_triggers + modality_triggers,
            )
        )
    return claims


def extract_claims(doc: Document) -> list[Claim]:
    """Point d'entrée du Lot B (contrat partagé) : affirmations candidates à la vérification."""
    return [c.to_claim() for c in extract_claims_detailed(doc)]
