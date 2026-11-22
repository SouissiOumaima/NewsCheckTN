"""Lot A2 — Gold, EXP-A2-019 : accord entre annotateurs et contrôle de la référence adjugée.

Protocole : docs/lot-a2_protocole_gold.md, §8. Script prêt, à lancer par le responsable du lot
APRÈS les annotations. Il n'adjuge rien : il liste les numéros de ligne en désaccord (jamais de
texte) ; les décisions sont prises en séance par les deux annotateurs.

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_agreement accord --jeu test --out-dir <hors dépôt>
    python -X utf8 -m normalization.gold_agreement accord --jeu commun --out-dir <hors dépôt>
    python -X utf8 -m normalization.gold_agreement reference --fichier <référence adjugée>

Contrôles : nombre de lignes (300 pour le test, 160 pour les textes communs), mêmes textes dans
le même ordre chez les deux annotateurs (par empreintes), étiquettes parmi t / a / f / x.
Si une annotation contient encore des « ? », aucun kappa n'est calculé : « accord humain non
mesuré » (§8).
"""

from __future__ import annotations

import argparse
import random
from collections import Counter
from pathlib import Path

from normalization.annotation import cohen_kappa, read_annotations
from normalization.gold_common import (
    BOOTSTRAP_DRAWS,
    SEED,
    RefusGold,
    check_out_dir,
    check_sha,
    git_state,
    percentile_interval,
    proportion,
    safe_main,
    sha256_file,
    sha256_texts,
    write_json,
)
from normalization.gold_leakage import MODEL_TN, SETS

LABELS = ("t", "a", "f", "x")
PENDING = "?"
N_TEST, N_COMMON = 300, 160
TEST_LIST_SHA = SETS["test"][3]
TRAIN_LIST_SHA = SETS["entrainement"][3]
FILES = {
    "test": (MODEL_TN / "test_frozen_300_annotateur1.tsv",
             MODEL_TN / "test_frozen_300_annotateur2.tsv"),
    "commun": (MODEL_TN / "train_800_annotateur1.tsv", MODEL_TN / "train_160_annotateur2.tsv"),
}


# ---------------------------------------------------------------------------
# Contrôles
# ---------------------------------------------------------------------------

def check_rows(name: str, rows: list[tuple[str, str]], n: int) -> None:
    """Nombre de lignes exact et étiquettes connues (t, a, f, x ou « ? » en attente)."""
    if len(rows) != n:
        raise RefusGold(f"{name} : {len(rows)} lignes au lieu de {n}")
    bad = [i for i, (label, _) in enumerate(rows, 1) if label not in (*LABELS, PENDING)]
    if bad:
        raise RefusGold(f"{name} : {len(bad)} étiquettes invalides (lignes {bad[:20]})")


def check_same_texts(first: list[tuple[str, str]], second: list[tuple[str, str]]) -> None:
    """Les deux annotateurs ont les mêmes textes dans le même ordre (comparaison sans affichage)."""
    differ = [i for i, (a, b) in enumerate(zip(first, second, strict=True), 1) if a[1] != b[1]]
    if differ:
        raise RefusGold(f"textes différents entre annotateurs : {len(differ)} lignes"
                        f" (lignes {differ[:20]})")


def load_pair(jeu: str, path_1: Path, path_2: Path) -> tuple[list, list, dict]:
    """Charge et contrôle les deux annotations ; renvoie (ann. 1, ann. 2, empreintes)."""
    for path in (path_1, path_2):
        if not path.is_file():
            raise RefusGold(f"fichier absent : {path}")
    rows_1, rows_2 = read_annotations(path_1), read_annotations(path_2)
    if jeu == "test":
        check_rows("annotateur 1", rows_1, N_TEST)
        check_sha("liste du test", sha256_texts([t for _, t in rows_1]), TEST_LIST_SHA)
        check_rows("annotatrice 2", rows_2, N_TEST)
    else:
        check_rows("annotateur 1 (entraînement)", rows_1, 800)
        check_sha("liste de l'entraînement", sha256_texts([t for _, t in rows_1]), TRAIN_LIST_SHA)
        rows_1 = rows_1[:N_COMMON]
        check_rows("annotatrice 2", rows_2, N_COMMON)
    check_same_texts(rows_1, rows_2)
    digests = {"annotateur1": sha256_file(path_1), "annotatrice2": sha256_file(path_2)}
    return rows_1, rows_2, digests


# ---------------------------------------------------------------------------
# Accord
# ---------------------------------------------------------------------------

def kappa_bootstrap(first: list[str], second: list[str], draws: int = BOOTSTRAP_DRAWS,
                    seed: int = SEED) -> tuple[float, float]:
    """IC percentile 95 % du kappa de Cohen, par tirage des paires avec remise."""
    rng = random.Random(seed)
    n = len(first)
    values = []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        values.append(cohen_kappa([first[i] for i in idx], [second[i] for i in idx])[2])
    return percentile_interval(values)


def agreement(rows_1: list[tuple[str, str]], rows_2: list[tuple[str, str]],
              draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> tuple[dict, list[int]]:
    """(résultats en effectifs, numéros de ligne en désaccord). Aucun texte."""
    labels_1, labels_2 = [r[0] for r in rows_1], [r[0] for r in rows_2]
    pending = {"annotateur1": labels_1.count(PENDING), "annotatrice2": labels_2.count(PENDING)}
    result: dict = {"n": len(rows_1), "en_attente": pending,
                    "etiquettes_annotateur1": dict(Counter(labels_1)),
                    "etiquettes_annotatrice2": dict(Counter(labels_2))}
    if any(pending.values()):
        result["statut"] = "accord humain non mesuré (annotation incomplète, §8)"
        return result, []
    observed, expected, kappa = cohen_kappa(labels_1, labels_2)
    low, high = kappa_bootstrap(labels_1, labels_2, draws, seed)
    pairs = list(zip(labels_1, labels_2, strict=True))
    disagreements = [i for i, (a, b) in enumerate(pairs, 1) if a != b]
    result.update({
        "statut": "mesuré",
        "accord_brut": proportion(len(rows_1) - len(disagreements), len(rows_1)),
        "accord_attendu": round(expected, 4),
        "kappa": round(kappa, 4), "kappa_ic_bas": round(low, 4), "kappa_ic_haut": round(high, 4),
        "matrice": {f"{a}->{b}": c for (a, b), c in sorted(Counter(pairs).items())},
        "desaccords": len(disagreements),
    })
    return result, disagreements


def check_reference(path: Path) -> dict:
    """Référence adjugée du test : 300 lignes, mêmes textes, aucune étiquette « ? »."""
    if not path.is_file():
        raise RefusGold(f"fichier absent : {path}")
    rows = read_annotations(path)
    check_rows("référence", rows, N_TEST)
    check_sha("liste du test", sha256_texts([t for _, t in rows]), TEST_LIST_SHA)
    pending = sum(label == PENDING for label, _ in rows)
    if pending:
        raise RefusGold(f"référence incomplète : {pending} étiquettes « ? »")
    return {"n": len(rows), "sha256_fichier": sha256_file(path),
            "etiquettes": dict(Counter(label for label, _ in rows))}


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="commande", required=True)
    acc = commands.add_parser("accord", help="kappa et désaccords entre les deux annotateurs")
    acc.add_argument("--jeu", choices=sorted(FILES), required=True)
    acc.add_argument("--out-dir", type=Path, required=True,
                     help="dossier de sortie HORS du dépôt (obligatoire)")
    acc.add_argument("--annotateur1", type=Path)
    acc.add_argument("--annotatrice2", type=Path)
    ref = commands.add_parser("reference", help="contrôle et empreinte de la référence adjugée")
    ref.add_argument("--fichier", type=Path, required=True)
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.commande == "reference":
        result = check_reference(args.fichier)
        print(f"référence : {result['n']} lignes ; étiquettes {result['etiquettes']}")
        print(f"SHA-256 du fichier (à consigner dans EXP-A2-019) : {result['sha256_fichier']}")
        return
    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    path_1 = args.annotateur1 or FILES[args.jeu][0]
    path_2 = args.annotatrice2 or FILES[args.jeu][1]
    rows_1, rows_2, digests = load_pair(args.jeu, path_1, path_2)
    result, disagreements = agreement(rows_1, rows_2)
    payload = {"experience": "EXP-A2-019", "protocole": "docs/lot-a2_protocole_gold.md §8",
               "jeu": args.jeu, "graine": SEED, "tirages_bootstrap": BOOTSTRAP_DRAWS,
               "code": git_state(), "empreintes": digests, **result}
    print(f"== accord, jeu {args.jeu} : {result['n']} textes ; statut : {result['statut']} ==")
    print(f"  en attente (« ? ») : {result['en_attente']}")
    if result["statut"] == "mesuré":
        print(f"  kappa {result['kappa']} [{result['kappa_ic_bas']} ; {result['kappa_ic_haut']}]"
              f" ; accord brut {result['accord_brut']['taux']} ;"
              f" désaccords à adjuger {result['desaccords']}")
        print(f"  matrice : {result['matrice']}")
    print(f"JSON : {write_json(out_dir, f'lot-a2_gold_accord_{args.jeu}', payload)}")
    lines = write_json(out_dir, f"lot-a2_gold_desaccords_{args.jeu}",
                       {"experience": "EXP-A2-019", "jeu": args.jeu, "lignes": disagreements})
    print(f"Lignes en désaccord (fichier local, ne pas versionner) : {lines}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
