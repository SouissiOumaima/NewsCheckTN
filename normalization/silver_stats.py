"""Lot A2 — Silver : significativité, graines, baseline neuronale et courbe (EXP-A2-014).

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.silver_stats bootstrap
    python -X utf8 -m normalization.silver_stats seeds      # scikit-learn requis
    python -X utf8 -m normalization.silver_stats curve      # scikit-learn requis
    python -X utf8 -m normalization.silver_stats curve --seeds 13 42 2026 --figure FICHIER.png

Ce que fait `bootstrap` (rien n'est réglé, mesure seulement) :
- pour chaque jeu (eval_30, dev en lettres arabes, dev en lettres latines), calcule les prédictions
  du pipeline (`normalize`) et des deux baselines triviales d'EXP-A2-011 (alphabet seul, majorité) ;
- tire 1 000 rééchantillons des MÊMES exemples (bootstrap apparié, graine fixe) et, à chaque tirage,
  calcule le macro-F1 du système et de la baseline sur ce tirage ;
- donne l'écart observé, son intervalle de confiance à 95 % (percentiles 2,5 et 97,5) et la part des
  tirages où le système ne fait pas mieux (p unilatéral).

Ce que font `seeds` et `curve` (modèle arabizi / français, mêmes données que `train_langid`) :
- refont la préparation de `train_langid` (mêmes fonctions importées) avec plusieurs graines : la
  graine change les 10 % d'arabizi mis de côté et le découpage des phrases françaises ;
- `seeds` compare la régression logistique livrée (nettoyage, 20 000 poids, seuil) à une baseline
  neuronale (perceptron multicouche sur les MÊMES n-grammes), 3 graines, moyenne ± écart-type ;
- `curve` entraîne la régression logistique sur 10, 25, 50 et 100 % de l'apprentissage ;
- le seuil est choisi sur le français de dev (aucune fausse alerte, règle de `train_langid`) ; la
  mesure se fait sur l'arabizi mis de côté et sur le français de TEST, jamais utilisé pour choisir.
Rien n'est écrit dans `normalization/resources/` : le modèle en service n'est jamais modifié.
Seuls des scores sont affichés, jamais un texte.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections.abc import Callable
from pathlib import Path

from normalization.evaluate import DEFAULT_DATASET, REPO, load_examples
from normalization.normalize import normalize
from normalization.review import alphabet_baseline, majority_baseline
from normalization.silver_tuning import macro_f1

INTERIM = REPO / "data" / "interim" / "langid"
DATASETS = [
    ("eval_30 (test gelé)", DEFAULT_DATASET),
    ("dev lettres arabes", INTERIM / "tsac_arabic_sample_reference.tsv"),
    ("dev lettres latines", INTERIM / "tsac_latin_sample_reference.tsv"),
]
N_BOOT = 1000
SEED = 20261115  # graine du bootstrap, fixée avant le calcul

SEEDS = (13, 42, 2026)  # 13 = graine du modèle livré (EXP-A2-006) ; 42 et 2026 fixées avant calcul
FRACTIONS = (0.10, 0.25, 0.50, 1.00)  # parts de l'apprentissage pour la courbe
MLP_THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999)  # seuils sur la probabilité arabizi


def label(value: object) -> str:
    """Valeur lisible d'une énumération (Lang.TN -> « tn »)."""
    return str(getattr(value, "value", value))


def paired_bootstrap(
    golds: list[str], system: list[str], baseline: list[str], n_boot: int, seed: int
) -> dict:
    """Écart de macro-F1 (système - baseline), IC à 95 % et p unilatéral, sur les mêmes tirages."""
    rng = random.Random(seed)
    n = len(golds)
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]  # tirage avec remise, le même pour les deux
        g = [golds[i] for i in idx]
        score_system = macro_f1(g, [system[i] for i in idx])
        diffs.append(score_system - macro_f1(g, [baseline[i] for i in idx]))
    diffs.sort()
    return {
        "diff": macro_f1(golds, system) - macro_f1(golds, baseline),
        "low": diffs[int(0.025 * n_boot)],
        "high": diffs[int(0.975 * n_boot) - 1],
        "p": sum(d <= 0 for d in diffs) / n_boot,
    }


def command_bootstrap() -> None:
    print(f"bootstrap apparié : {N_BOOT} tirages, graine {SEED}\n")
    for name, path in DATASETS:
        if not path.exists():
            print(f"{name} : fichier absent, ignoré ({path})")
            continue
        examples = load_examples(path)
        golds = [e["lang"] for e in examples]
        texts = [e["text"] for e in examples]
        system = [label(normalize(t).lang) for t in texts]
        print(f"{name} (N = {len(examples)}) : macro-F1 système {macro_f1(golds, system):.2f}")
        for base_name, baseline in (("alphabet seul", alphabet_baseline(texts)),
                                    ("majorité", majority_baseline(golds))):
            r = paired_bootstrap(golds, system, baseline, N_BOOT, SEED)
            print(f"  contre {base_name:13} : baseline {macro_f1(golds, baseline):.2f} ;"
                  f" écart {r['diff']:+.2f} [IC 95 % {r['low']:+.2f} ; {r['high']:+.2f}] ;"
                  f" p = {r['p']:.3f}")
        print()


# --- Graines, baseline neuronale, courbe d'apprentissage ----------------------------------


def mean_std(values: list[float]) -> tuple[float, float]:
    """Moyenne et écart-type (échantillon) ; écart-type nul s'il n'y a qu'une valeur."""
    mean = statistics.mean(values)
    return mean, (statistics.stdev(values) if len(values) > 1 else 0.0)


def choose_threshold(french_dev_scores: list[float], thresholds, max_false_alarm: float = 0.0):
    """Règle de `train_langid` : plus petit seuil sans fausse alerte sur le français de dev."""
    for threshold in thresholds:
        rate = sum(s >= threshold for s in french_dev_scores) / len(french_dev_scores)
        if rate <= max_false_alarm:
            return threshold
    return thresholds[-1]  # repli : aucun seuil ne tient le critère, on garde le plus haut


def binary_scores(
    arabizi_scores: list[float], french_scores: list[float], threshold: float
) -> dict:
    """Macro-F1 arabizi / français, rappel de l'arabizi et fausses alertes, à un seuil donné."""
    golds = ["arabizi"] * len(arabizi_scores) + ["fr"] * len(french_scores)
    preds = ["arabizi" if s >= threshold else "fr" for s in arabizi_scores + french_scores]
    return {
        "macro_f1": macro_f1(golds, preds),
        "rappel": sum(s >= threshold for s in arabizi_scores) / len(arabizi_scores),
        "alertes": sum(s >= threshold for s in french_scores),
        "n_fr": len(french_scores),
        "seuil": threshold,
    }


def short_versions(prepared: list[str]) -> list[str]:
    """Phrases complètes + leurs 5 premiers mots (taille d'un commentaire), comme train_langid."""
    return prepared + [" ".join(s.split()[:5]) for s in prepared if len(s.split()) >= 5]


def load_pool() -> dict:
    """Charge et prépare UNE fois les données de `train_langid` (le plus long)."""
    from normalization import train_langid as tl

    sample = []
    if tl.SAMPLE.exists():
        for line in tl.read_lines(tl.SAMPLE):
            sample.append(tl.prepare(line.partition("\t")[2]))
    return {
        "arabizi": tl.unique_prepared(tl.load_arabizi(), set(sample)),  # sans l'échantillon annoté
        "french_train": tl.load_french("train"),
        "french_dev": short_versions([tl.prepare(s) for s in tl.load_french("dev")]),
        "french_test": short_versions([tl.prepare(s) for s in tl.load_french("test")]),
    }


def split(pool: dict, seed: int, fraction: float = 1.0) -> dict:
    """Même découpage que `train_langid.main`, avec la graine donnée.

    Les 10 % d'arabizi mis de côté ne dépendent que de la graine : la courbe d'apprentissage
    mesure donc toutes les fractions sur les MÊMES textes.
    """
    from normalization import train_langid as tl

    rng = random.Random(seed)
    arabizi = list(pool["arabizi"])
    rng.shuffle(arabizi)
    n_dev = len(arabizi) // 10
    arabizi_dev, arabizi_train = arabizi[:n_dev], arabizi[n_dev:]
    lengths = [len(t.split()) for t in arabizi_train]
    french_train = tl.cut_like_comments(pool["french_train"], lengths, rng)
    if fraction < 1.0:
        rng.shuffle(french_train)  # sous-échantillon aléatoire, reproductible
        arabizi_train = arabizi_train[: max(1, int(fraction * len(arabizi_train)))]
        french_train = french_train[: max(1, int(fraction * len(french_train)))]
    return {"ar_train": arabizi_train, "fr_train": french_train, "ar_dev": arabizi_dev}


def train_logreg(ar_train: list[str], fr_train: list[str]) -> Callable[[list[str]], list[float]]:
    """Le modèle livré : régression logistique, nettoyage, 20 000 poids les plus forts.

    Mêmes étapes que `train_langid.main` (2 et 3), sans rien écrire sur le disque.
    """
    from normalization import train_langid as tl

    weights, intercept = tl.fit(ar_train, fr_train)
    kept = [t for t in ar_train if tl.score(t, weights, intercept) >= -2.0]
    weights, intercept = tl.fit(kept, fr_train)
    strongest = sorted(weights.items(), key=lambda item: -abs(item[1]))[: tl.MAX_WEIGHTS]
    exported = {gram: round(w, 4) for gram, w in strongest}
    intercept = round(intercept, 4)
    return lambda texts: [tl.score(t, exported, intercept) for t in texts]


def train_mlp(
    ar_train: list[str], fr_train: list[str], seed: int
) -> Callable[[list[str]], list[float]]:
    """Baseline neuronale : perceptron multicouche (64 neurones), mêmes n-grammes binaires."""
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.neural_network import MLPClassifier

    from normalization import train_langid as tl

    vectorizer = CountVectorizer(analyzer=tl.analyzer, binary=True, min_df=tl.MIN_TEXTS)
    features = vectorizer.fit_transform(ar_train + fr_train)
    labels = [1] * len(ar_train) + [0] * len(fr_train)
    model = MLPClassifier(
        hidden_layer_sizes=(64,),
        batch_size=256,
        max_iter=20,  # arrêt anticipé sur 10 % de l'apprentissage (jamais sur la mesure)
        early_stopping=True,
        n_iter_no_change=3,
        random_state=seed,  # la graine fixe aussi l'initialisation du réseau
    )
    model.fit(features, labels)
    return lambda texts: list(model.predict_proba(vectorizer.transform(texts))[:, 1])


def evaluate(scorer, thresholds, pool: dict, data: dict) -> dict:
    """Seuil choisi sur le français de dev, puis mesure sur l'arabizi mis de côté et le test."""
    threshold = choose_threshold(scorer(pool["french_dev"]), thresholds)
    return binary_scores(scorer(data["ar_dev"]), scorer(pool["french_test"]), threshold)


def print_row(name: str, results: list[dict]) -> None:
    """Une ligne : moyenne ± écart-type sur les graines."""
    f1, f1_sd = mean_std([r["macro_f1"] for r in results])
    rec, rec_sd = mean_std([r["rappel"] for r in results])
    alarms, alarms_sd = mean_std([float(r["alertes"]) for r in results])
    print(f"  {name:32} macro-F1 {f1:.3f} ± {f1_sd:.3f} ; rappel arabizi {rec:.3f} ± {rec_sd:.3f} ;"
          f" fausses alertes {alarms:.1f} ± {alarms_sd:.1f} / {results[0]['n_fr']}")


def command_seeds() -> None:
    from normalization import train_langid as tl

    pool = load_pool()
    print(f"données : {len(pool['arabizi'])} textes arabizi ; français dev"
          f" {len(pool['french_dev'])}, test {len(pool['french_test'])}"
          " (phrases + 5 premiers mots)\n")
    logreg, mlp = [], []
    for seed in SEEDS:
        data = split(pool, seed)
        logreg.append(evaluate(train_logreg(data["ar_train"], data["fr_train"]),
                               tl.THRESHOLDS, pool, data))
        mlp.append(evaluate(train_mlp(data["ar_train"], data["fr_train"], seed),
                            MLP_THRESHOLDS, pool, data))
        for name, r in (("régression logistique", logreg[-1]), ("perceptron multicouche", mlp[-1])):
            print(f"graine {seed:4} | {name:22} | seuil {r['seuil']:<5} | macro-F1"
                  f" {r['macro_f1']:.3f} | rappel {r['rappel']:.3f} | alertes {r['alertes']}")
    print(f"\nmoyenne ± écart-type sur {len(SEEDS)} graines {SEEDS} :")
    print_row("régression logistique (livrée)", logreg)
    print_row("perceptron multicouche (neur.)", mlp)


def command_curve(seeds: list[int], figure: Path | None) -> None:
    from normalization import train_langid as tl

    pool = load_pool()
    print(f"courbe d'apprentissage, régression logistique, graines {tuple(seeds)}\n")
    points = []
    for fraction in FRACTIONS:
        results, sizes = [], None
        for seed in seeds:
            data = split(pool, seed, fraction)
            sizes = (len(data["ar_train"]), len(data["fr_train"]))
            results.append(evaluate(train_logreg(data["ar_train"], data["fr_train"]),
                                    tl.THRESHOLDS, pool, data))
        f1, f1_sd = mean_std([r["macro_f1"] for r in results])
        points.append((fraction, f1, f1_sd))
        print_row(f"{fraction:4.0%} ({sizes[0]} ar., {sizes[1]} fr.)", results)
    if figure:
        import matplotlib

        matplotlib.use("Agg")  # pas de fenêtre : on écrit seulement le fichier
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 3.2))
        ax.errorbar([100 * p[0] for p in points], [p[1] for p in points],
                    yerr=[p[2] for p in points], marker="o", capsize=3)
        ax.set_xlabel("part de l'apprentissage (%)")
        ax.set_ylabel("macro-F1 (arabizi / français)")
        ax.set_title("Lot A2 — courbe d'apprentissage (EXP-A2-014)")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(figure, dpi=150)
        print(f"\nfigure écrite : {figure}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # accents lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("bootstrap", help="IC à 95 % de l'écart système - baselines")
    commands.add_parser("seeds", help="3 graines : modèle livré contre baseline neuronale")
    curve = commands.add_parser("curve", help="courbe d'apprentissage (10 à 100 %)")
    curve.add_argument("--seeds", type=int, nargs="+", default=[SEEDS[0]])
    curve.add_argument("--figure", type=Path, default=None, help="fichier PNG (facultatif)")
    args = parser.parse_args()
    if args.command == "bootstrap":
        command_bootstrap()
    elif args.command == "seeds":
        command_seeds()
    else:
        command_curve(args.seeds, args.figure)


if __name__ == "__main__":
    main()
