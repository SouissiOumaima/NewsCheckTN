"""Lot A2 — Modèle appris pour le tunisien en lettres arabes : tirage des jeux annotés.

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.model_tn_data draw    # tire les jeux à annoter (une fois)
    python -X utf8 -m normalization.model_tn_data kappa   # accord entre annotateurs, ensuite

Protocole : docs/lot-a2_modele_tn_protocole.md (commité AVANT tout entraînement).

Ce que fait `draw`, une seule fois :
- réserve = commentaires TSAC en lettres arabes, hors de TOUS les textes déjà annotés ;
- mélange avec une graine fixe propre à ce projet, puis découpe en deux jeux DISJOINTS :
  test gelé (300 textes) et entraînement (800 textes) ;
- écrit des fichiers d'annotation (étiquette « ? » à remplacer par t / a / f / x) :
  le test pour deux annotateurs, l'entraînement pour l'annotateur 1, et ses 160 premiers
  textes (20 %) pour l'annotateur 2 ;
- affiche l'empreinte SHA-256 de chaque liste de textes, à recopier dans le journal : elle
  prouve que le tirage n'a pas changé après coup.
Les fichiers vont dans data/interim/langid/model_tn/ : non versionnés (textes du corpus).
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from collections import Counter
from normalization.annotation import (
    SAMPLES,
    candidates,
    cohen_kappa,
    load_tsac,
    read_annotations,
    write_annotations,
)
from normalization.evaluate import REPO

INTERIM = REPO / "data" / "interim" / "langid"
OUT = INTERIM / "model_tn"
REFERENCES = [
    INTERIM / "tsac_arabic_sample_reference.tsv",
    INTERIM / "tsac_latin_sample_reference.tsv",
]

SEED = 20261107  # graine propre à ce projet (date du protocole), autre que celle d'annotation.py
N_TEST = 300
N_TRAIN = 800
N_TRAIN_DOUBLE = 160  # 20 % de l'entraînement annotés deux fois, pour mesurer l'accord

FILES = {
    "test_1": OUT / "test_frozen_300_annotateur1.tsv",
    "test_2": OUT / "test_frozen_300_annotateur2.tsv",
    "train_1": OUT / "train_800_annotateur1.tsv",
    "train_2": OUT / "train_160_annotateur2.tsv",
}


def split_pool(
    pool: list[str], seed: int, n_test: int, n_train: int
) -> tuple[list[str], list[str]]:
    """Mélange une copie de la réserve, puis renvoie (test, entraînement), disjoints."""
    if n_test + n_train > len(pool):
        raise ValueError(f"réserve trop petite : {len(pool)} textes pour {n_test + n_train}")
    shuffled = list(pool)
    random.Random(seed).shuffle(shuffled)
    return shuffled[:n_test], shuffled[n_test:n_test + n_train]


def fingerprint(texts: list[str]) -> str:
    """Empreinte SHA-256 d'une liste ordonnée de textes (une ligne par texte)."""
    return hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()


def annotated_texts() -> set[str]:
    """Tous les textes déjà annotés (échantillons et références) : exclus de la réserve."""
    paths = [*SAMPLES.values(), *REFERENCES]
    return {text for path in paths if path.exists() for _, text in read_annotations(path)}


def command_draw() -> None:
    existing = [str(p) for p in FILES.values() if p.exists()]
    if existing:  # un tirage ne se refait pas : sinon le test ne serait plus « gelé »
        sys.exit("ARRÊT : tirage déjà fait, fichiers présents : " + ", ".join(existing))

    annotated = annotated_texts()
    # dict.fromkeys : retire les doublons en gardant l'ordre (le tirage reste reproductible)
    pool = list(dict.fromkeys(t for t in candidates(load_tsac(), "arabic") if t not in annotated))
    test, train = split_pool(pool, SEED, N_TEST, N_TRAIN)
    assert not set(test) & set(train)  # garde-fou : aucun texte dans les deux jeux

    write_annotations(FILES["test_1"], [("?", t) for t in test])
    write_annotations(FILES["test_2"], [("?", t) for t in test])
    write_annotations(FILES["train_1"], [("?", t) for t in train])
    write_annotations(FILES["train_2"], [("?", t) for t in train[:N_TRAIN_DOUBLE]])

    print(f"réserve : {len(pool)} textes (lettres arabes, jamais annotés) ; graine {SEED}")
    print(f"test gelé : {len(test)} textes ; SHA-256 {fingerprint(test)}")
    print(f"entraînement : {len(train)} textes ; SHA-256 {fingerprint(train)}")
    for name, path in FILES.items():
        print(f"  {name:8} {path}")


def command_kappa() -> None:
    """Accord entre les deux annotateurs, sur le test et sur les 160 textes doublés."""
    for first, second in (("test_1", "test_2"), ("train_1", "train_2")):
        a, b = read_annotations(FILES[first]), read_annotations(FILES[second])
        pairs = [(la, lb) for (la, ta), (lb, tb) in zip(a, b, strict=False) if ta == tb]
        done = [(la, lb) for la, lb in pairs if la != "?" and lb != "?"]
        if not done:
            print(f"{first} / {second} : aucune paire annotée par les deux")
            continue
        observed, expected, kappa = cohen_kappa([x for x, _ in done], [y for _, y in done])
        disagreements = sum(x != y for x, y in done)
        print(f"{first} / {second} : {len(done)} paires ; accord {observed:.2f} ;"
              f" kappa {kappa:.2f} ; désaccords à adjuger {disagreements}")
        print("  étiquettes annotateur 1 :", dict(Counter(x for x, _ in done)))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # lettres arabes lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("draw", help="tire les jeux test (300) et entraînement (800), une fois")
    commands.add_parser("kappa", help="accord entre annotateurs après annotation")
    args = parser.parse_args()
    {"draw": command_draw, "kappa": command_kappa}[args.command]()


if __name__ == "__main__":
    main()
