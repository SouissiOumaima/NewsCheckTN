"""Lot B — Résolution de coréférence par règles.

Pronoms sujets (il/elle, هو/هي, howa/hiya…) rattachés à la mention compatible la
plus récente dans les deux phrases précédentes. Sans candidat sûr, la phrase est
laissée inchangée.
"""

from __future__ import annotations


def resolve(sentences: list[str]) -> list[str]:
    """Retourne une version autonome de chaque phrase (même ordre, même longueur)."""
    # TODO(Lot B): fenêtre de mentions, accord genre/nombre, journal des résolutions.
    return list(sentences)
