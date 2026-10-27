"""Lot A2 — Perplexité : repérer les textes bruités avec un modèle de langue à n-grammes.

Usage (depuis la racine du dépôt, corpus locaux de data/raw/langid/ nécessaires) :
    python -m normalization.perplexity            # entraîne, mesure, enregistre le modèle

Principe (chapitre 6 : n-grammes et perplexité) : un modèle de langue appris sur des
commentaires réels donne une probabilité à chaque caractère selon les précédents. La
perplexité d'un texte est la « surprise moyenne » du modèle : basse pour un texte qui
ressemble aux commentaires vus, haute pour un texte cassé (encodage abîmé, lettres au
hasard). Un modèle par alphabet : lettres arabes, lettres latines.

Le modèle est appris sur des commentaires (TSAC, Tunizi), pas sur de la presse : sinon le
tunisien lui-même paraîtrait « bruité ». Il mesure donc l'écart à un commentaire ordinaire,
pas l'écart à la langue standard.

Sortie : data/interim/langid/perplexity_model.pkl (non versionné). Sans ce fichier,
perplexity() et is_noisy() renvoient None.
"""

from __future__ import annotations

import csv
import math
import pickle
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path

from normalization.normalize import normalize

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw" / "langid"
MODEL_FILE = REPO / "data" / "interim" / "langid" / "perplexity_model.pkl"

ORDER = 4  # contexte de 3 caractères pour prédire le 4e
WEIGHTS = (0.1, 0.2, 0.3, 0.4)  # poids des ordres 1 à 4 (interpolation), somme = 1
SEED = 13  # même graine que le reste du lot
FALSE_ALARM = 0.05  # seuil = 95e centile des textes propres de dev : 5 % de fausses alertes
START, END = "\x02", "\x03"  # marques de début et de fin de texte


class CharNgramModel:
    """Modèle de langue à n-grammes de caractères, ordres 1 à ORDER interpolés.

    P(c | contexte) = somme des poids × fréquence relative à chaque ordre ; l'ordre 1
    est lissé (add-one) pour qu'aucun caractère n'ait une probabilité nulle.
    """

    def __init__(self) -> None:
        self.counts = [Counter() for _ in range(ORDER)]  # (contexte, caractère) par ordre
        self.contexts = [Counter() for _ in range(ORDER)]  # contexte seul, par ordre
        self.vocabulary: set[str] = set()

    def fit(self, texts: list[str]) -> CharNgramModel:
        for text in texts:
            padded = START * (ORDER - 1) + text + END
            for i in range(ORDER - 1, len(padded)):
                char = padded[i]
                self.vocabulary.add(char)
                for n in range(ORDER):  # n = longueur du contexte (0 à ORDER - 1)
                    context = padded[i - n:i]
                    self.counts[n][(context, char)] += 1
                    self.contexts[n][context] += 1
        return self

    def log_prob(self, context: str, char: str) -> float:
        size = len(self.vocabulary) + 1  # +1 : place pour un caractère jamais vu
        prob = 0.0
        for n, weight in enumerate(WEIGHTS):
            ctx = context[len(context) - n:] if n else ""
            seen = self.contexts[n][ctx]
            if n == 0:
                prob += weight * (self.counts[0][("", char)] + 1) / (seen + size)
            elif seen:
                prob += weight * self.counts[n][(ctx, char)] / seen
        return math.log(prob)

    def perplexity(self, text: str) -> float:
        padded = START * (ORDER - 1) + text + END
        logs = [self.log_prob(padded[i - ORDER + 1:i], padded[i])
                for i in range(ORDER - 1, len(padded))]
        return math.exp(-sum(logs) / len(logs))


def prepare(text: str) -> str:
    """Texte du pipeline (normalize), en minuscules, sans emojis ni symboles.

    Les emojis et les symboles ne disent rien de la langue : gardés, ils rendaient
    « surprenant » un commentaire ordinaire suivi de quelques emojis.
    """
    kept = (c if c.isalnum() or c in " '" else " " for c in normalize(text).text.lower())
    return " ".join("".join(kept).split())


def script_of(prepared: str) -> str | None:
    """« arabic » ou « latin » selon la part de lettres arabes ; None si mêlé ou sans lettre.

    Compte fait ici, sans dépendre d'une fonction interne du normaliseur.
    """
    arabic = sum("\u0600" <= c <= "\u06ff" for c in prepared)  # lettres du bloc arabe
    latin = sum(c.isalpha() for c in prepared) - arabic  # toutes les autres lettres
    if arabic + latin == 0:
        return None
    share = arabic / (arabic + latin)
    if share >= 0.9:
        return "arabic"
    return "latin" if share <= 0.1 else None


# ---------------------------------------------------------------------------
# Usage dans le pipeline
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_model() -> dict | None:
    """Modèles et seuils enregistrés par l'entraînement ; None si le fichier est absent."""
    if not MODEL_FILE.exists():
        return None
    with MODEL_FILE.open("rb") as handle:
        saved = pickle.load(handle)  # fichier produit sur cette machine par main()
    models = {}
    for script, state in saved["models"].items():
        models[script] = CharNgramModel()
        models[script].__dict__.update(state)  # compteurs enregistrés en dictionnaires simples
    return {"models": models, "thresholds": saved["thresholds"]}


def perplexity(text: str) -> float | None:
    """Perplexité du texte pour le modèle de son alphabet ; None si elle ne s'applique pas."""
    saved, prepared = load_model(), prepare(text)
    script = script_of(prepared)
    if saved is None or script is None or not prepared.strip():
        return None
    return saved["models"][script].perplexity(prepared)


def is_noisy(text: str) -> bool | None:
    """True si la perplexité dépasse le seuil de l'alphabet ; None si non mesurable."""
    saved, value = load_model(), perplexity(text)
    if value is None:
        return None
    return value > saved["thresholds"][script_of(prepare(text))]


# ---------------------------------------------------------------------------
# Entraînement et mesure
# ---------------------------------------------------------------------------

def load_comments() -> dict[str, list[str]]:
    """Commentaires TSAC et Tunizi préparés, sans doublon, rangés par alphabet."""
    texts = []
    for name in ("train_pos.txt", "train_neg.txt", "test_pos.txt", "test_neg.txt"):
        with (RAW / "TSAC" / name).open(encoding="utf-8-sig", errors="replace") as handle:
            texts += [line.strip() for line in handle]
    with (RAW / "tunizi_train").open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        texts += [row["text"] for row in csv.DictReader(handle)]
    by_script: dict[str, list[str]] = {"arabic": [], "latin": []}
    for prepared in dict.fromkeys(prepare(t) for t in texts if t.strip()):
        script = script_of(prepared)
        if script and len(prepared.split()) >= 3:  # 3 mots ou plus, comme les échantillons
            by_script[script].append(prepared)
    return by_script


def corrupt(text: str, kind: str, rng: random.Random, alphabet: list[str]) -> str:
    """Bruit artificiel, pour savoir si la perplexité le repère."""
    if kind == "encodage":  # UTF-8 relu comme Windows-1252 : « Ø§Ù„ », « Ã© »
        return text.encode("utf-8").decode("cp1252", errors="replace")
    if kind == "lettres":  # 30 % des lettres remplacées au hasard
        return "".join(rng.choice(alphabet) if c.isalpha() and rng.random() < 0.3 else c
                       for c in text)
    words = text.split()  # « melange » : lettres de chaque mot mélangées
    return " ".join("".join(rng.sample(w, len(w))) for w in words)


def auc(clean: list[float], noisy: list[float]) -> float:
    """Probabilité qu'un texte bruité ait une perplexité plus haute qu'un texte propre."""
    wins = sum((n > c) + 0.5 * (n == c) for n in noisy for c in clean)
    return wins / (len(noisy) * len(clean))


def main() -> None:
    rng = random.Random(SEED)
    saved = {"models": {}, "thresholds": {}}
    for script, texts in load_comments().items():
        rng.shuffle(texts)
        n = len(texts) // 10  # 80 % apprendre, 10 % régler le seuil, 10 % tester
        test, dev, train = texts[:n], texts[n:2 * n], texts[2 * n:]
        model = CharNgramModel().fit(train)
        dev_scores = sorted(model.perplexity(t) for t in dev)
        threshold = dev_scores[int((1 - FALSE_ALARM) * len(dev_scores))]
        # On enregistre les compteurs (vars), pas l'objet : le fichier reste lisible
        # quel que soit le nom du module qui l'a écrit.
        saved["models"][script], saved["thresholds"][script] = vars(model), threshold
        alphabet = sorted({c for t in train[:2000] for c in t if c.isalpha()})
        sample = test[:1000]  # 1 000 textes de test suffisent pour mesurer
        clean = [model.perplexity(t) for t in sample]
        print(f"== {script} : {len(train)} pour apprendre, {len(dev)} dev, {len(test)} test ==")
        print(f"  seuil (95e centile dev) : {threshold:.1f}")
        print(f"  textes propres signalés : {sum(v > threshold for v in clean) / len(clean):.1%}")
        for kind in ("encodage", "lettres", "melange"):
            noisy = [model.perplexity(corrupt(t, kind, rng, alphabet)) for t in sample]
            caught = sum(v > threshold for v in noisy) / len(noisy)
            area = auc(clean[:300], noisy[:300])
            print(f"  bruit « {kind} » : repéré {caught:.1%} | AUC {area:.3f}")
        worst = sorted(dev, key=model.perplexity, reverse=True)[:5]
        print("  textes réels les plus « surprenants » (dev) :")
        for text in worst:
            print(f"    {model.perplexity(text):8.1f}  {text[:80]}")
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_FILE.open("wb") as handle:
        pickle.dump(saved, handle)
    load_model.cache_clear()
    print(f"modèle écrit : {MODEL_FILE}")


if __name__ == "__main__":
    main()
