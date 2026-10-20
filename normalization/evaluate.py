"""Lot A2 — Évaluation de l'identification de langue et de script.

Usage (depuis la racine du dépôt) :
    python -m normalization.evaluate                 # jeu par défaut
    python -m normalization.evaluate --errors        # + liste des erreurs
    python -m normalization.evaluate chemin/jeu.jsonl

Le jeu est un fichier JSONL : une phrase par ligne, avec au moins les champs
`id`, `text`, `lang` et `script` (les étiquettes de référence, posées à la main).

Le script ne fait que lire et mesurer : il ne modifie aucun fichier.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from normalization.normalize import normalize

# Jeu annoté par le Lot B : 34 phrases en FR, arabe standard, tunisien, mixte.
DEFAULT_DATASET = Path("tests/fixtures/linguistic_analysis/eval_30.jsonl")


def load_examples(path: Path) -> list[dict]:
    """Lit un fichier JSONL : chaque ligne non vide est un objet JSON."""
    examples = []
    # encoding="utf-8" est indispensable sous Windows pour lire l'arabe.
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def report(examples: list[dict], predictions: list[str], field: str) -> None:
    """Affiche, pour un champ (`lang` ou `script`), le score de chaque classe."""
    total: Counter[str] = Counter()  # phrases par étiquette de référence
    correct: Counter[str] = Counter()  # phrases bien classées par étiquette
    confusions: Counter[tuple[str, str]] = Counter()  # (référence, prédiction)

    for example, predicted in zip(examples, predictions, strict=True):
        gold = example.get(field, "?")  # "?" si la ligne n'a pas d'étiquette
        total[gold] += 1
        if predicted == gold:
            correct[gold] += 1
        else:
            confusions[(gold, predicted)] += 1

    print(f"== {field} ==")
    for label in sorted(total):
        rate = correct[label] / total[label]
        print(f"  {label:8} {correct[label]:2}/{total[label]:<2}  {rate:.2f}")

    # Exactitude globale : part de phrases bien classées, toutes classes mêlées.
    overall = sum(correct.values()) / sum(total.values())
    # Moyenne par classe : chaque langue pèse autant, même si elle a peu de
    # phrases. C'est elle qui révèle une langue mal traitée mais minoritaire.
    macro = sum(correct[label] / total[label] for label in total) / len(total)
    print(f"  exactitude globale : {overall:.2f} | moyenne par classe : {macro:.2f}")

    for (gold, predicted), count in confusions.most_common():
        print(f"  confusion {gold} -> {predicted} : {count}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--errors", action="store_true", help="liste chaque erreur")
    args = parser.parse_args()

    # Sous Windows, on force l'UTF-8 pour afficher l'arabe sans erreur.
    sys.stdout.reconfigure(encoding="utf-8")

    examples = load_examples(args.dataset)
    # On normalise chaque phrase UNE fois, puis on lit langue et script.
    documents = [normalize(example["text"]) for example in examples]
    langs = [document.lang.value for document in documents]
    scripts = [document.script for document in documents]

    print(f"Jeu : {args.dataset} ({len(examples)} phrases)")
    print()
    report(examples, langs, "lang")
    report(examples, scripts, "script")

    if args.errors:
        print("== erreurs ==")
        for example, lang, script in zip(examples, langs, scripts, strict=True):
            gold_lang = example.get("lang", "?")
            gold_script = example.get("script", "?")
            if (lang, script) != (gold_lang, gold_script):
                print(
                    f"  {example.get('id', '?'):7} "
                    f"attendu {gold_lang}/{gold_script}, obtenu {lang}/{script} : "
                    f"{example['text']}"
                )


if __name__ == "__main__":
    main()
