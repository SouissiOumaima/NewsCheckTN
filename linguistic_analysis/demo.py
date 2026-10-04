"""Lot B — Démonstration : analyse détaillée d'une ou plusieurs phrases.

Affiche, pour chaque phrase candidate, ce que produit le Lot B : affirmation vérifiable ou non,
opinion, modalité et certitude, triplet sujet-prédicat-objet, phrase résolue par coréférence,
parseur utilisé et indices qui ont déclenché les règles.

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.demo "Je pense que le gouvernement devrait agir plus vite."
    python -m linguistic_analysis.demo "Le ministre a visité Sfax. Il a annoncé 200 emplois."
    python -m linguistic_analysis.demo --rules "El 7koma 9alet elli el as3ar bech tan9es."
    python -m linguistic_analysis.demo --json "..."      # sortie JSON (contrat détaillé)
Sans argument, une série d'exemples FR / AR / tunisien est analysée.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings

EXAMPLES = [
    "Le taux de chômage en Tunisie a atteint 16,4 % en 2023.",
    "Je pense que le gouvernement devrait agir plus vite.",
    "Le ministre a visité Sfax. Il a annoncé 200 emplois.",
    "حسب المعهد الوطني للإحصاء، بلغ عدد السكان 12 مليون نسمة.",
    "El 7koma 9alet elli el as3ar bech tan9es.",
]


def _yes(value: bool) -> str:
    return "oui" if value else "non"


def describe(text: str) -> str:
    """Rapport lisible de l'analyse du Lot B pour `text`."""
    from linguistic_analysis.claim_extraction import extract_claims_detailed
    from normalization.normalize import normalize

    doc = normalize(text)
    claims = extract_claims_detailed(doc)
    lines = [f"Texte : {text}", f"Langue détectée en amont : {doc.lang.value} ({doc.script})"]
    if not claims:
        lines.append("Aucune phrase candidate (phrases de moins de 4 mots).")
        return "\n".join(lines)
    for number, c in enumerate(claims, start=1):
        lines += [
            "",
            f"[{number}] {c.text}",
            f"    affirmation vérifiable : {_yes(c.is_claim)}",
            f"    opinion / non factuel  : {_yes(c.is_opinion)}",
            f"    modalité               : {c.modality} (certitude {c.certainty:.2f})",
            f"    sujet                  : {c.subject or '—'}",
            f"    prédicat               : {c.predicate or '—'}",
            f"    objet                  : {c.obj or '—'}",
        ]
        if c.resolution_log:
            lines.append(f"    phrase autonome        : {c.resolved_text}")
            lines.append(f"    coréférence            : {', '.join(c.resolution_log)}")
        lines.append(f"    parseur                : {c.parser}")
        lines.append(f"    indices                : {', '.join(c.triggers) or '—'}")
    return "\n".join(lines)


def as_json(text: str) -> list[dict]:
    from linguistic_analysis.claim_extraction import extract_claims_detailed
    from linguistic_analysis.io_contract import detailed_to_json
    from normalization.normalize import normalize

    claims = extract_claims_detailed(normalize(text))
    rows = detailed_to_json(claims)
    for row, claim in zip(rows, claims, strict=True):
        row["is_claim"] = claim.is_claim
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Démonstration de l'analyse du Lot B.")
    parser.add_argument("texts", nargs="*", help="phrase(s) à analyser (par défaut : exemples)")
    parser.add_argument("--rules", action="store_true", help="règles seules, sans spaCy / Stanza")
    parser.add_argument("--json", action="store_true", help="sortie JSON détaillée")
    args = parser.parse_args(argv)

    # Console Windows : forcer l'UTF-8 pour afficher l'arabe sans erreur d'encodage.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Masquer les avertissements des bibliothèques (chargement des modèles) pendant la démo.
    warnings.simplefilter("ignore")
    logging.getLogger("stanza").setLevel(logging.ERROR)

    texts = args.texts or EXAMPLES
    if args.rules:
        from linguistic_analysis import preprocessing

        preprocessing.get_parser = lambda lang: None

    if args.json:
        print(json.dumps({t: as_json(t) for t in texts}, ensure_ascii=False, indent=2))
        return
    print("\n\n".join(describe(t) for t in texts))


if __name__ == "__main__":
    main()
