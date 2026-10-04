"""Génère `mock_documents.jsonl` : documents au format exact produit par le Lot A2.

Les textes sont passés dans `normalization.normalize.normalize` (sans le modifier), pour
reproduire fidèlement ce que recevra `extract_claims`. À relancer si la normalisation évolue :
    python tests/fixtures/linguistic_analysis/make_mock_documents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from linguistic_analysis.io_contract import document_to_json, write_jsonl  # noqa: E402
from normalization.normalize import normalize  # noqa: E402

TEXTS = [
    # Français
    "Le taux de chômage en Tunisie a atteint 16,4 % au deuxième trimestre 2023.",
    "Selon le ministère de la Santé, 120 nouveaux cas ont été enregistrés. "
    "Il a appelé à la vigilance.",
    "Je pense que cette réforme est une catastrophe pour les jeunes.",
    "Le gouvernement aurait signé un accord avec le FMI la semaine dernière.",
    # Arabe standard
    "ارتفعت نسبة التضخم في تونس إلى 9,3 بالمئة خلال شهر جانفي.",
    "حسب المعهد الوطني للإحصاء، بلغ عدد السكان 12 مليون نسمة.",
    "أعتقد أن هذا القرار سيضر بالاقتصاد الوطني.",
    # Tunisien en lettres arabes
    "الحكومة قالت إلي الأسعار باش تنقص الشهر الجاي.",
    # Tunisien en arabizi
    "El 7koma 9alet elli el as3ar bech tan9es fel chhar ejjay.",
    "Ena n7ess elli el wadh3 khayeb barcha.",
    # Mixte FR / tunisien
    "El ministre 9al que le taux de chômage a baissé de 2 % en 2024.",
]


def main() -> None:
    out = Path(__file__).with_name("mock_documents.jsonl")
    write_jsonl([document_to_json(normalize(t)) for t in TEXTS], out)
    print(f"{len(TEXTS)} documents -> {out}")


if __name__ == "__main__":
    main()
