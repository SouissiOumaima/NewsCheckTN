"""Lot B — Segmentation et extraction d'affirmations candidates (SPO, modalité).

Enchaînement : segmentation → factualité → SPO → modalité → coréférence.
`extract_claims` (contrat partagé) projette la sortie détaillée vers `common.schemas.Claim`,
sans exclure les opinions : l'information `is_opinion` reste dans la sortie détaillée, le
filtrage éventuel relevant d'une décision d'équipe.
"""

from __future__ import annotations

from common.schemas import Claim, Document, Lang
from linguistic_analysis import coreference, factuality, modality, spo
from linguistic_analysis.preprocessing import analyze, split_sentences
from linguistic_analysis.types import DEFAULT_MODALITY, ExtractedClaim

__all__ = ["detect_modality", "extract_claims", "extract_claims_detailed", "split_sentences"]

MIN_TOKENS = 4


def detect_modality(sentence: str) -> str:
    """Label de modalité d'une phrase isolée (voir `modality.detect_modality` pour le détail)."""
    doc = Document(raw_text=sentence, text=sentence, lang=Lang.UNKNOWN, script="mixed")
    analyzed = analyze(doc)
    return modality.detect_modality(analyzed[0])[0] if analyzed else DEFAULT_MODALITY


def extract_claims_detailed(doc: Document) -> list[ExtractedClaim]:
    """Sortie détaillée du Lot B (champs internes inclus), opinions comprises."""
    sentences = analyze(doc)
    # Coréférence sur toutes les phrases : un antécédent peut se trouver dans une phrase courte.
    resolutions = coreference.resolve_with_log(sentences)

    claims = []
    for sentence, resolution in zip(sentences, resolutions, strict=True):
        if len(sentence.text.split()) < MIN_TOKENS:
            continue
        is_opinion, opinion_conf, opinion_triggers = factuality.classify_factuality(sentence)
        triple = spo.extract_spo(sentence) or spo.SPO()
        label, certainty, modality_triggers = modality.detect_modality(
            sentence,
            factual=(is_opinion, opinion_conf, opinion_triggers),
            reported=triple.reported,
        )
        claims.append(
            ExtractedClaim(
                text=sentence.text,
                lang=doc.lang,  # TODO(Lot B): sentence.lang une fois le point L1 tranché
                span=(sentence.start, sentence.end),
                resolved_text=resolution.resolved_text,
                subject=triple.subject,
                predicate=triple.predicate,
                obj=triple.obj,
                source=triple.source,
                time=triple.time,
                location=triple.location,
                modality=label,
                certainty=certainty,
                is_opinion=is_opinion,
                confidence=max(triple.confidence, opinion_conf),
                parser=sentence.parser,
                triggers=opinion_triggers + modality_triggers,
                resolution_log=resolution.log,
            )
        )
    return claims


def extract_claims(doc: Document) -> list[Claim]:
    """Point d'entrée du Lot B (contrat partagé) : affirmations candidates à la vérification."""
    return [c.to_claim() for c in extract_claims_detailed(doc)]
