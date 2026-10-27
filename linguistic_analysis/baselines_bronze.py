"""Lot B — Baselines triviales sur `eval_30` (revue Bronze), à côté du système.

Usage (depuis la racine du dépôt) :

    python -m linguistic_analysis.baselines_bronze [--markdown FICHIER] [--rules-only]

Ne modifie ni les règles, ni le jeu d'évaluation, ni `evaluation/results/` : le script affiche
les tableaux et, avec `--markdown`, les écrit dans le fichier indiqué.

Baselines (règles exactes) :

1. Détection d'affirmation : « toute phrase = affirmation » (`is_claim = True` partout).
2. Modalité : « classe majoritaire » du gold (la plus fréquente ; égalité départagée par ordre
   alphabétique), prédite pour toutes les phrases.
3. Triplet SPO, sur la phrase cible seule (`item["text"]`, sans contexte), après
   `normalize` : mots = segments séparés par des espaces, ponctuation retirée en début et fin
   de mot, mots vides éliminés.
   - prédicat : premier mot dont la forme repliée (`fold`) figure dans
     `preprocessing.verb_lexicon()["forms"]` (lexique verbal du mode règles, sans retrait des
     clitiques) ;
   - sujet : premier « mot plein » (au moins 3 caractères alphabétiques, chiffres exclus)
     différent du prédicat ;
   - si aucun verbe du lexique : prédicat = mot qui suit le sujet ;
   - objet : mot qui suit le prédicat (différent du sujet), sinon absent (`None`).

Métriques : celles de `evaluate.py` (`exact_match`, `token_f1`, `_metrics`) ; précision, rappel
et F1 de la classe « affirmation » par `evaluation.metrics.precision_recall_f1` ; macro-F1 par
`evaluation.metrics.macro_f1` (classes présentes dans le gold ou la prédiction).

Écart système − baseline : bootstrap apparié percentile (mêmes tirages de phrases pour les deux
sorties), graine `evaluate.BOOTSTRAP_SEED`, `evaluate.BOOTSTRAP_RESAMPLES` tirages, 95 %.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter
from pathlib import Path

from evaluation.metrics import macro_f1, precision_recall_f1
from linguistic_analysis import evaluate
from linguistic_analysis.preprocessing import fold, verb_lexicon
from normalization.normalize import normalize

ROLES = evaluate.ROLES
_FULL_WORD = re.compile(r"[^\W\d_]{3,}")
_EDGE_PUNCT = " .,;:!?؟،«»\"'()[]"


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------


def majority_label(items: list[dict]) -> str:
    """Modalité la plus fréquente du gold (égalité : ordre alphabétique)."""
    counts = Counter(it["gold"]["modality"] for it in items)
    return min(counts, key=lambda label: (-counts[label], label))


def _words(text: str) -> list[str]:
    words = (w.strip(_EDGE_PUNCT) for w in normalize(text).text.split())
    return [w for w in words if any(ch.isalnum() for ch in w)]


def baseline_spo(text: str) -> dict[str, str | None]:
    """Triplet trivial (voir la règle en tête du module)."""
    words = _words(text)
    forms = verb_lexicon()["forms"]
    p = next((i for i, w in enumerate(words) if fold(w) in forms), None)
    s = next((i for i, w in enumerate(words) if i != p and _FULL_WORD.fullmatch(w)), None)
    if p is None and s is not None and s + 1 < len(words):
        p = s + 1
    o = p + 1 if p is not None and p + 1 < len(words) else None
    if o is not None and o == s:
        o = o + 1 if o + 1 < len(words) else None
    return {
        "subject": words[s] if s is not None else None,
        "predicate": words[p] if p is not None else None,
        "obj": words[o] if o is not None else None,
    }


def baseline_records(items: list[dict], label: str) -> list[dict]:
    """Sortie des baselines au format de `evaluate` (`id`, `gold`, `pred`)."""
    return [
        {
            "id": it["id"],
            "gold": it["gold"],
            "pred": {
                "is_claim": True,
                "modality": label,
                **baseline_spo(it["text"]),
                "resolved_text": it["text"],
            },
        }
        for it in items
    ]


# ---------------------------------------------------------------------------
# Métriques
# ---------------------------------------------------------------------------


def scores(records: list[dict]) -> dict[str, float | None]:
    """Métriques à plat (détection, modalité, SPO), arrondies à 3 décimales."""
    gold = ["claim" if r["gold"]["is_claim"] else "non" for r in records]
    pred = ["claim" if r["pred"]["is_claim"] else "non" for r in records]
    claim = precision_recall_f1(gold, pred, "claim")
    gold_mod = [r["gold"]["modality"] for r in records]
    pred_mod = [r["pred"]["modality"] for r in records]
    base = evaluate._metrics(records)
    out = {
        "claim_accuracy": base["is_claim_accuracy"],
        "claim_precision": round(claim["precision"], 3),
        "claim_recall": round(claim["recall"], 3),
        "claim_f1": round(claim["f1"], 3),
        "claim_macro_f1": base["is_claim_macro_f1"],
        "modality_accuracy": base["modality_accuracy"],
        "modality_macro_f1": round(macro_f1(gold_mod, pred_mod), 3) if records else None,
        "spo_all_exact": base["spo_all_exact"],
    }
    for role in ROLES:
        out[f"spo_exact.{role}"] = base["spo_exact"][role]
        out[f"spo_partial.{role}"] = base["spo_partial"][role]
    return out


def paired_diff(
    baseline: list[dict],
    system: list[dict],
    *,
    resamples: int = evaluate.BOOTSTRAP_RESAMPLES,
    seed: int = evaluate.BOOTSTRAP_SEED,
    confidence: float = evaluate.CONFIDENCE,
) -> dict[str, dict]:
    """Écart système − baseline par métrique, avec intervalle bootstrap apparié."""
    a = sorted(baseline, key=lambda r: r["id"])
    b = sorted(system, key=lambda r: r["id"])
    if [r["id"] for r in a] != [r["id"] for r in b]:
        raise ValueError("comparaison appariée : phrases différentes dans les deux sorties")
    observed_a, observed_b = scores(a), scores(b)
    rng = random.Random(seed)
    diffs: dict[str, list[float]] = {key: [] for key in observed_a}
    n = len(a)
    for _ in range(resamples if n else 0):
        indices = [rng.randrange(n) for _ in range(n)]
        drawn_a = scores([a[i] for i in indices])
        drawn_b = scores([b[i] for i in indices])
        for key in diffs:
            va, vb = drawn_a[key], drawn_b[key]
            if va is not None and vb is not None:
                diffs[key].append(vb - va)
    out = {}
    for key, values in diffs.items():
        va, vb = observed_a[key], observed_b[key]
        interval = evaluate._interval(values, confidence)
        out[key] = {
            "baseline": va,
            "system": vb,
            "diff": None if va is None or vb is None else round(vb - va, 3),
            "low": round(interval[0], 3) if interval else None,
            "high": round(interval[1], 3) if interval else None,
            "valid": len(values),
        }
    return out


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

ROWS = (
    ("Détection : exactitude", "claim_accuracy", "n"),
    ("Détection : précision (affirmation)", "claim_precision", "n"),
    ("Détection : rappel (affirmation)", "claim_recall", "n"),
    ("Détection : F1 (affirmation)", "claim_f1", "n"),
    ("Détection : macro-F1 (2 classes)", "claim_macro_f1", "n"),
    ("Modalité : exactitude", "modality_accuracy", "n"),
    ("Modalité : macro-F1", "modality_macro_f1", "n"),
    ("SPO : triplet exact", "spo_all_exact", "spo_n"),
    ("SPO : sujet exact", "spo_exact.subject", "spo_n"),
    ("SPO : prédicat exact", "spo_exact.predicate", "spo_n"),
    ("SPO : objet exact", "spo_exact.obj", "spo_n"),
    ("SPO : sujet partiel (F1 tokens)", "spo_partial.subject", "spo_n"),
    ("SPO : prédicat partiel (F1 tokens)", "spo_partial.predicate", "spo_n"),
    ("SPO : objet partiel (F1 tokens)", "spo_partial.obj", "spo_n"),
)


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def _ci(d: dict) -> str:
    if d["diff"] is None:
        return "—"
    return f"{d['diff']:+.3f} [{_fmt(d['low'])} ; {_fmt(d['high'])}]"


def build_report(items: list[dict], systems: dict[str, list[dict]]) -> str:
    """Tableaux Markdown : composant | baseline | systèmes | N | écart (IC 95 %)."""
    label = majority_label(items)
    base = baseline_records(items, label)
    n = len(items)
    spo_n = sum(it["gold"]["is_claim"] for it in items)
    counts = {"n": n, "spo_n": spo_n}
    comparisons = {name: paired_diff(base, recs) for name, recs in systems.items()}
    names = list(systems)

    distribution = Counter(it["gold"]["modality"] for it in items)
    lines = [
        f"Jeu : `{evaluate.EVAL_SET.name}` — {n} phrases, {spo_n} affirmations (gold).",
        f"Bootstrap apparié : graine {evaluate.BOOTSTRAP_SEED}, "
        f"{evaluate.BOOTSTRAP_RESAMPLES} tirages, IC {int(evaluate.CONFIDENCE * 100)} %.",
        "",
        "## Répartition des modalités (gold)",
        "",
        "| Modalité | N | Part |",
        "|---|---|---|",
    ]
    for lab in sorted(distribution, key=lambda x: (-distribution[x], x)):
        lines.append(f"| {lab} | {distribution[lab]} | {distribution[lab] / n:.3f} |")
    lines += [
        "",
        f"Classe majoritaire : `{label}`.",
        "",
        "## Baseline contre système",
        "",
        "| Composant | Baseline | " + " | ".join(names) + " | N | "
        + " | ".join(f"Écart {name} [IC 95 %]" for name in names) + " |",
        "|---|---|" + "---|" * len(names) + "---|" + "---|" * len(names),
    ]
    first = comparisons[names[0]]
    for title, key, count in ROWS:
        cells = [_fmt(first[key]["baseline"])]
        cells += [_fmt(comparisons[name][key]["system"]) for name in names]
        cells.append(str(counts[count]))
        cells += [_ci(comparisons[name][key]) for name in names]
        lines.append(f"| {title} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Baselines : détection « toute phrase = affirmation » ; modalité « classe majoritaire » ;",
        "SPO « premier mot plein / premier verbe du lexique / mot suivant » (règle exacte : "
        "docstring de `linguistic_analysis/baselines_bronze.py`).",
        "",
        "## Limites de la mesure",
        "",
        "- N = 34 phrases (22 affirmations) : intervalles larges ; une phrase vaut 0.03 en "
        "détection et 0.045 en SPO.",
        "- `eval_30` a servi à mettre au point les règles du système (pas de jeu tenu à "
        "l'écart) : les scores du système sont optimistes ; mesure indépendante attendue "
        "sur `eval_100`.",
        "- Macro-F1 de la modalité : classes rares (une phrase `conditionnel`) ; valeur "
        "instable.",
        "- La baseline SPO réutilise le lexique verbal du mode règles : elle n'est pas "
        "indépendante du système.",
        "- Mode parseurs : dépend des modèles spaCy / Stanza installés (colonne "
        "`parsers_used`), sans modèle il retombe sur les règles.",
        "- Accord inter-annotateurs : non mesuré (aucune seconde annotation de `eval_30` "
        "dans le dépôt) ; plafond humain inconnu.",
    ]
    return "\n".join(lines) + "\n"


def system_records(items: list[dict], rules: bool) -> tuple[list[dict], list[str]]:
    results = evaluate.evaluate(items, rules=rules)
    records = [{"id": r["id"], "gold": r["gold"], "pred": r["pred"]} for r in results["items"]]
    return records, results["parsers_used"]


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--markdown", type=Path, help="écrit aussi le rapport dans ce fichier")
    parser.add_argument("--rules-only", action="store_true", help="système en mode règles seul")
    args = parser.parse_args(argv)

    items = evaluate.load_eval_set()
    systems: dict[str, list[dict]] = {}
    systems["règles"], _ = system_records(items, rules=True)
    used = ["rules"]
    if not args.rules_only:
        systems["parseurs"], used = system_records(items, rules=False)
    digest = evaluate.sha256_file(evaluate.EVAL_SET)
    header = (
        f"# Baselines Bronze — Lot B\n\nSha256 du jeu : `{digest}`. "
        f"Analyseurs utilisés : {', '.join(used)}.\n\n"
    )
    report = header + build_report(items, systems)
    print(report)
    if args.markdown:
        args.markdown.write_text(report, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
