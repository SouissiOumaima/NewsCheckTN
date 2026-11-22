"""Lot A2 — Gold, EXP-A2-020 : prédiction LOCALE de la cascade (3 modèles entraînés sur Kaggle).

Protocole : docs/lot-a2_protocole_gold.md, §9. Les textes du test ne quittent pas le poste :
seul final_train.tsv est envoyé sur Kaggle (notebooks/lot_a2/marbert_final.ipynb).

Usage (lancé par le responsable du lot, une fois, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_predict_local --entrees <dossier gold_kaggle_inputs> \
        --resume <run_summary.json> --modele-graine1 <dossier> --modele-graine2 <dossier> \
        --modele-graine3 <dossier> --out-dir <hors dépôt>

Contrôles avant toute prédiction : configuration figée de run_summary.json (EXP-A2-015 et
avenant 2), empreinte de chaque fichier de chaque modèle, empreinte et effectif de chaque fichier
d'entrée (final_inputs.json), entraînement fait sur le même final_train.tsv.

Cascade (figée) : règles = tn -> tn ; sinon, texte consulté (règles = ar, écriture arabe ou
mixte) -> tn si la probabilité du modèle atteint 0.30, sinon ar ; sinon, la sortie des règles.
Test et presse : toute sortie autre que tn devient ar (binaire, comme gold_final).

torch et transformers ne sont importés qu'au chargement d'un modèle (jamais par normalize()) ;
ils ne figurent pas dans requirements.txt. Sorties : effectifs et empreintes, aucun texte.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from normalization.gold_common import (
    RefusGold,
    check_file,
    check_out_dir,
    git_state,
    safe_main,
    sha256_file,
    write_json,
)
from normalization.gold_kaggle_inputs import FILES

THRESHOLD = 0.30  # EXP-A2-015, figé
SEEDS = ("1", "2", "3")  # avenant 2 du protocole du modèle tunisien
EXPECTED_CONFIG = {"model": "UBC-NLP/MARBERTv2", "lr": 2e-5, "epochs": 4, "batch": 16,
                   "max_len": 128, "warmup": 0.1, "weight_decay": 0.01, "seeds": [1, 2, 3],
                   "seuil_cascade": THRESHOLD}
BINARY = {"test": True, "presse": True, "eval_30": False}
Scorer = Callable[[list[str]], list[float]]


# ---------------------------------------------------------------------------
# Contrôles
# ---------------------------------------------------------------------------

def check_summary(summary: dict, train_sha: str) -> None:
    """Configuration figée, graines 1 à 3, entraînement sur le même final_train.tsv."""
    config = summary.get("config", {})
    differ = sorted(k for k, v in EXPECTED_CONFIG.items() if config.get(k) != v)
    if differ:
        raise RefusGold(f"run_summary.json : configuration différente pour {differ}")
    if summary.get("entrainement", {}).get("sha256") != train_sha:
        raise RefusGold("run_summary.json : entraînement fait sur un autre final_train.tsv")
    if sorted(summary.get("modeles", {})) != list(SEEDS):
        raise RefusGold(f"run_summary.json : modèles attendus pour les graines {list(SEEDS)}")


def check_model_dir(seed: str, directory: Path, expected: dict[str, str]) -> None:
    """Chaque fichier du modèle a l'empreinte consignée ; aucun fichier en plus ni en moins."""
    if not directory.is_dir():
        raise RefusGold(f"dossier du modèle absent (graine {seed}) : {directory}")
    present = sorted(p.name for p in directory.iterdir() if p.is_file())
    if present != sorted(expected):
        raise RefusGold(f"graine {seed} : fichiers du modèle différents de run_summary.json")
    for name, digest in expected.items():
        check_file(f"modèle graine {seed}, {name}", directory / name, digest)


def load_inputs(folder: Path) -> tuple[dict, dict[str, list[tuple[int, str, int, str]]]]:
    """final_inputs.json, puis chaque fichier de prédiction vérifié (empreinte et effectif)."""
    info_path = folder / "final_inputs.json"
    if not info_path.is_file():
        raise RefusGold(f"final_inputs.json absent : {info_path}")
    info = json.loads(info_path.read_text(encoding="utf-8"))["fichiers"]
    sets = {}
    for name in ("test", "eval_30", "presse"):
        if name not in info:
            continue  # presse non mesurée
        path = folder / FILES[name]
        check_file(name, path, info[name]["sha256"])
        rows = read_rows(name, path)
        if len(rows) != info[name]["n"]:
            raise RefusGold(f"{name} : {len(rows)} lignes au lieu de {info[name]['n']}")
        sets[name] = rows
    return info, sets


def read_rows(name: str, path: Path) -> list[tuple[int, str, int, str]]:
    """(numero, regles, consulte, texte) ; en-tête vérifié ; erreurs sans texte."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "numero\tregles\tconsulte\ttext":
        raise RefusGold(f"{name} : en-tête inattendu")
    rows = []
    for number, line in enumerate(lines[1:], 2):
        parts = line.split("\t", 3)
        if len(parts) != 4 or not parts[0].isdigit() or parts[2] not in ("0", "1"):
            raise RefusGold(f"{name} : ligne {number} mal formée")
        rows.append((int(parts[0]), parts[1], int(parts[2]), parts[3]))
    return rows


# ---------------------------------------------------------------------------
# Cascade
# ---------------------------------------------------------------------------

def cascade_label(rules: str, consulted: int, prob: float | None, binary: bool) -> str:
    """Règle tn -> tn ; consulté -> seuil 0.30 ; sinon règles ; binaire : non-tn -> ar."""
    if rules == "tn":
        label = "tn"
    elif consulted:
        if prob is None:
            raise ValueError("probabilité manquante pour un texte consulté")
        label = "tn" if prob >= THRESHOLD else "ar"
    else:
        label = rules
    return "ar" if binary and label != "tn" else label


def predict_set(rows: list[tuple[int, str, int, str]], scorer: Scorer, binary: bool) -> list[str]:
    """Le modèle n'est appelé que sur les textes consultés."""
    consulted = [r for r in rows if r[2] == 1]
    probs = dict(zip((r[0] for r in consulted), scorer([r[3] for r in consulted]), strict=True))
    return [cascade_label(r[1], r[2], probs.get(r[0]), binary) for r in rows]


def write_predictions(path: Path, rows: list[tuple[int, str, int, str]],
                      labels: list[str]) -> None:
    """« numéro<TAB>étiquette », format de gold_final ; refuse d'écraser."""
    if path.exists():
        raise RefusGold(f"{path.name} existe déjà : les prédictions ne se refont pas")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.writelines(f"{r[0]}\t{label}\n" for r, label in zip(rows, labels, strict=True))


def predict_all(sets: dict, scorers: dict[str, Scorer], out_dir: Path) -> dict:
    """Toutes les graines et tous les jeux ; renvoie chemins, empreintes et effectifs."""
    result: dict = {}
    for seed, scorer in scorers.items():
        result[seed] = {}
        for name, rows in sets.items():
            labels = predict_set(rows, scorer, BINARY[name])
            path = out_dir / f"predictions_{name}_graine{seed}.tsv"
            write_predictions(path, rows, labels)
            if len(path.read_text(encoding="utf-8").splitlines()) != len(rows):
                raise RefusGold(f"{path.name} : nombre de lignes incorrect")
            result[seed][name] = {"chemin": str(path), "sha256": sha256_file(path),
                                  "n": len(rows), "tn": labels.count("tn")}
    return result


# ---------------------------------------------------------------------------
# Modèle (import paresseux)
# ---------------------------------------------------------------------------

def load_scorer(directory: Path, max_len: int = 128, batch: int = 16) -> Scorer:
    """Probabilité de la classe tn ; fichiers locaux seulement (aucun téléchargement)."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(directory, local_files_only=True)
    model.eval()

    def score(texts: list[str]) -> list[float]:
        out: list[float] = []
        for start in range(0, len(texts), batch):
            enc = tokenizer(texts[start:start + batch], truncation=True, max_length=max_len,
                            padding=True, return_tensors="pt")
            with torch.no_grad():
                logits = model(**enc).logits
            out += torch.softmax(logits.float(), dim=-1)[:, 1].tolist()
        return out

    return score


# ---------------------------------------------------------------------------
# Commande
# ---------------------------------------------------------------------------

def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entrees", type=Path, required=True)
    parser.add_argument("--resume", type=Path, required=True, help="run_summary.json (Kaggle)")
    for seed in SEEDS:
        parser.add_argument(f"--modele-graine{seed}", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    args = parser.parse_args(argv)

    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    info, sets = load_inputs(args.entrees)
    if not args.resume.is_file():
        raise RefusGold(f"run_summary.json absent : {args.resume}")
    summary = json.loads(args.resume.read_text(encoding="utf-8"))
    check_summary(summary, info["entrainement"]["sha256"])
    dirs = {s: getattr(args, f"modele_graine{s}") for s in SEEDS}
    for seed, directory in dirs.items():
        check_model_dir(seed, directory, summary["modeles"][seed]["fichiers"])
    scorers = {seed: load_scorer(directory) for seed, directory in dirs.items()}

    result = predict_all(sets, scorers, out_dir)
    for seed, by_set in result.items():
        for name, entry in by_set.items():
            print(f"  graine {seed} {name:8} n={entry['n']:4} tn={entry['tn']:4}"
                  f" SHA-256 {entry['sha256']}")
    payload = {"experience": "EXP-A2-020", "code": git_state(), "seuil": THRESHOLD,
               "run_summary_sha256": sha256_file(args.resume),
               "entrees": {k: v["sha256"] for k, v in info.items()}, "predictions": result}
    print(f"JSON (à reporter dans le manifeste) : "
          f"{write_json(out_dir, 'lot-a2_gold_predictions', payload)}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
