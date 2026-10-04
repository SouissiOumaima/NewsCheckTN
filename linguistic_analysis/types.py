"""Structures internes du Lot B.

`ExtractedClaim` porte des informations plus riches que `common.schemas.Claim`
(texte résolu, score de certitude, confiance, parseur utilisé). Ces champs restent
internes au module tant que l'équipe n'a pas validé leur ajout au schéma partagé ;
`to_claim()` projette vers le contrat actuel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from common.schemas import Claim, Lang

# Valeurs possibles de la modalité. "assertif" est la valeur par défaut
# (le Lot C s'appuie dessus).
MODALITY_LABELS = (
    "assertif",
    "rapporté",
    "conditionnel",
    "hypothétique",
    "opinion",
    "interrogatif",
    "souhait",
)
DEFAULT_MODALITY = "assertif"


@dataclass
class ExtractedClaim:
    """Affirmation extraite avec l'ensemble des informations du Lot B."""

    text: str
    lang: Lang
    span: tuple[int, int] = (0, 0)
    resolved_text: str = ""  # version autonome après coréférence (vide = identique à text)
    subject: str | None = None
    predicate: str | None = None
    obj: str | None = None
    modality: str = DEFAULT_MODALITY
    certainty: float = 1.0  # 0 = très incertain, 1 = asserté sans réserve
    is_opinion: bool = False
    confidence: float = 0.0  # confiance dans l'extraction
    parser: str = "rules"  # "spacy-fr" | "stanza-ar" | "rules"
    triggers: list[str] = field(default_factory=list)  # indices ayant déclenché les règles
    resolution_log: list[str] = field(default_factory=list)  # coréférence : « il → Le ministre »

    def __post_init__(self) -> None:
        if not self.resolved_text:
            self.resolved_text = self.text
        if self.modality not in MODALITY_LABELS:
            raise ValueError(f"Modalité inconnue : {self.modality!r} (attendu : {MODALITY_LABELS})")

    def to_claim(self) -> Claim:
        """Projette vers `common.schemas.Claim` (checkworthiness laissé au Lot C)."""
        return Claim(
            text=self.text,
            lang=self.lang,
            span=self.span,
            subject=self.subject,
            predicate=self.predicate,
            obj=self.obj,
            modality=self.modality,
        )
