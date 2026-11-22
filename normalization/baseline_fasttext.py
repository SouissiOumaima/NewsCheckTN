"""Lot A2 — Gold, EXP-A2-017 : baseline externe fastText lid.176 (dev seulement).

Protocole : docs/lot-a2_protocole_gold.md, §6.

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.baseline_fasttext --out-dir <dossier hors dépôt>

Modèle : models/checkpoints/lid.176.bin (non versionné), téléchargé depuis
https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin ; empreinte vérifiée.
Le paquet `fasttext` n'est importé qu'au chargement du modèle : jamais par normalize().

Correspondance (fixée au §6) : ar, arz -> ar ; fr -> fr ; toute autre étiquette -> autre.
lid.176 n'a pas d'étiquette tunisienne : son rappel tn est nul par construction.
Chiffre informatif séparé : part des textes de référence `t` étiquetés `arz` (arabe égyptien).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from normalization.evaluate import REPO, load_examples, scores
from normalization.gold_common import (
    BOOTSTRAP_DRAWS,
    SEED,
    check_file,
    check_out_dir,
    error_record,
    git_state,
    paired_bootstrap,
    proportion,
    safe_main,
    write_json,
)

DEFAULT_MODEL = REPO / "models" / "checkpoints" / "lid.176.bin"
MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
# Empreinte du fichier téléchargé le 2026-11-22 (131 266 198 octets).
MODEL_SHA256 = "7e69ec5451bc261cc7844e49e4792a85d7f09c06789ec800fc4a44aec362764e"
MAPPING = {"ar": "ar", "arz": "ar", "fr": "fr"}


def map_label(raw: str) -> str:
    """Étiquette lid.176 (sans « __label__ ») -> code du projet (§6)."""
    return MAPPING.get(raw, "autre")


def top_label(model, text: str) -> str:
    """Étiquette brute la plus probable.

    On appelle `model.f.predict` (la fonction C++) plutôt que `model.predict` : avec numpy 2,
    `model.predict` de fasttext 0.9.2 lève ValueError (copy=False). fastText refuse aussi les
    retours à la ligne : on les remplace par des espaces.
    """
    line = text.replace("\r", " ").replace("\n", " ")
    predictions = model.f.predict(line, 1, 0.0, "replace")
    return predictions[0][1].removeprefix("__label__") if predictions else "autre"


def load_model(path: Path = DEFAULT_MODEL, expected: str = MODEL_SHA256):
    """Vérifie l'empreinte, PUIS importe fasttext et charge le modèle."""
    check_file("modèle lid.176", path, expected)
    import fasttext  # import paresseux : dépendance d'évaluation seulement

    fasttext.FastText.eprint = lambda *args, **kwargs: None  # avertissement de chargement
    return fasttext.load_model(str(path))


def make_predictor(model) -> Callable[[list[str]], list[str]]:
    """Prédicteur au format des scripts Gold : textes -> codes ar / fr / autre."""
    return lambda texts: [map_label(top_label(model, t)) for t in texts]


def load_predictor(path: Path = DEFAULT_MODEL) -> Callable[[list[str]], list[str]]:
    return make_predictor(load_model(path))


# ---------------------------------------------------------------------------
# Mesure EXP-A2-017
# ---------------------------------------------------------------------------

def compare(examples: list[dict], dataset: str, model,
            rules: Callable[[list[str]], list[str]], draws: int = BOOTSTRAP_DRAWS,
            seed: int = SEED) -> dict:
    """Scores de fastText et des règles, écart apparié règles − fastText, part de t -> arz."""
    errors: list[dict] = []
    kept, raw, ours = [], [], []
    for ex in examples:
        try:
            label = top_label(model, ex["text"])
            mine = rules([ex["text"]])[0]
        except Exception as exc:
            errors.append(error_record(dataset, ex["id"], exc))
            continue
        kept.append(ex)
        raw.append(label)
        ours.append(mine)
    golds = [ex["lang"] for ex in kept]
    mapped = [map_label(r) for r in raw]
    tn_raw = [r for g, r in zip(golds, raw, strict=True) if g == "tn"]
    result = {
        "n": len(kept),
        "fasttext": _score(golds, mapped),
        "regles": _score(golds, ours),
        "etiquettes_brutes": _counts(raw),
        "t_etiquetes_arz": proportion(sum(r == "arz" for r in tn_raw), len(tn_raw)),
        "erreurs": errors,
    }
    if kept:
        # « avant » = fastText, « après » = règles : l'écart vaut règles − fastText.
        result["regles_moins_fasttext"] = paired_bootstrap(golds, mapped, ours, draws, seed)
    return result


def _score(golds: list[str], predictions: list[str]) -> dict:
    if not golds:
        return {"n": 0}
    result = scores([{"lang": g} for g in golds], predictions, "lang")
    return {"n": result["n"], "exactitude": result["accuracy"], "macro_f1": result["macro_f1"],
            "par_classe": result["by_class"]}


def _counts(labels: list[str]) -> dict[str, int]:
    """Effectifs par étiquette brute (aucun texte)."""
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def run(argv: list[str] | None = None) -> None:
    # Import local : gold_robustness importe ce module pour son branchement fastText.
    from normalization.gold_robustness import DEV_SETS, rules_predictor

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie HORS du dépôt (obligatoire)")
    parser.add_argument("--modele", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--dev-arabe", type=Path, default=DEV_SETS["arabe"][0])
    parser.add_argument("--dev-latin", type=Path, default=DEV_SETS["latin"][0])
    args = parser.parse_args(argv)

    out_dir = check_out_dir(args.out_dir)  # avant toute lecture
    paths = {"arabe": args.dev_arabe, "latin": args.dev_latin}
    digests = {name: check_file(f"dev {name}", paths[name], DEV_SETS[name][1])
               for name in DEV_SETS}
    model = load_model(args.modele)
    payload = {"experience": "EXP-A2-017", "protocole": "docs/lot-a2_protocole_gold.md §6",
               "modele": {"url": MODEL_URL, "sha256": MODEL_SHA256}, "graine": SEED,
               "tirages_bootstrap": BOOTSTRAP_DRAWS, "code": git_state(),
               "empreintes": digests, "jeux": {}}
    for name in DEV_SETS:
        result = compare(load_examples(paths[name]), name, model, rules_predictor)
        payload["jeux"][name] = result
        ft, rg = result["fasttext"], result["regles"]
        print(f"== dev {name} : {result['n']} textes ==")
        print(f"  fastText : exactitude {ft.get('exactitude')} macro-F1 {ft.get('macro_f1')}")
        print(f"  règles   : exactitude {rg.get('exactitude')} macro-F1 {rg.get('macro_f1')}")
        if "regles_moins_fasttext" in result:
            d = result["regles_moins_fasttext"]["macro_f1"]
            print(f"  écart macro-F1 règles − fastText : {d['ecart']} [{d['ic_bas']} ;"
                  f" {d['ic_haut']}]")
        arz = result["t_etiquetes_arz"]
        print(f"  t étiquetés arz : {arz['k']}/{arz['n']} (informatif, hors score)")
        print(f"  erreurs : {len(result['erreurs'])}")
    print(f"JSON : {write_json(out_dir, 'lot-a2_gold_fasttext_dev', payload)}")


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
