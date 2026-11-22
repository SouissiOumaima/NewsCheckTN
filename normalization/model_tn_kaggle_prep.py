"""Lot A2 — EXP-A2-015 : préparation versionnée de kaggle_train.tsv (colonnes label, lex, text).

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.model_tn_kaggle_prep --sortie <fichier .tsv>

Entrée : data/interim/langid/model_tn/train_800_annotateur1.tsv (« étiquette TAB texte »),
vérifiée par l'empreinte de la liste ordonnée des 800 textes (tirage du 2026-11-07).
Sortie : en-tête « label\tlex\ttext », puis une ligne par texte `t` ou `a` (protocole §3 :
`f` et `x` exclus) ; label = 1 pour `t`, 0 pour `a` ; lex = 1 si le pipeline actuel dit déjà
`tn` (normalize(texte).lang), texte brut inchangé ; fins de ligne « \n ».

Même calcul que pour EXP-A2-015 : l'empreinte de la sortie doit être celle du fichier envoyé
sur Kaggle (39a3643b…). Le script n'affiche que le nombre de lignes et le SHA-256 de la sortie ;
en cas d'erreur, jamais le contenu d'une ligne.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from normalization.annotation import read_annotations
from normalization.evaluate import REPO
from normalization.model_tn_data import FILES, fingerprint
from normalization.normalize import normalize

TRAIN_LIST_SHA = "5b4f40b94c7ac38ecae82afdf9ab76ea7cc1c478069db4dfdc0191bcd716b061"
N_TRAIN = 800
HEADER = "label\tlex\ttext\n"


class Refus(Exception):
    """Refus volontaire ; message écrit par nous, sans texte du corpus."""


def kaggle_rows(rows: list[tuple[str, str]]) -> list[tuple[int, int, str]]:
    """(label, lex, texte) des textes `t` / `a`, dans l'ordre du fichier."""
    out = []
    for number, (label, text) in enumerate(rows, 1):
        if label not in ("t", "a"):
            continue
        if "\t" in text or len(text.splitlines()) > 1:
            raise Refus(f"ligne {number} : tabulation ou saut de ligne dans le texte")
        out.append((1 if label == "t" else 0, int(normalize(text).lang.value == "tn"), text))
    return out


def render(rows: list[tuple[int, int, str]]) -> str:
    """Contenu exact du fichier : en-tête puis « label TAB lex TAB texte »."""
    return HEADER + "".join(f"{label}\t{lex}\t{text}\n" for label, lex, text in rows)


def check_output(path: Path, repo: Path = REPO) -> Path:
    """Refuse d'écraser, et refuse un chemin du dépôt qui ne serait pas ignoré par Git."""
    resolved = path.expanduser().resolve()
    if resolved.exists():
        raise Refus(f"{resolved.name} existe déjà : je ne l'écrase pas")
    if resolved.is_relative_to(repo.resolve()):
        ignored = subprocess.run(["git", "check-ignore", "-q", str(resolved)], cwd=repo,
                                 check=False).returncode == 0
        if not ignored:
            raise Refus("la sortie serait versionnée : choisir un chemin ignoré par Git (data/)")
    return resolved


def prepare(source: Path, output: Path, expected: str = TRAIN_LIST_SHA,
            n_expected: int = N_TRAIN) -> tuple[int, str]:
    """Contrôle l'entrée, écrit la sortie ; renvoie (nombre de lignes de données, SHA-256)."""
    if not source.is_file():
        raise Refus(f"fichier d'entrée absent : {source}")
    rows = read_annotations(source)
    if fingerprint([text for _, text in rows]) != expected:
        raise Refus("empreinte de la liste ordonnée différente du tirage du 2026-11-07")
    kept = kaggle_rows(rows)
    if len(kept) != n_expected:
        raise Refus(f"{len(kept)} textes t / a au lieu de {n_expected}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(kept))
    return len(kept), hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entree", type=Path, default=FILES["train_1"])
    parser.add_argument("--sortie", type=Path, required=True,
                        help="fichier à créer (jamais écrasé ; chemin ignoré par Git)")
    args = parser.parse_args()
    try:
        n, digest = prepare(args.entree, check_output(args.sortie))
    except Refus as refus:
        print(f"REFUS : {refus}")
        raise SystemExit(2) from None
    except Exception as exc:  # le message peut contenir un texte : jamais affiché
        print(f"ERREUR : {type(exc).__name__} ; message masqué")
        raise SystemExit(1) from None
    print(f"lignes de données : {n} ; SHA-256 de la sortie : {digest}")


if __name__ == "__main__":
    main()
