# Jeu de développement du Lot D (retrieval)

**Données FICTIVES** (`source = "exemple_fictif"`) : elles servent uniquement à développer et
tester le code du retrieval. Les chiffres ne doivent pas être cités comme de vrais faits.

- `evidence_dev.jsonl` : 15 passages FR / AR, au format de `data/processed/evidence_corpus.jsonl`
  (lisible par `data.loaders.load_evidence_corpus`).
- `claims_dev.jsonl` : 17 affirmations (FR, arabe standard, tunisien en lettres arabes, arabizi)
  avec `gold_doc_ids`, les preuves attendues. Liste vide = aucune preuve dans le corpus
  (cas d'abstention attendue).

À remplacer par le corpus réel du Lot A1 et les paires (affirmation, preuve) annotées.
