"""Lot B — Segmentation et extraction d'affirmations candidates (SPO, modalité)."""

from __future__ import annotations

import re

from common.schemas import Claim, Document

_SENT_SPLIT = re.compile(r"(?<=[.!?؟])\s+")
_REPORTED = re.compile(r"\b(selon|d'après|aurait|auraient)\b|حسب|وفق", re.IGNORECASE)
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
    # TODO(Lot B): règles + traits morphologiques (mode, temps) via spaCy/Stanza.
    return "rapporté" if _REPORTED.search(sentence) else "assertif"


def extract_spo(sentence: str) -> tuple[str | None, str | None, str | None]:
    # TODO(Lot B): extraction sujet-prédicat-objet sur l'arbre de dépendances.
    return None, None, None


def extract_claims(doc: Document) -> list[Claim]:
    """Point d'entrée du Lot B : phrases candidates à la vérification."""
    # TODO(Lot B): coréférence pour rendre chaque affirmation autonome.
    claims = []
    for sentence, span in split_sentences(doc.text):
        if len(sentence.split()) < MIN_TOKENS:
            continue
        s, p, o = extract_spo(sentence)
        claims.append(
            Claim(
                text=sentence,
                lang=doc.lang,
                span=span,
                subject=s,
                predicate=p,
                obj=o,
                modality=detect_modality(sentence),
            )
        )
    return claims
