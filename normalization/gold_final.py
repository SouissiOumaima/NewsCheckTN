"""Lot A2 — Gold, EXP-A2-020 : mesure unique de la cascade sur le test gelé (script NON lancé).

Protocole : docs/lot-a2_protocole_gold.md, §9 ; critères : docs/lot-a2_modele_tn_protocole.md, §4.

Usage (une seule fois, par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_final --manifeste <manifeste.json> --out-dir <hors dépôt>

Aucune option de seuil, de modèle ni de jeu : tout vient du manifeste, écrit et consigné AVANT
la mesure (chemins et empreintes SHA-256 seulement). Format du manifeste :
    {
      "reference_test": {"chemin": "...tsv", "sha256": "..."},
      "statut_reference": "adjugee" | "annotateur1_seul",
      "graines": {"1": {"test": {"chemin", "sha256"}, "eval_30": {...}, "presse": {...}},
                  "2": {...}, "3": {...}},
      "presse": {"chemin": "...txt", "sha256": "...", "annee": 2024, "url": "...",
                 "sha256_archive": "..."}   ou   null (critère « non mesuré »)
    }
Fichiers de prédictions (écrits par l'entraînement final, une fois) : une ligne par texte,
« numéro<TAB>étiquette », numéros 1..N dans l'ordre du jeu ; étiquettes tn / ar pour le test et
la presse, fr / ar / tn pour eval_30. Presse : une phrase par ligne (UTF-8).

Le script refuse de tourner si une empreinte ne correspond pas, et refuse un 2e passage dans le
même dossier de sortie sans --deuxieme-passage (le passage est alors déclaré comme tel).
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from datetime import datetime
from pathlib import Path

from common.schemas import Lang
from normalization.annotation import read_annotations
from normalization.evaluate import DEFAULT_DATASET, load_examples, scores
from normalization.gold_common import (
    BOOTSTRAP_DRAWS,
    SEED,
    RefusGold,
    check_file,
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
from normalization.gold_leakage import SETS
from normalization.normalize import detect_language, normalize

TEST_LIST_SHA = SETS["test"][3]
EVAL30_SHA = SETS["eval_30"][3]
SEEDS = ("1", "2", "3")  # avenant 2 du protocole du modèle tunisien
N_TEST = 300
# Critères du protocole du modèle tunisien (§4), recopiés sans changement.
MIN_RECALL_TN = 0.70
MIN_PRECISION_TN = 0.90
MAX_FALSE_ALARMS = 0.01
EVAL30_MACRO_F1_PROTOCOLE = 0.94
LOCK_NAME = "lot-a2_gold_final_passage.json"


# ---------------------------------------------------------------------------
# Lecture contrôlée
# ---------------------------------------------------------------------------

def load_reference(path: Path, expected: str, list_sha: str = TEST_LIST_SHA,
                   n: int = N_TEST) -> list[tuple[str, str]]:
    """Référence du test : empreintes (fichier et liste ordonnée), n lignes, aucun « ? »."""
    check_file("référence du test", path, expected)
    rows = read_annotations(path)
    if len(rows) != n:
        raise RefusGold(f"référence : {len(rows)} lignes au lieu de {n}")
    check_sha("liste du test", sha256_texts([t for _, t in rows]), list_sha)
    bad = [i for i, (label, _) in enumerate(rows, 1) if label not in ("t", "a", "f", "x")]
    if bad:
        raise RefusGold(f"référence : {len(bad)} étiquettes invalides ou « ? » (lignes {bad[:20]})")
    return rows


def load_predictions(name: str, entry: dict, n: int, allowed: set[str]) -> list[str]:
    """Prédictions « numéro<TAB>étiquette », numéros 1..n tous présents, étiquettes autorisées."""
    path = Path(entry["chemin"])
    check_file(name, path, entry["sha256"])
    labels: dict[int, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2 or not parts[0].strip().isdigit():
            raise RefusGold(f"{name} : ligne {number} mal formée")
        labels[int(parts[0])] = parts[1].strip()
    if sorted(labels) != list(range(1, n + 1)):
        raise RefusGold(f"{name} : {len(labels)} numéros au lieu de 1..{n}")
    bad = sorted(i for i, label in labels.items() if label not in allowed)
    if bad:
        raise RefusGold(f"{name} : {len(bad)} étiquettes non autorisées (lignes {bad[:20]})")
    return [labels[i] for i in range(1, n + 1)]


def load_press(entry: dict) -> list[str]:
    path = Path(entry["chemin"])
    check_file("presse neuve", path, entry["sha256"])
    return [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

def binary_scores(golds: list[str], preds: list[str]) -> dict:
    """Rappel et précision de « tn » (classe positive) ; comptes inclus."""
    tp = sum(g == p == "tn" for g, p in zip(golds, preds, strict=True))
    predicted = sum(p == "tn" for p in preds)
    support = sum(g == "tn" for g in golds)
    return {"vp": tp, "predits_tn": predicted, "support_tn": support,
            "rappel_tn": tp / support if support else 0.0,
            "precision_tn": tp / predicted if predicted else 0.0}


def binary_bootstrap(golds: list[str], preds: list[str], draws: int = BOOTSTRAP_DRAWS,
                     seed: int = SEED) -> dict:
    """IC percentile 95 % du rappel et de la précision tn."""
    rng = random.Random(seed)
    n = len(golds)
    recalls, precisions = [], []
    for _ in range(draws):
        idx = [rng.randrange(n) for _ in range(n)]
        s = binary_scores([golds[i] for i in idx], [preds[i] for i in idx])
        recalls.append(s["rappel_tn"])
        precisions.append(s["precision_tn"])
    r_low, r_high = percentile_interval(recalls)
    p_low, p_high = percentile_interval(precisions)
    return {"rappel_ic": [round(r_low, 4), round(r_high, 4)],
            "precision_ic": [round(p_low, 4), round(p_high, 4)]}


def reference_view(rows: list[tuple[str, str]]) -> tuple[list[int], list[str]]:
    """Indices (0-based) et étiquettes des textes t / a (f et x exclus, protocole §3)."""
    kept = [i for i, (label, _) in enumerate(rows) if label in ("t", "a")]
    return kept, ["tn" if rows[i][0] == "t" else "ar" for i in kept]


def rules_binary(text: str) -> str:
    """Baseline « lexique seul » : le pipeline actuel, ramené à tn / non-tn."""
    return "tn" if detect_language(text) == Lang.TN else "ar"


def mean_sd(values: list[float]) -> dict:
    return {"moyenne": round(statistics.mean(values), 4),
            "ecart_type": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0}


def criteria(test_rows: list[tuple[str, str]], test_preds: dict[str, list[str]],
             eval_examples: list[dict], eval_preds: dict[str, list[str]],
             press_texts: list[str] | None, press_preds: dict[str, list[str]] | None,
             draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> dict:
    """Les 4 critères du protocole, par graine et en moyenne, avec la baseline lexique seul."""
    kept, golds = reference_view(test_rows)
    baseline = [rules_binary(test_rows[i][1]) for i in kept]
    per_seed = {}
    for s, preds in test_preds.items():
        chosen = [preds[i] for i in kept]
        per_seed[s] = {**binary_scores(golds, chosen), **binary_bootstrap(golds, chosen, draws,
                                                                          seed)}
    out = {"n_test_t_a": len(kept), "graines": per_seed,
           "baseline_lexique_seul": {**binary_scores(golds, baseline),
                                     **binary_bootstrap(golds, baseline, draws, seed)}}
    out["rappel_tn"] = mean_sd([v["rappel_tn"] for v in per_seed.values()])
    out["precision_tn"] = mean_sd([v["precision_tn"] for v in per_seed.values()])

    eval_golds = [e["lang"] for e in eval_examples]
    rules_eval = scores(eval_examples, [normalize(e["text"]).lang.value for e in eval_examples],
                        "lang")["macro_f1"]
    eval_f1 = {s: scores(eval_examples, p, "lang")["macro_f1"] for s, p in eval_preds.items()}
    out["eval_30"] = {"n": len(eval_golds), "macro_f1_regles": rules_eval,
                      "macro_f1_protocole": EVAL30_MACRO_F1_PROTOCOLE,
                      "graines": eval_f1, **mean_sd(list(eval_f1.values()))}

    if press_texts is None or press_preds is None:
        out["presse"] = {"statut": "non mesuré (aucune année autre que 2022, §9)"}
    else:
        rates = {s: proportion(sum(p == "tn" for p in preds), len(preds))
                 for s, preds in press_preds.items()}
        base = [rules_binary(t) for t in press_texts]
        out["presse"] = {"statut": "mesuré", "n": len(press_texts), "graines": rates,
                         "baseline_lexique_seul": proportion(base.count("tn"), len(base)),
                         **mean_sd([r["taux"] for r in rates.values()])}
    return out


def verdict(result: dict, statut_reference: str) -> dict:
    """Critères jugés sur la moyenne des graines ; « indicatif » si annotateur unique (§8)."""
    checks = {
        "1_rappel_tn": result["rappel_tn"]["moyenne"] >= MIN_RECALL_TN,
        "2_precision_tn": result["precision_tn"]["moyenne"] >= MIN_PRECISION_TN,
        "3_fausses_alertes": (result["presse"]["moyenne"] <= MAX_FALSE_ALARMS
                              if result["presse"]["statut"] == "mesuré" else None),
        "4_eval_30": result["eval_30"]["moyenne"] >= result["eval_30"]["macro_f1_regles"],
    }
    if statut_reference != "adjugee":
        conclusion = ("indicatif : référence d'un seul annotateur, accord humain non mesuré ;"
                      " pas de conclusion au sens du protocole")
    elif None in checks.values():
        conclusion = "non conclu : critère 3 non mesuré"
    else:
        conclusion = "critères atteints" if all(checks.values()) else "critères non atteints"
    return {"criteres": checks, "conclusion": conclusion}


# ---------------------------------------------------------------------------
# Passage unique
# ---------------------------------------------------------------------------

def acquire_passage(out_dir: Path, second: bool, manifest_sha: str) -> int:
    """1er passage, ou 2e déclaré avec --deuxieme-passage ; jamais un 3e."""
    lock = out_dir / LOCK_NAME
    done = json.loads(lock.read_text(encoding="utf-8"))["passages"] if lock.exists() else []
    if not done and second:
        raise RefusGold("--deuxieme-passage demandé alors qu'aucun passage n'a eu lieu")
    if done and not second:
        raise RefusGold(f"mesure déjà faite ({len(done)} passage) : relance seulement avec"
                        " --deuxieme-passage, à déclarer comme telle")
    if len(done) >= 2:
        raise RefusGold("deux passages déjà faits : aucun autre n'est permis")
    number = len(done) + 1
    done.append({"passage": number, "date": datetime.now().isoformat(timespec="seconds"),
                 "manifeste_sha256": manifest_sha})
    lock.write_text(json.dumps({"passages": done}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return number


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise RefusGold(f"manifeste absent : {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in ("reference_test", "statut_reference", "graines", "presse")
               if k not in manifest]
    if missing:
        raise RefusGold(f"manifeste incomplet : {missing}")
    if manifest["statut_reference"] not in ("adjugee", "annotateur1_seul"):
        raise RefusGold("statut_reference doit valoir « adjugee » ou « annotateur1_seul »")
    if sorted(manifest["graines"]) != list(SEEDS):
        raise RefusGold(f"graines attendues : {list(SEEDS)}")
    return manifest


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifeste", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    parser.add_argument("--deuxieme-passage", action="store_true")
    args = parser.parse_args(argv)

    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    manifest = load_manifest(args.manifeste)
    # Toutes les empreintes sont vérifiées avant le moindre calcul de score.
    rows = load_reference(Path(manifest["reference_test"]["chemin"]),
                          manifest["reference_test"]["sha256"])
    check_file("eval_30", DEFAULT_DATASET, EVAL30_SHA)
    eval_examples = load_examples(DEFAULT_DATASET)
    press = manifest["presse"]
    press_texts = load_press(press) if press else None
    test_preds, eval_preds, press_preds = {}, {}, ({} if press else None)
    for s in SEEDS:
        files = manifest["graines"][s]
        test_preds[s] = load_predictions(f"prédictions test graine {s}", files["test"], N_TEST,
                                         {"tn", "ar"})
        eval_preds[s] = load_predictions(f"prédictions eval_30 graine {s}", files["eval_30"],
                                         len(eval_examples), {"fr", "ar", "tn"})
        if press_preds is not None:
            press_preds[s] = load_predictions(f"prédictions presse graine {s}", files["presse"],
                                              len(press_texts), {"tn", "ar"})
    manifest_sha = sha256_file(args.manifeste)
    number = acquire_passage(out_dir, args.deuxieme_passage, manifest_sha)

    result = criteria(rows, test_preds, eval_examples, eval_preds, press_texts, press_preds)
    decision = verdict(result, manifest["statut_reference"])
    payload = {"experience": "EXP-A2-020", "protocole": "docs/lot-a2_protocole_gold.md §9",
               "passage": number, "manifeste_sha256": manifest_sha, "code": git_state(),
               "statut_reference": manifest["statut_reference"], "presse": press,
               "graine_bootstrap": SEED, "tirages_bootstrap": BOOTSTRAP_DRAWS,
               **result, "verdict": decision}
    print(f"== EXP-A2-020, passage {number} ; référence : {manifest['statut_reference']} ==")
    print(f"  test (t / a) : n = {result['n_test_t_a']}")
    print(f"  rappel tn {result['rappel_tn']} ; précision tn {result['precision_tn']}")
    base = result["baseline_lexique_seul"]
    print(f"  baseline lexique seul : rappel {round(base['rappel_tn'], 4)}"
          f" précision {round(base['precision_tn'], 4)}")
    print(f"  eval_30 macro-F1 : cascade {result['eval_30']['moyenne']}"
          f" ; règles {result['eval_30']['macro_f1_regles']}")
    print(f"  presse : {result['presse'].get('moyenne', result['presse']['statut'])}")
    print(f"  critères : {decision['criteres']}")
    print(f"  conclusion : {decision['conclusion']}")
    print(f"JSON : {write_json(out_dir, f'lot-a2_gold_final_passage{number}', payload)}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
