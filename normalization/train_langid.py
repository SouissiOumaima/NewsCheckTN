"""Lot A2 — Entraînement du modèle français / arabizi (à lancer hors ligne).

Usage (depuis la racine du dépôt, avec scikit-learn installé) :
    python -m normalization.train_langid

Données attendues dans data/raw/langid/ (non versionnées) :
    tunizi_train      Tunizi (Zenodo, CC BY 4.0) : commentaires en arabizi
    TSAC/             TSAC (GitHub, LGPL-3.0) : commentaires Facebook tunisiens
    UD_French-GSD/    UD French-GSD (GitHub, CC BY-SA 4.0) : phrases françaises

Sortie : normalization/resources/arabizi_ngrams.json, un poids par n-gramme de
caractères. Ce petit fichier est versionné ; il est lu par langid.py, qui n'a
besoin d'aucune bibliothèque pour s'en servir.

Le script est déterministe : mêmes données et même graine = même modèle.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from normalization import langid
from normalization.normalize import ARABIZI_DIGITS_V1, detect_script_by_rules, normalize

RAW = Path("data/raw/langid")
SAMPLE = Path("data/interim/langid/tsac_latin_sample.tsv")  # annoté à la main, jamais appris
OUTPUT = Path("normalization/resources/arabizi_ngrams.json")

SEED = 13  # graine unique pour tous les tirages aléatoires
NGRAM_RANGE = (1, 4)  # morceaux de 1 à 4 caractères
MIN_TEXTS = 5  # un n-gramme vu dans moins de 5 textes est ignoré (bruit)
MAX_WEIGHTS = 20000  # on ne garde que les poids les plus forts (fichier < 1 Mo)
MAX_FALSE_ALARM = 0.0  # aucun texte français de mesure ne doit être classé arabizi
THRESHOLDS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


def prepare(text: str) -> str:
    """Même préparation qu'à l'usage : normalisation du pipeline, puis lettres seules."""
    return langid.prepare_latin(normalize(text).text)


def analyzer(prepared: str) -> list[str]:
    """Découpage en n-grammes : exactement la fonction utilisée par langid.py."""
    return langid.char_ngrams(prepared, *NGRAM_RANGE)


def read_lines(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", errors="replace") as handle:
        return [line.strip() for line in handle if line.strip()]


def load_arabizi() -> list[str]:
    """Arabizi : tout Tunizi, plus les lignes de TSAC reconnues par la règle à chiffres."""
    with (RAW / "tunizi_train").open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        texts = [row["text"] for row in csv.DictReader(handle)]
    for name in ("train_pos.txt", "train_neg.txt", "test_pos.txt", "test_neg.txt"):
        # Règles seules : le choix des exemples ne doit pas dépendre d'un modèle déjà entraîné.
        lines = read_lines(RAW / "TSAC" / name)
        # Règle d'origine, sans le 8 : les exemples (donc le modèle) restent ceux d'EXP-A2-006.
        texts += [
            t for t in lines
            if detect_script_by_rules(normalize(t).text, digits=ARABIZI_DIGITS_V1) == "arabizi"
        ]
    return texts


def load_french(split: str) -> list[str]:
    """Phrases françaises : lignes '# text = ...' du fichier UD (train, dev ou test)."""
    path = RAW / "UD_French-GSD" / f"fr_gsd-ud-{split}.conllu"
    with path.open(encoding="utf-8") as handle:
        return [line[len("# text = "):].strip() for line in handle if line.startswith("# text = ")]


def unique_prepared(texts: list[str], exclude: set[str]) -> list[str]:
    """Prépare les textes, retire les doublons, les textes trop courts et les exclus."""
    prepared = dict.fromkeys(prepare(text) for text in texts)  # garde l'ordre, retire les doublons
    return [p for p in prepared if len(p.split()) >= 2 and p not in exclude]


def cut_like_comments(sentences: list[str], lengths: list[int], rng: random.Random) -> list[str]:
    """Découpe des phrases de presse en morceaux de la longueur des commentaires.

    Sans cela, le modèle pourrait apprendre "texte long = français" au lieu
    d'apprendre la langue.
    """
    chunks = []
    for sentence in sentences:
        words = prepare(sentence).split()
        start = 0
        while start < len(words):
            size = rng.choice(lengths)
            if len(words[start:start + size]) >= 3:
                chunks.append(" ".join(words[start:start + size]))
            start += size
    return chunks


def fit(arabizi: list[str], french: list[str]):
    """Entraîne une régression logistique sur la présence des n-grammes."""
    # Imports ici : scikit-learn n'est nécessaire que pour l'entraînement.
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    # binary=True : on note si un n-gramme est présent, pas combien de fois.
    vectorizer = CountVectorizer(analyzer=analyzer, binary=True, min_df=MIN_TEXTS)
    features = vectorizer.fit_transform(arabizi + french)
    labels = [1] * len(arabizi) + [0] * len(french)
    # class_weight="balanced" : les deux langues pèsent autant, quelle que soit leur taille.
    model = LogisticRegression(C=0.5, class_weight="balanced", max_iter=3000, random_state=SEED)
    model.fit(features, labels)
    weights = dict(zip(vectorizer.get_feature_names_out(), model.coef_[0], strict=True))
    return {gram: float(weight) for gram, weight in weights.items()}, float(model.intercept_[0])


def score(prepared: str, weights: dict[str, float], intercept: float) -> float:
    """Même calcul que langid.arabizi_score : somme des poids des n-grammes présents."""
    return intercept + sum(weights.get(gram, 0.0) for gram in set(analyzer(prepared)))


def rate(scores: list[float], threshold: float) -> float:
    """Part des textes dont le score atteint le seuil (donc classés arabizi)."""
    return sum(1 for value in scores if value >= threshold) / len(scores)


def main(output: Path = OUTPUT) -> None:
    rng = random.Random(SEED)

    # --- 1. Données -------------------------------------------------------
    sample = []  # (étiquette, texte préparé) de l'échantillon annoté à la main
    if SAMPLE.exists():
        for line in read_lines(SAMPLE):
            label, _, text = line.partition("\t")
            sample.append((label.strip().lower(), prepare(text)))
    never_learn = {text for _, text in sample}

    arabizi = unique_prepared(load_arabizi(), never_learn)
    rng.shuffle(arabizi)
    n_dev = len(arabizi) // 10  # 10 % mis de côté pour mesurer, jamais appris
    arabizi_dev, arabizi_train = arabizi[:n_dev], arabizi[n_dev:]

    lengths = [len(text.split()) for text in arabizi_train]
    french_train = cut_like_comments(load_french("train"), lengths, rng)
    french_dev = [prepare(s) for s in load_french("dev")]
    french_dev_short = [" ".join(s.split()[:5]) for s in french_dev if len(s.split()) >= 5]
    print(f"arabizi : {len(arabizi_train)} pour apprendre, {len(arabizi_dev)} pour mesurer")
    print(f"français : {len(french_train)} morceaux pour apprendre,"
          f" {len(french_dev)} phrases pour mesurer")

    # --- 2. Premier passage, puis nettoyage -------------------------------
    # Les corpus d'arabizi contiennent quelques commentaires en français.
    # On entraîne une première fois, on retire les textes "arabizi" que le
    # modèle juge nettement français, puis on réentraîne sur le reste.
    weights, intercept = fit(arabizi_train, french_train)
    kept = [t for t in arabizi_train if score(t, weights, intercept) >= -2.0]
    removed = [t for t in arabizi_train if score(t, weights, intercept) < -2.0]
    print(f"nettoyage : {len(removed)} textes 'arabizi' retirés car jugés français, par exemple :")
    for text in removed[:8]:
        print(f"    {text[:90]}")
    weights, intercept = fit(kept, french_train)

    # --- 3. Export : on ne garde que les poids les plus forts --------------
    strongest = sorted(weights.items(), key=lambda item: -abs(item[1]))[:MAX_WEIGHTS]
    exported = {gram: round(weight, 4) for gram, weight in sorted(strongest)}
    intercept = round(intercept, 4)

    # --- 4. Choix du seuil, mesuré avec le modèle EXPORTÉ ------------------
    french_scores = [score(t, exported, intercept) for t in french_dev + french_dev_short]
    arabizi_scores = [score(t, exported, intercept) for t in arabizi_dev]
    print()
    print("seuil | français classé arabizi (à éviter) | arabizi retrouvé")
    for threshold in THRESHOLDS:
        print(f"  {threshold:3.1f} | {rate(french_scores, threshold):6.2%}"
              f" | {rate(arabizi_scores, threshold):6.2%}")
    # Le plus petit seuil pour lequel aucun texte français de mesure n'est classé arabizi.
    allowed = [t for t in THRESHOLDS if rate(french_scores, t) <= MAX_FALSE_ALARM]
    if allowed:
        threshold = allowed[0]
        print(f"seuil retenu : {threshold}")
    else:
        # Aucun seuil ne tient le critère : on garde le plus haut, et on le dit.
        threshold = THRESHOLDS[-1]
        print(f"seuil retenu : {threshold} (repli : aucun seuil n'atteint"
              f" {MAX_FALSE_ALARM:.2%} de français classé arabizi)")

    model = {
        "description": "Poids par n-gramme de caractères : positif = arabizi, négatif = français.",
        "sources": "Tunizi (CC BY 4.0), TSAC (LGPL-3.0), UD French-GSD (CC BY-SA 4.0)",
        "seed": SEED,
        "ngram_range": list(NGRAM_RANGE),
        "intercept": intercept,
        "threshold": threshold,
        "weights": exported,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(model, handle, ensure_ascii=False, indent=0, sort_keys=True)
        handle.write("\n")
    size = output.stat().st_size / 1024
    print(f"modèle écrit : {output} ({len(exported)} poids, {size:.0f} Ko)")
    if output.resolve() != OUTPUT.resolve():
        # Écrit ailleurs (test de régénération) : langid lit toujours le fichier du dépôt,
        # les mesures ci-dessous porteraient donc sur un autre modèle. On s'arrête ici.
        return
    langid.load_arabizi_model.cache_clear()  # force langid à relire le nouveau fichier

    # --- 5. Mesures finales, avec la fonction réellement livrée ------------
    test = [prepare(s) for s in load_french("test")]
    wrong = sum(1 for text in test if langid.is_arabizi_text(text))
    print(f"français, fichier de test jamais consulté : {wrong} classé(s) arabizi sur {len(test)}")
    found = sum(1 for text in arabizi_dev if langid.is_arabizi_text(text))
    print(f"arabizi mis de côté : {found} retrouvés sur {len(arabizi_dev)}")
    for name, label in (("tunisien (t)", "t"), ("français (f)", "f")):
        rows = [text for tag, text in sample if tag == label]
        if rows:
            as_arabizi = sum(1 for text in rows if langid.is_arabizi_text(text))
            print(f"échantillon annoté, {name} : {as_arabizi} classé(s) arabizi sur {len(rows)}")

    # --- 6. Que regarde le modèle ? ---------------------------------------
    ordered = sorted(exported.items(), key=lambda item: item[1])
    print("n-grammes les plus français :", " ".join(repr(g) for g, _ in ordered[:25]))
    print("n-grammes les plus arabizi  :", " ".join(repr(g) for g, _ in ordered[-25:]))


if __name__ == "__main__":
    main()
