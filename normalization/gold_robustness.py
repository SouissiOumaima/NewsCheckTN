"""Lot A2 — Gold, EXP-A2-016 : robustesse INV de l'identification de langue (dev seulement).

Protocole : docs/lot-a2_protocole_gold.md, §5 (perturbations, mesures, règle de décision).

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_robustness --out-dir <dossier hors dépôt>

Pour chaque perturbation P1 à P10 et chaque jeu de dev (lettres arabes, lettres latines) :
taux de bascule de la langue (intervalle de Wilson, décision robuste / fragile / indéterminé),
exactitude et macro-F1 avant / après (écart apparié, IC bootstrap), pour les règles du Lot A2
et la baseline « alphabet seul ». Plus deux invariants sans étiquette : idempotence de
normalize() et cohérence entre texte brut et texte normalisé.

Sorties : effectifs, taux, intervalles et empreintes seulement (console et JSON hors dépôt).
"""

from __future__ import annotations

import argparse
import random
import re
from collections.abc import Callable
from pathlib import Path

from normalization import baseline_fasttext
from normalization.evaluate import load_examples
from normalization.gold_common import (
    BOOTSTRAP_DRAWS,
    SEED,
    Z_95,
    RefusGold,
    check_file,
    check_out_dir,
    decision_inv,
    error_record,
    git_state,
    paired_bootstrap,
    proportion,
    safe_main,
    write_json,
)
from normalization.normalize import detect_language, normalize
from normalization.review import INTERIM, alphabet_baseline

# Jeux de dev d'EXP-A2-009, gelés le 2026-10-26 ; empreintes recopiées d'EXP-A2-011.
DEV_SETS = {
    "arabe": (INTERIM / "tsac_arabic_sample_reference.tsv",
              "a59f3d27621a4f4d4297f7d73b80301418767197316fb785cb7f0f32bb4ad92f"),
    "latin": (INTERIM / "tsac_latin_sample_reference.tsv",
              "1703f003cc0132c148ca46bf92b86ea05270d8851eb3d447109e366985877a46"),
}

# ---------------------------------------------------------------------------
# Perturbations (§5) : chacune reçoit le texte et un tirage propre au couple (code, ligne)
# ---------------------------------------------------------------------------

ARABIC_LETTER = re.compile(r"[ء-ي]")
NON_JOINING = set("ءآأؤإاةدذرزو")  # lettres qui ne s'attachent pas à la suivante
TATWEEL = "ـ"
HARAKAT = ["َ", "ُ", "ِ", "ْ"]  # fatha, damma, kasra, soukoun
LAM_ALEF = "ﻻ"  # ligature lam-alef, forme de présentation
EMOJIS = ["😂", "❤", "👍", "🔥"]
URL = "https://example.com/article"
P5_RATE = 0.3


def p1_lower(text: str, rng: random.Random) -> str:
    return text.lower()


def p2_upper(text: str, rng: random.Random) -> str:
    return text.upper()


def p3_elongation(text: str, rng: random.Random) -> str:
    """Une lettre d'un mot tiré au hasard apparaît 3 fois de suite."""
    positions = [i for i, c in enumerate(text) if c.isalpha()]
    if not positions:
        return text
    words = sorted({_word_start(text, i) for i in positions})
    start = rng.choice(words)
    letters = [i for i in positions if _word_start(text, i) == start]
    i = rng.choice(letters)
    return text[:i + 1] + text[i] * 2 + text[i + 1:]


def _word_start(text: str, i: int) -> int:
    while i > 0 and not text[i - 1].isspace():
        i -= 1
    return i


def p4_tatweel(text: str, rng: random.Random) -> str:
    """Un tatweel après une lettre arabe qui s'attache à une lettre arabe suivante."""
    spots = [i for i in range(len(text) - 1)
             if ARABIC_LETTER.match(text[i]) and text[i] not in NON_JOINING
             and ARABIC_LETTER.match(text[i + 1])]
    if not spots:
        return text
    i = rng.choice(spots)
    return text[:i + 1] + TATWEEL + text[i + 1:]


def p5_diacritics(text: str, rng: random.Random) -> str:
    """Après chaque lettre arabe, une haraka avec la probabilité 0.3 ; au moins une."""
    letters = [i for i, c in enumerate(text) if ARABIC_LETTER.match(c)]
    if not letters:
        return text
    chosen = {i for i in letters if rng.random() < P5_RATE} or {rng.choice(letters)}
    return "".join(c + (rng.choice(HARAKAT) if i in chosen else "") for i, c in enumerate(text))


def p6_presentation(text: str, rng: random.Random) -> str:
    return text.replace("لا", LAM_ALEF)


def p7_emoji(text: str, rng: random.Random) -> str:
    return f"{text} {rng.choice(EMOJIS)}"


def p8_url(text: str, rng: random.Random) -> str:
    return f"{text} {URL}"


def p9_punctuation(text: str, rng: random.Random) -> str:
    return text + "!!!"


def p10_spaces(text: str, rng: random.Random) -> str:
    """Chaque espace devient, au hasard, deux espaces ou une espace insécable."""
    return re.sub(" ", lambda _: rng.choice(["  ", " "]), text)


# code -> (fonction, jeux concernés), colonne « S'applique à » du §5
PERTURBATIONS: dict[str, tuple[Callable[[str, random.Random], str], frozenset[str]]] = {
    "P1": (p1_lower, frozenset({"latin"})),
    "P2": (p2_upper, frozenset({"latin"})),
    "P3": (p3_elongation, frozenset({"arabe", "latin"})),
    "P4": (p4_tatweel, frozenset({"arabe"})),
    "P5": (p5_diacritics, frozenset({"arabe"})),
    "P6": (p6_presentation, frozenset({"arabe"})),
    "P7": (p7_emoji, frozenset({"arabe", "latin"})),
    "P8": (p8_url, frozenset({"arabe", "latin"})),
    "P9": (p9_punctuation, frozenset({"arabe", "latin"})),
    "P10": (p10_spaces, frozenset({"arabe", "latin"})),
}


def perturb(code: str, text: str, line: str, seed: int = SEED) -> str:
    """Applique une perturbation ; tirage déterministe propre à (graine, code, ligne)."""
    function, _ = PERTURBATIONS[code]
    return function(text, random.Random(f"{seed}-{code}-{line}"))


# ---------------------------------------------------------------------------
# Systèmes mesurés : prédicteur = liste de textes -> liste de codes de langue
# ---------------------------------------------------------------------------

def rules_predictor(texts: list[str]) -> list[str]:
    """Règles du Lot A2 : detect_language, comme l'écrit le §5."""
    return [detect_language(t).value for t in texts]


PREDICTORS: dict[str, Callable[[list[str]], list[str]]] = {
    "regles": rules_predictor,
    "alphabet": alphabet_baseline,
}

# Systèmes facultatifs, chargés seulement s'ils sont demandés (fastText : EXP-A2-017, §6).
# baseline_fasttext n'importe le paquet fasttext qu'au chargement du modèle.
OPTIONAL_LOADERS: dict[str, Callable[[argparse.Namespace], Callable[[list[str]], list[str]]]] = {
    "fasttext": lambda args: baseline_fasttext.load_predictor(args.fasttext_modele),
}


# ---------------------------------------------------------------------------
# Mesure
# ---------------------------------------------------------------------------

def _predict_each(predictor: Callable[[list[str]], list[str]], items: list[tuple[str, str]],
                  dataset: str, errors: list[dict]) -> dict[str, str]:
    """Prédit texte par texte ; une erreur est notée (ligne, type) et le texte écarté."""
    out = {}
    for line, text in items:
        try:
            out[line] = predictor([text])[0]
        except Exception as exc:
            errors.append(error_record(dataset, line, exc))
    return out


def measure_perturbation(examples: list[dict], dataset: str, code: str,
                         predictors: dict[str, Callable[[list[str]], list[str]]],
                         errors: list[dict], seed: int = SEED,
                         draws: int = BOOTSTRAP_DRAWS) -> dict:
    """Taux de bascule et avant / après pour une perturbation, sur un jeu, pour chaque système."""
    pairs = []  # (ligne, référence, original, perturbé) des textes modifiés
    for ex in examples:
        try:
            changed = perturb(code, ex["text"], ex["id"], seed)
        except Exception as exc:
            errors.append(error_record(dataset, ex["id"], exc))
            continue
        if changed != ex["text"]:
            pairs.append((ex["id"], ex["lang"], ex["text"], changed))
    result = {"applicables": len(pairs), "systemes": {}}
    for name, predictor in predictors.items():
        before = _predict_each(predictor, [(p[0], p[2]) for p in pairs], dataset, errors)
        after = _predict_each(predictor, [(p[0], p[3]) for p in pairs], dataset, errors)
        kept = [p for p in pairs if p[0] in before and p[0] in after]
        flips = sum(before[p[0]] != after[p[0]] for p in kept)
        entry = {"bascule": proportion(flips, len(kept)),
                 "decision": decision_inv(flips, len(kept))}
        if kept:
            entry["avant_apres"] = paired_bootstrap(
                [p[1] for p in kept], [before[p[0]] for p in kept],
                [after[p[0]] for p in kept], draws=draws, seed=seed)
        result["systemes"][name] = entry
    return result


def measure_invariants(examples: list[dict], dataset: str, errors: list[dict]) -> dict:
    """Idempotence de normalize() et cohérence detect_language(brut) / normalize(brut).lang."""
    n = idem_fail = coh_fail = 0
    for ex in examples:
        try:
            doc = normalize(ex["text"])
            idem = normalize(doc.text).text == doc.text
            coh = detect_language(ex["text"]) == doc.lang
        except Exception as exc:
            errors.append(error_record(dataset, ex["id"], exc))
            continue
        n += 1
        idem_fail += not idem
        coh_fail += not coh
    return {"idempotence_echecs": proportion(idem_fail, n),
            "coherence_echecs": proportion(coh_fail, n)}


def measure_dataset(examples: list[dict], dataset: str,
                    predictors: dict[str, Callable[[list[str]], list[str]]],
                    seed: int = SEED, draws: int = BOOTSTRAP_DRAWS) -> dict:
    """Toutes les perturbations concernant ce jeu, puis les invariants."""
    errors: list[dict] = []
    perturbations = {code: measure_perturbation(examples, dataset, code, predictors, errors,
                                                seed, draws)
                     for code, (_, scope) in PERTURBATIONS.items() if dataset in scope}
    return {"n": len(examples), "perturbations": perturbations,
            "invariants": measure_invariants(examples, dataset, errors), "erreurs": errors}


# ---------------------------------------------------------------------------
# Commande
# ---------------------------------------------------------------------------

def print_summary(dataset: str, result: dict) -> None:
    """Affiche effectifs, taux, intervalles et décisions ; aucun texte."""
    print(f"== dev {dataset} : {result['n']} textes ==")
    for code, pert in result["perturbations"].items():
        for name, entry in pert["systemes"].items():
            b = entry["bascule"]
            line = (f"  {code:4} {name:9} n={b['n']:3} bascules={b['k']:3} "
                    f"taux={b['taux'] if b['taux'] is not None else '-'} "
                    f"Wilson=[{b['wilson_bas']} ; {b['wilson_haut']}] {entry['decision']}")
            if "avant_apres" in entry:
                f1 = entry["avant_apres"]["macro_f1"]
                line += (f" | macro-F1 {f1['avant']}→{f1['apres']}"
                         f" [{f1['ic_bas']} ; {f1['ic_haut']}]")
            print(line)
    for key, value in result["invariants"].items():
        print(f"  {key} : {value['k']}/{value['n']} Wilson=[{value['wilson_bas']} ;"
              f" {value['wilson_haut']}]")
    print(f"  erreurs : {len(result['erreurs'])}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    parser.add_argument("--dev-arabe", type=Path, default=DEV_SETS["arabe"][0])
    parser.add_argument("--dev-latin", type=Path, default=DEV_SETS["latin"][0])
    parser.add_argument("--systemes", default="regles,alphabet",
                        help="systèmes mesurés, séparés par des virgules (option : fasttext)")
    parser.add_argument("--fasttext-modele", type=Path, default=baseline_fasttext.DEFAULT_MODEL)
    return parser.parse_args(argv)


def build_predictors(names: str, args: argparse.Namespace) -> dict:
    """Systèmes demandés ; les facultatifs (fastText) ne sont chargés que s'ils sont demandés."""
    chosen = {}
    for name in [n.strip() for n in names.split(",") if n.strip()]:
        if name in PREDICTORS:
            chosen[name] = PREDICTORS[name]
        elif name in OPTIONAL_LOADERS:
            chosen[name] = OPTIONAL_LOADERS[name](args)
        else:
            raise RefusGold(f"système inconnu : {name}")
    return chosen


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    out_dir = check_out_dir(args.out_dir)  # avant toute lecture de données
    paths = {"arabe": args.dev_arabe, "latin": args.dev_latin}
    digests = {name: check_file(f"dev {name}", paths[name], DEV_SETS[name][1])
               for name in DEV_SETS}
    predictors = build_predictors(args.systemes, args)
    payload = {
        "experience": "EXP-A2-016", "protocole": "docs/lot-a2_protocole_gold.md §5",
        "graine": SEED, "tirages_bootstrap": BOOTSTRAP_DRAWS, "z_wilson": Z_95,
        "code": git_state(), "empreintes": digests, "systemes": list(predictors), "jeux": {},
    }
    for name in DEV_SETS:
        result = measure_dataset(load_examples(paths[name]), name, predictors)
        payload["jeux"][name] = result
        print_summary(name, result)
    path = write_json(out_dir, "lot-a2_gold_inv_dev", payload)
    print(f"JSON : {path}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
