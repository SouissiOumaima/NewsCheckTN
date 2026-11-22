"""Lot A2 — Outils communs aux scripts du palier Gold (docs/lot-a2_protocole_gold.md).

Contenu : intervalle de Wilson, règle de décision du §5, bootstrap apparié, empreintes SHA-256,
contrôle du dossier de sortie, écriture du JSON, gestion d'erreurs sans texte.

Règle de sortie, valable pour tous les scripts Gold : on n'affiche et on n'écrit que des
effectifs, des taux, des intervalles et des empreintes. Jamais le contenu d'une ligne, même en
cas d'erreur : une exception est réduite à son type et à un numéro de ligne.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
import sys
import traceback
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from normalization.evaluate import REPO, scores

Z_95 = 1.959964  # quantile de la loi normale pour un intervalle à 95 %
BOOTSTRAP_DRAWS = 1000  # §1 du protocole Gold
SEED = 20261122  # §1 du protocole Gold


class RefusGold(Exception):
    """Refus volontaire (empreinte, dossier, préconditions). Message écrit par nous, sans texte."""


# ---------------------------------------------------------------------------
# Statistiques
# ---------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalle de Wilson d'une proportion k / n (n = 0 : on ne sait rien, [0 ; 1])."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def decision_inv(k: int, n: int) -> str:
    """Règle du §5 : indéterminé si n < 30 ; robuste si haute ≤ 0.05 ; fragile si basse > 0.02."""
    if n < 30:
        return "indéterminé"
    low, high = wilson(k, n)
    if high <= 0.05:
        return "robuste"
    if low > 0.02:
        return "fragile"
    return "indéterminé"


def proportion(k: int, n: int) -> dict:
    """Effectif, compte, taux et intervalle de Wilson, arrondis pour le JSON."""
    low, high = wilson(k, n)
    return {"n": n, "k": k, "taux": round(k / n, 4) if n else None,
            "wilson_bas": round(low, 4), "wilson_haut": round(high, 4)}


def _metrics(golds: Sequence[str], predictions: Sequence[str]) -> tuple[float, float]:
    """(exactitude, macro-F1) avec la fonction de score d'EXP-A2-011."""
    result = scores([{"lang": g} for g in golds], list(predictions), "lang")
    return result["accuracy"], result["macro_f1"]


def paired_bootstrap(golds: Sequence[str], before: Sequence[str], after: Sequence[str],
                     draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> dict:
    """Exactitude et macro-F1 avant / après, et écart (après − avant) avec IC percentile 95 %.

    Apparié : chaque tirage reprend les mêmes textes pour « avant » et « après ».
    """
    n = len(golds)
    if not (n == len(before) == len(after)) or n == 0:
        raise ValueError("listes vides ou de longueurs différentes")
    acc_b, f1_b = _metrics(golds, before)
    acc_a, f1_a = _metrics(golds, after)
    rng = random.Random(seed)
    diffs_acc, diffs_f1 = [], []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        g = [golds[i] for i in idx]
        ab, fb = _metrics(g, [before[i] for i in idx])
        aa, fa = _metrics(g, [after[i] for i in idx])
        diffs_acc.append(aa - ab)
        diffs_f1.append(fa - fb)
    return {
        "n": n,
        "exactitude": _summary(acc_b, acc_a, diffs_acc),
        "macro_f1": _summary(f1_b, f1_a, diffs_f1),
    }


def percentile_interval(values: Sequence[float]) -> tuple[float, float]:
    """Bornes 2.5 % et 97.5 % (méthode percentile, sans interpolation)."""
    ordered = sorted(values)
    last = len(ordered) - 1
    return ordered[round(0.025 * last)], ordered[round(0.975 * last)]


def _summary(before: float, after: float, diffs: list[float]) -> dict:
    low, high = percentile_interval(diffs)
    return {"avant": round(before, 4), "apres": round(after, 4),
            "ecart": round(after - before, 4), "ic_bas": round(low, 4), "ic_haut": round(high, 4)}


# ---------------------------------------------------------------------------
# Empreintes
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Empreinte des octets du fichier (méthode d'EXP-A2-011)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_texts(texts: Sequence[str]) -> str:
    """Empreinte d'une liste ordonnée de textes (méthode de normalization.model_tn_data)."""
    return hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()


def check_sha(name: str, actual: str, expected: str) -> None:
    """Refuse de continuer si l'empreinte ne correspond pas."""
    if actual != expected:
        raise RefusGold(f"empreinte différente pour {name} : attendu {expected}, obtenu {actual}")


def check_file(name: str, path: Path, expected: str) -> str:
    """Vérifie l'existence puis l'empreinte d'un fichier ; renvoie l'empreinte."""
    if not path.is_file():
        raise RefusGold(f"fichier absent pour {name} : {path}")
    digest = sha256_file(path)
    check_sha(name, digest, expected)
    return digest


# ---------------------------------------------------------------------------
# Sorties
# ---------------------------------------------------------------------------

def check_out_dir(path: Path, repo: Path = REPO) -> Path:
    """Le dossier de sortie doit être hors du dépôt (y compris data/) ; il est créé ensuite."""
    resolved = path.expanduser().resolve()
    if resolved == repo.resolve() or resolved.is_relative_to(repo.resolve()):
        raise RefusGold(f"--out-dir est dans le dépôt ({resolved}) : choisir un dossier hors dépôt")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def git_state(repo: Path = REPO) -> dict:
    """Commit courant et état de l'arbre de travail, pour la reproductibilité."""
    def run(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=repo,
                              check=False).stdout.strip()
    return {"commit": run("rev-parse", "--short", "HEAD") or "inconnu",
            "arbre_propre": run("status", "--porcelain", "--", "normalization") == ""}


def write_json(out_dir: Path, stem: str, payload: dict) -> Path:
    """Écrit le JSON de résultats daté dans le dossier (déjà contrôlé) ; renvoie son chemin."""
    path = out_dir / f"{stem}_{date.today():%Y%m%d}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Erreurs sans texte
# ---------------------------------------------------------------------------

def error_record(dataset: str, line: str, exc: BaseException) -> dict:
    """Trace d'une erreur sur un texte : jeu, numéro de ligne, type. Jamais le message."""
    return {"jeu": dataset, "ligne": line, "type": type(exc).__name__}


def _where(exc: BaseException) -> str:
    """Dernier endroit de notre code (fichier et ligne) où l'exception est passée."""
    frames = traceback.extract_tb(exc.__traceback__)
    ours = [f for f in frames if "normalization" in Path(f.filename).parts] or frames
    if not ours:
        return "lieu inconnu"
    return f"{Path(ours[-1].filename).name}, ligne {ours[-1].lineno}"


def safe_main(run: Callable[[], None]) -> None:
    """Lance `run` ; en cas d'échec, n'affiche que le type d'erreur et le lieu, jamais le message.

    Le message d'une exception peut contenir un texte du corpus : il n'est jamais affiché.
    Seuls les refus (RefusGold), rédigés par nous sans texte, ont leur message affiché.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        run()
    except RefusGold as refus:
        print(f"REFUS : {refus}")
        raise SystemExit(2) from None
    except Exception as exc:  # on veut tout attraper, sans rien laisser fuir
        print(f"ERREUR : {type(exc).__name__} ({_where(exc)}) ; message masqué (peut contenir"
              " un texte)")
        raise SystemExit(1) from None
