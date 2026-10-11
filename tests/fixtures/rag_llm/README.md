# Jeu de développement du Lot D (retrieval)

**Données FICTIVES** (`source = "exemple_fictif"`) : elles servent uniquement à développer et
tester le code du retrieval. Les chiffres ne doivent pas être cités comme de vrais faits.

- `evidence_dev.jsonl` : 15 passages FR / AR, au format de `data/processed/evidence_corpus.jsonl`
  (lisible par `data.loaders.load_evidence_corpus`).
- `claims_dev.jsonl` : 20 affirmations (FR, arabe standard, tunisien en lettres arabes, arabizi)
  avec `gold_doc_ids` (preuves attendues ; liste vide = aucune preuve dans le corpus) et
  `gold_label` (`vrai` | `faux` | `trompeur` | `preuves_insuffisantes`).
  v1 (EXP-D-001) : 17 affirmations, sans `gold_label`. v2 (EXP-D-002) : + 3 affirmations vraies
  (`dev-c18` à `dev-c20`) pour équilibrer un jeu dominé par des affirmations fausses.

À remplacer par le corpus réel du Lot A1 et les paires (affirmation, preuve) annotées.
