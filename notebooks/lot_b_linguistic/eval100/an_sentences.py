"""Phrases candidates tirées des comptes rendus intégraux de l'Assemblée nationale (DILA).

Source : jeu « Comptes rendus des Débats de l'Assemblée nationale » (data.gouv.fr, Licence
Ouverte / Open Licence), archives `AN_<année><numéro>.taz` de https://echanges.dila.gouv.fr/
OPENDATA/Debats/AN/. Lecture des archives en mémoire (aucune extraction sur disque).

Pour chaque intervention (`Para` hors sommaire) : texte sans l'orateur (`Orateur`) ni les
didascalies (`Italique`), découpé en phrases. Filtres neutres uniquement (aucune sélection par
contenu) : 6 à 40 mots ; pas de parenthèse, crochet ni chevron ; pas de nom d'orateur de la
séance ; pas de « M. » / « Mme » suivi d'un nom.

Usage :
    python -I an_sentences.py --archives-dir <dossier des .taz> --out <an_phrases.jsonl>
"""

from __future__ import annotations

import argparse
import io
import json
import re
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

MIN_WORDS, MAX_WORDS = 6, 40
SKIP_INLINE = {"Orateur", "Italique"}
_SENT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀÂÉÈÊÎÔÛÇ«])")
_CIVILITY = re.compile(r"\b(M\.|Mme|MM\.|Mmes)\s+[A-ZÀÂÉÈÊÎÔÛÇ]")
_NOT_SURNAMES = {"Président", "Madame", "Monsieur"}


def local(tag: str) -> str:
    return tag.split("}")[-1]


def para_text(para: ET.Element) -> str:
    parts = [para.text or ""]
    for child in para:
        if local(child.tag) not in SKIP_INLINE:
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    text = re.sub(r"\s+", " ", "".join(parts)).strip()
    return re.sub(r"^[\s.\-–—:,]+", "", text)  # ponctuation laissée par l'orateur retiré


def sentences_of(root: ET.Element) -> list[tuple[int, int, str]]:
    names = {re.sub(r"\s+", " ", "".join(n.itertext())).strip()
             for n in root.iter() if local(n.tag) == "Nom"}
    surnames = {w for n in names for w in n.split()
                if len(w) > 3 and w[:1].isupper() and w not in _NOT_SURNAMES}
    parents = {child: parent for parent in root.iter() for child in parent}
    out = []
    for k, para in enumerate(el for el in root.iter() if local(el.tag) == "Para"):
        parent = parents.get(para)
        if parent is None or local(parent.tag).startswith("Sommaire"):
            continue
        for j, sentence in enumerate(_SENT.split(para_text(para))):
            sentence = sentence.strip()
            if not MIN_WORDS <= len(sentence.split()) <= MAX_WORDS:
                continue
            if any(c in sentence for c in "()<>[]") or _CIVILITY.search(sentence):
                continue
            if any(re.search(rf"\b{re.escape(s)}\b", sentence) for s in surnames):
                continue
            out.append((k, j, sentence))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archives-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for archive in sorted(args.archives_dir.glob("AN_*.taz")):
        with tarfile.open(archive) as outer:
            inner_member = next(m for m in outer.getmembers() if m.isfile())
            inner = tarfile.open(fileobj=io.BytesIO(outer.extractfile(inner_member).read()))
            members = sorted((m for m in inner.getmembers() if m.isfile()), key=lambda m: m.name)
            for member in members:
                name = member.name.split("/")[-1]
                if not name.startswith("CRI_"):
                    continue
                root = ET.fromstring(inner.extractfile(member).read())
                seance = re.search(r"CRI_(\d{4})(\d{2})(\d{2})", name)
                day = "-".join(seance.groups()) if seance else None
                for k, j, sentence in sentences_of(root):
                    rows.append({"key": f"{archive.name}:{name}:{k}:{j}", "text": sentence,
                                 "archive": archive.name, "file": name, "date": day})
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} phrases candidates -> {args.out.name}")


if __name__ == "__main__":
    main()
