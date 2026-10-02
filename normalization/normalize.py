"""Lot A2 — Normalisation FR / AR / tunisien et identification de langue."""

from __future__ import annotations

import re
import unicodedata

from common.schemas import Document, Lang

_ARABIC_CHARS = re.compile(r"[؀-ۿ]")
_LATIN_CHARS = re.compile(r"[A-Za-zÀ-ÿ]")
_ARABIC_DIACRITICS = re.compile(r"[ً-ْـ]")  # harakat + tatweel
# Chiffres utilisés en arabizi pour des lettres arabes (3=ع, 7=ح, 9=ق, 5=خ, 2=ء)
_ARABIZI_HINT = re.compile(r"[a-z]+[235679][a-z]*|\b[235679][a-z]+", re.IGNORECASE)


def detect_script(text: str) -> str:
    """Retourne arabic | latin | arabizi | mixed."""
    n_ar = len(_ARABIC_CHARS.findall(text))
    n_lat = len(_LATIN_CHARS.findall(text))
    if n_ar and n_lat:
        return "mixed"
    if n_ar:
        return "arabic"
    if _ARABIZI_HINT.search(text):
        return "arabizi"
    return "latin"


def detect_language(text: str) -> Lang:
    """Identifie la langue (heuristique provisoire)."""
    # TODO(Lot A2): remplacer par fastText lid.176 + classifieur MSA vs tunisien.
    if not text.strip():
        return Lang.UNKNOWN
    script = detect_script(text)
    if script == "arabizi":
        return Lang.TN
    if script in ("arabic", "mixed"):
        return Lang.AR
    return Lang.FR


def normalize_arabic(text: str) -> str:
    """Supprime diacritiques/tatweel et unifie alef, ya, ta marbuta."""
    text = _ARABIC_DIACRITICS.sub("", text)
    text = re.sub("[إأآ]", "ا", text)
    return text.replace("ى", "ي").replace("ة", "ه")


def arabizi_to_arabic(text: str) -> str:
    """Translittération arabizi -> lettres arabes."""
    # TODO(Lot A2): implémenter (table de correspondance + désambiguïsation).
    return text


def normalize(text: str) -> Document:
    """Point d'entrée du Lot A2 utilisé par le pipeline."""
    raw = text
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    script = detect_script(text)
    lang = detect_language(text)
    if script in ("arabic", "mixed"):
        text = normalize_arabic(text)
    return Document(raw_text=raw, text=text, lang=lang, script=script)
