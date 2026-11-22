"""Lot A2 — Gold, EXP-A2-020 : fichiers d'entrée de l'entraînement final et de la prédiction.

Protocole : docs/lot-a2_protocole_gold.md, §9 ; cascade figée d'EXP-A2-015.

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_kaggle_inputs --out-dir <hors dépôt> \
        [--presse <échantillon> --presse-sha256 <empreinte>]

Écrit, hors dépôt :
- final_train.tsv  (label, lex, text) : SEUL fichier envoyé sur Kaggle ; 800 textes t / a de
  l'entraînement ; label 1 = t, 0 = a ; lex = 1 si le pipeline actuel dit déjà `tn` (même
  calcul que pour EXP-A2-015) ;
- final_test.tsv, final_eval30.tsv, final_presse.tsv (numero, regles, consulte, text) : restent
  en local (prédiction locale, gold_predict_local) ; le test n'a AUCUNE étiquette ;
  regles = normalize(texte).lang ; consulte = 1 si regles == "ar" et écriture arabe ou mixte
  (seuls ces textes sont soumis au modèle) ;
- final_inputs.json : effectifs et SHA-256 de chaque fichier.
Aucun texte affiché.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from normalization.annotation import read_annotations
from normalization.evaluate import DEFAULT_DATASET, load_examples
from normalization.gold_common import (
    RefusGold,
    check_file,
    check_out_dir,
    check_sha,
    git_state,
    safe_main,
    sha256_file,
    sha256_texts,
)
from normalization.gold_leakage import SETS
from normalization.normalize import normalize

N_TRAIN = 800
CONSULTED_SCRIPTS = ("arabic", "mixed")  # choix validé le 2026-11-22, à documenter (EXP-A2-020)
FILES = {"entrainement": "final_train.tsv", "test": "final_test.tsv",
         "eval_30": "final_eval30.tsv", "presse": "final_presse.tsv"}


def check_text(dataset: str, number: int, text: str) -> None:
    """Un texte doit tenir sur une ligne, sans tabulation (sinon les colonnes se décalent)."""
    if "\t" in text or len(text.splitlines()) > 1:
        raise RefusGold(f"{dataset} : ligne {number} contient une tabulation ou un saut de ligne")


def train_rows(rows: list[tuple[str, str]]) -> list[tuple[int, int, str]]:
    """(label, lex, texte) des textes t / a ; f et x exclus (protocole du modèle tunisien, §3)."""
    out = []
    for number, (label, text) in enumerate(rows, 1):
        if label not in ("t", "a"):
            continue
        check_text("entraînement", number, text)
        lex = int(normalize(text).lang.value == "tn")
        out.append((1 if label == "t" else 0, lex, text))
    return out


def prediction_rows(dataset: str, texts: list[str]) -> list[tuple[int, str, int, str]]:
    """(numero, regles, consulte, texte) ; numéros 1..n dans l'ordre du jeu."""
    out = []
    for number, text in enumerate(texts, 1):
        check_text(dataset, number, text)
        doc = normalize(text)
        consulted = int(doc.lang.value == "ar" and doc.script in CONSULTED_SCRIPTS)
        out.append((number, doc.lang.value, consulted, text))
    return out


def write_tsv(path: Path, header: list[str], rows: list[tuple]) -> None:
    """Écrit un TSV ; refuse d'écraser un fichier existant (les entrées sont figées)."""
    if path.exists():
        raise RefusGold(f"{path.name} existe déjà : les entrées ne se refont pas")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\t".join(header) + "\n")
        handle.writelines("\t".join(str(v) for v in row) + "\n" for row in rows)


def build(train: list[tuple[str, str]], test_texts: list[str], eval_texts: list[str],
          press_texts: list[str] | None, out_dir: Path) -> dict:
    """Écrit les fichiers et renvoie le résumé (effectifs et empreintes, aucun texte)."""
    kept = train_rows(train)
    if len(kept) != N_TRAIN:
        raise RefusGold(f"entraînement : {len(kept)} textes t / a au lieu de {N_TRAIN}")
    summary: dict = {}
    path = out_dir / FILES["entrainement"]
    write_tsv(path, ["label", "lex", "text"], kept)
    summary["entrainement"] = {"fichier": path.name, "n": len(kept),
                               "t": sum(r[0] for r in kept), "lex": sum(r[1] for r in kept),
                               "sha256": sha256_file(path)}
    sets = {"test": test_texts, "eval_30": eval_texts}
    if press_texts is not None:
        sets["presse"] = press_texts
    for name, texts in sets.items():
        rows = prediction_rows(name, texts)
        path = out_dir / FILES[name]
        write_tsv(path, ["numero", "regles", "consulte", "text"], rows)
        summary[name] = {"fichier": path.name, "n": len(rows),
                         "regles_tn": sum(r[1] == "tn" for r in rows),
                         "consultes": sum(r[2] for r in rows), "sha256": sha256_file(path)}
    return summary


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    parser.add_argument("--entrainement", type=Path, default=SETS["entrainement"][0])
    parser.add_argument("--test", type=Path, default=SETS["test"][0])
    parser.add_argument("--presse", type=Path, help="échantillon tiré par gold_presse")
    parser.add_argument("--presse-sha256", help="empreinte de l'échantillon (gold_presse)")
    args = parser.parse_args(argv)
    if (args.presse is None) != (args.presse_sha256 is None):
        raise RefusGold("--presse et --presse-sha256 vont ensemble")

    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    inputs_json = out_dir / "final_inputs.json"
    if inputs_json.exists():
        raise RefusGold("final_inputs.json existe déjà : les entrées ne se refont pas")
    for name, path in (("entraînement", args.entrainement), ("test", args.test)):
        if not path.is_file():
            raise RefusGold(f"fichier absent pour {name} : {path}")
    train = read_annotations(args.entrainement)
    check_sha("liste de l'entraînement", sha256_texts([t for _, t in train]),
              SETS["entrainement"][3])
    test_texts = [t for _, t in read_annotations(args.test)]  # étiquettes jamais lues ensuite
    check_sha("liste du test", sha256_texts(test_texts), SETS["test"][3])
    check_file("eval_30", DEFAULT_DATASET, SETS["eval_30"][3])
    eval_texts = [e["text"] for e in load_examples(DEFAULT_DATASET)]
    press_texts = None
    if args.presse:
        check_file("presse", args.presse, args.presse_sha256)
        press_texts = [s for s in args.presse.read_text(encoding="utf-8-sig").splitlines()
                       if s.strip()]

    summary = build(train, test_texts, eval_texts, press_texts, out_dir)
    for name, info in summary.items():
        extra = (f"t {info['t']} lex {info['lex']}" if name == "entrainement"
                 else f"règles tn {info['regles_tn']} consultés {info['consultes']}")
        print(f"  {info['fichier']:18} n={info['n']:4} {extra} ; SHA-256 {info['sha256']}")
    payload = {"experience": "EXP-A2-020", "code": git_state(), "fichiers": summary,
               "consulte": {"regles": "ar", "ecritures": list(CONSULTED_SCRIPTS)}}
    inputs_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON : {inputs_json}")
    print("Sur Kaggle : envoyer final_train.tsv et final_inputs.json SEULEMENT.")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
