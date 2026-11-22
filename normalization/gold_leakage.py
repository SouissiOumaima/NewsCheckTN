"""Lot A2 — Gold, EXP-A2-018 : audit des fuites entre jeux, par empreintes seulement.

Protocole : docs/lot-a2_protocole_gold.md, §7.

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_leakage --out-dir <dossier hors dépôt>

Deux empreintes SHA-256 par texte : texte brut sans espaces de bord, et texte normalisé
(`" ".join(normalize(texte).text.split())`). Résultats : doublons internes de chaque jeu et
intersections de chaque paire de jeux, en effectifs seulement. Les numéros de ligne concernés
vont dans un fichier séparé du dossier de sortie (hors dépôt), jamais à l'écran.

Règle du §7 : si le test gelé partage au moins un texte avec l'entraînement ou le dev, ces textes
sont retirés du test avant la mesure, par un avenant daté au protocole du modèle tunisien.
"""

from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
from pathlib import Path

from normalization.annotation import read_annotations
from normalization.evaluate import DEFAULT_DATASET, load_examples
from normalization.gold_common import (
    RefusGold,
    check_file,
    check_out_dir,
    check_sha,
    error_record,
    git_state,
    safe_main,
    sha256_texts,
    write_json,
)
from normalization.gold_robustness import DEV_SETS
from normalization.normalize import normalize
from normalization.review import INTERIM

MODEL_TN = INTERIM / "model_tn"
# Empreintes : listes ordonnées (protocole du modèle tunisien, tirage du 2026-11-07) et
# fichiers (EXP-A2-011). « liste » = SHA-256 de "\n".join(textes) ; « fichier » = des octets.
SETS = {
    "test": (MODEL_TN / "test_frozen_300_annotateur1.tsv", "annotation", "liste",
             "a579a57da9611c1218bcb24c3e78df6979c381e284ac25f8ccf9c9af37fdd252"),
    "entrainement": (MODEL_TN / "train_800_annotateur1.tsv", "annotation", "liste",
                     "5b4f40b94c7ac38ecae82afdf9ab76ea7cc1c478069db4dfdc0191bcd716b061"),
    "dev_arabe": (DEV_SETS["arabe"][0], "annotation", "fichier", DEV_SETS["arabe"][1]),
    "dev_latin": (DEV_SETS["latin"][0], "annotation", "fichier", DEV_SETS["latin"][1]),
    "eval_30": (DEFAULT_DATASET, "jsonl", "fichier",
                "1d0bcfaa4b2a01fbd428fb18240174e309ac9877dc474a4dc1399e15e9dd34ce"),
}
# Jeux dont un recouvrement avec le test impose un retrait (§7).
FORBIDDEN_WITH_TEST = ("entrainement", "dev_arabe", "dev_latin")


def read_texts(path: Path, kind: str) -> list[str]:
    """Textes d'un jeu, dans l'ordre du fichier, quelle que soit leur étiquette."""
    if kind == "annotation":
        return [text for _, text in read_annotations(path)]
    return [example["text"] for example in load_examples(path)]


def load_set(name: str, path: Path, kind: str, method: str, expected: str) -> tuple[list, str]:
    """Vérifie l'empreinte (fichier ou liste ordonnée) puis renvoie (textes, empreinte)."""
    if method == "fichier":
        return read_texts(path, kind), check_file(name, path, expected)
    if not path.is_file():
        raise RefusGold(f"fichier absent pour {name} : {path}")
    texts = read_texts(path, kind)
    digest = sha256_texts(texts)
    check_sha(name, digest, expected)
    return texts, digest


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprints(texts: list[str], dataset: str, errors: list[dict]) -> list[tuple[int, str, str]]:
    """(ligne, empreinte brute, empreinte normalisée) ; une erreur est notée sans texte."""
    out = []
    for number, text in enumerate(texts, 1):
        try:
            out.append((number, _sha(text.strip()), _sha(" ".join(normalize(text).text.split()))))
        except Exception as exc:
            errors.append(error_record(dataset, str(number), exc))
    return out


def internal_duplicates(prints: list[tuple[int, str, str]]) -> dict:
    """Textes en trop (effectif − empreintes distinctes), pour chaque type d'empreinte."""
    return {"n": len(prints),
            "doublons_bruts": len(prints) - len({p[1] for p in prints}),
            "doublons_normalises": len(prints) - len({p[2] for p in prints})}


def intersection(first: list[tuple[int, str, str]], second: list[tuple[int, str, str]]) -> dict:
    """Effectifs partagés entre deux jeux, et lignes concernées (fichier local seulement)."""
    result, lines = {}, {}
    for key, idx in (("brut", 1), ("normalise", 2)):
        other = {p[idx] for p in second}
        hits = [p for p in first if p[idx] in other]
        mine = {p[idx] for p in first}
        result[key] = {"textes_du_premier": len(hits), "empreintes_communes": len(mine & other)}
        lines[key] = {"premier": [p[0] for p in hits],
                      "second": [p[0] for p in second if p[idx] in mine]}
    return {"effectifs": result, "lignes": lines}


def audit(sets: dict[str, list[str]]) -> tuple[dict, dict]:
    """(résultats en effectifs, numéros de ligne) pour des jeux déjà chargés et vérifiés."""
    errors: list[dict] = []
    prints = {name: fingerprints(texts, name, errors) for name, texts in sets.items()}
    results = {"doublons_internes": {n: internal_duplicates(p) for n, p in prints.items()},
               "intersections": {}, "erreurs": errors}
    lines = {}
    for a, b in combinations(prints, 2):
        inter = intersection(prints[a], prints[b])
        results["intersections"][f"{a}|{b}"] = inter["effectifs"]
        lines[f"{a}|{b}"] = inter["lignes"]
    to_remove = lines_to_remove_from_test(lines)
    results["decision"] = {
        "textes_du_test_a_retirer": len(to_remove),
        "retrait_necessaire": bool(to_remove),
        "consigne": ("retirer ces textes du test AVANT la mesure, par un avenant daté au "
                     "protocole du modèle tunisien (§5)") if to_remove else "aucun retrait",
    }
    lines["test_a_retirer"] = sorted(to_remove)
    return results, lines


def lines_to_remove_from_test(lines: dict) -> set[int]:
    """Règle du §7 : lignes du test présentes (brut ou normalisé) dans l'entraînement ou le dev.

    Union : un texte présent à la fois dans l'entraînement et le dev n'est compté qu'une fois.
    Le test est le premier jeu de SETS, donc toujours « premier » dans les paires.
    """
    touched: set[int] = set()
    for other in FORBIDDEN_WITH_TEST:
        pair = lines.get(f"test|{other}", {})
        for kind in pair.values():
            touched.update(kind["premier"])
    return touched


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    for name, (path, *_rest) in SETS.items():
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, default=path, dest=name)
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    sets, digests = {}, {}
    for name, (_, kind, method, expected) in SETS.items():
        sets[name], digests[name] = load_set(name, getattr(args, name), kind, method, expected)
    results, lines = audit(sets)
    payload = {"experience": "EXP-A2-018", "protocole": "docs/lot-a2_protocole_gold.md §7",
               "code": git_state(), "empreintes": digests, **results}
    for name, dup in results["doublons_internes"].items():
        print(f"  {name:13} n={dup['n']:4} doublons bruts={dup['doublons_bruts']}"
              f" normalisés={dup['doublons_normalises']}")
    for pair, counts in results["intersections"].items():
        print(f"  {pair:24} brut={counts['brut']['empreintes_communes']}"
              f" normalisé={counts['normalise']['empreintes_communes']}")
    print(f"  décision : {results['decision']['consigne']}")
    print(f"  erreurs : {len(results['erreurs'])}")
    print(f"JSON : {write_json(out_dir, 'lot-a2_gold_fuites', payload)}")
    lines_path = write_json(out_dir, "lot-a2_gold_fuites_lignes", {"experience": "EXP-A2-018",
                                                                    "lignes": lines})
    print(f"Numéros de ligne (fichier local, ne pas versionner) : {lines_path}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
