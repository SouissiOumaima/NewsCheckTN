"""Lot A2 — Évaluation de l'identification de langue et de script.

Usage (depuis la racine du dépôt) :
    python -m normalization.evaluate                 # jeu par défaut
    python -m normalization.evaluate --errors        # + liste des erreurs
    python -m normalization.evaluate chemin/jeu.jsonl
    python -m normalization.evaluate --save --exp-id EXP-A2-008   # + fichier du tableau de bord

Deux formats de jeu sont acceptés :
- JSONL : une phrase par ligne, avec au moins les champs `id`, `text`, `lang`
  et `script` (les étiquettes de référence, posées à la main) ;
- TSV d'annotation (voir docs/lot-a2_guide_annotation.md) : étiquette `t`
  (tunisien), `a` (arabe standard) ou `f` (français), une tabulation, puis le
  texte. Les lignes `x` (indécidables) et `?` (non annotées) sont ignorées.
  Ces fichiers n'ont pas d'étiquette de script : seule la langue est mesurée.

Sans --save, le script ne fait que lire et mesurer : il ne modifie aucun fichier. Avec --save, il
écrit un fichier JSON dans evaluation/results/, au format décrit dans evaluation/README.md : c'est
ce dossier que lit la page « Évaluation » de la plateforme. Ces fichiers ne sont pas versionnés.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from normalization.normalize import normalize

# Racine du dépôt, déduite de l'emplacement de ce fichier : les chemins par défaut
# fonctionnent quel que soit le dossier d'où la commande est lancée.
REPO = Path(__file__).resolve().parent.parent

# Jeu annoté par le Lot B : 34 phrases en FR, arabe standard, tunisien, mixte.
DEFAULT_DATASET = REPO / "tests" / "fixtures" / "linguistic_analysis" / "eval_30.jsonl"

# Dossier lu par le tableau de bord (format : evaluation/README.md).
RESULTS_DIR = REPO / "evaluation" / "results"


# Étiquettes du guide d'annotation -> codes de langue du projet.
TSV_LABELS = {"t": "tn", "a": "ar", "f": "fr"}


def load_examples(path: Path) -> list[dict]:
    """Lit un jeu JSONL, ou un fichier d'annotation TSV en lettres arabes."""
    examples = []
    # encoding="utf-8-sig" lit l'UTF-8 avec ou sans marque d'ordre d'octets (BOM).
    with path.open(encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            if path.suffix != ".tsv":
                examples.append(json.loads(line))
                continue
            label, _, text = line.rstrip("\r\n").partition("\t")
            if label.strip().lower() in TSV_LABELS:  # on saute x et ?
                lang = TSV_LABELS[label.strip().lower()]
                # Le numéro de ligne sert d'identifiant.
                examples.append({"id": f"l{number}", "lang": lang, "text": text})
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


def scores(examples: list[dict], predictions: list[str], field: str) -> dict:
    """Précision, rappel et F1 par classe, F1 moyen par classe (macro-F1) et exactitude.

    Les classes sont celles des étiquettes de référence. Précision : part des phrases
    prédites dans une classe qui y sont vraiment ; rappel : part des phrases d'une classe
    retrouvées ; F1 : moyenne harmonique des deux.
    """
    golds = [example.get(field, "?") for example in examples]
    by_class = {}
    for label in sorted(set(golds)):
        hits = sum(1 for g, p in zip(golds, predictions, strict=True) if g == p == label)
        predicted = sum(1 for p in predictions if p == label)
        support = golds.count(label)
        precision = hits / predicted if predicted else 0.0
        recall = hits / support
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        by_class[label] = {"precision": round(precision, 4), "recall": round(recall, 4),
                           "f1": round(f1, 4), "support": support}
    accuracy = sum(1 for g, p in zip(golds, predictions, strict=True) if g == p) / len(golds)
    macro_f1 = sum(c["f1"] for c in by_class.values()) / len(by_class)
    return {"n": len(golds), "accuracy": round(accuracy, 4), "macro_f1": round(macro_f1, 4),
            "by_class": by_class}


def save_results(lang: dict, script: dict | None, exp_id: str, model: str, split: str,
                 dataset: Path) -> Path:
    """Écrit les scores au format du tableau de bord ; renvoie le chemin du fichier."""
    try:
        shown = dataset.resolve().relative_to(REPO).as_posix()  # chemin lisible, sans le disque
    except ValueError:
        shown = dataset.as_posix()
    metrics = {"macro_f1": lang["macro_f1"], "accuracy": lang["accuracy"], "n": lang["n"],
               "by_lang": lang["by_class"]}
    if script is not None:
        metrics["script"] = script  # même structure, pour l'alphabet
    record = {"exp_id": exp_id, "lot": "A2", "task": "langid", "model": model, "split": split,
              "dataset": shown, "metrics": metrics}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"a2_langid_{model}_{date.today():%Y%m%d}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset", nargs="?", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--errors", action="store_true", help="liste chaque erreur")
    parser.add_argument("--save", action="store_true",
                        help="écrit les scores dans evaluation/results/ (tableau de bord)")
    parser.add_argument("--exp-id", help="entrée de experiments.md (obligatoire avec --save)")
    parser.add_argument("--split", default="dev", help="partie du jeu évaluée (défaut : dev)")
    parser.add_argument("--model", default="regles-ngrams", help="nom court du système évalué")
    args = parser.parse_args()
    if args.save and not args.exp_id:
        parser.error("--save demande --exp-id (ex. --exp-id EXP-A2-008)")

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
    # Le script n'est mesuré que si le jeu fournit cette étiquette (pas les fichiers TSV).
    has_script = all("script" in example for example in examples)
    if has_script:
        report(examples, scripts, "script")

    if args.errors:
        print("== erreurs ==")
        for example, lang, script in zip(examples, langs, scripts, strict=True):
            gold_lang = example.get("lang", "?")
            # Sans étiquette de script, on considère le script trouvé comme correct.
            gold_script = example.get("script", script)
            if (lang, script) != (gold_lang, gold_script):
                print(
                    f"  {example.get('id', '?'):7} "
                    f"attendu {gold_lang}/{gold_script}, obtenu {lang}/{script} : "
                    f"{example['text']}"
                )

    if args.save:
        lang_scores = scores(examples, langs, "lang")
        script_scores = scores(examples, scripts, "script") if has_script else None
        path = save_results(lang_scores, script_scores, args.exp_id, args.model, args.split,
                            args.dataset)
        print(f"résultats écrits : {path}")


if __name__ == "__main__":
    main()
