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

## Jeu réel Tunifact v0 (EXP-D-004)

- `claims_tunifact_v0.jsonl` : 15 affirmations rédigées par le Lot D à partir de 5 articles
  Tunifact du Lot A1 (698 migration → vrai ; 613 vaccins, 797 bac, 890 Poste → faux ;
  937 coupures en France → trompeur, d'après le verdict publié par Tunifact).
  `origine` : `original` (même langue que l'article, 5), `traduction` (autre langue, tunisien ou
  arabizi, traduit par le Lot D, 7), `inventee` (aucune preuve dans le corpus, 3).
- Le corpus (25 phrases Tunifact + 30 phrases TArC comme distracteurs) n'est **pas** versionné :
  `python -m rag_llm.build_tunifact_eval` l'écrit dans `data/interim/lot_d/` à partir de la
  branche `lot-a1-data` (droits de redistribution Tunifact non confirmés).

## Jeu réel Tunifact v1 (EXP-D-006)

- `claims_tunifact_v1.jsonl` : les 15 affirmations de v0 (identifiants de preuve des articles 698
  et 937 convertis au format de l'export : `698-005` → `698-s0005`) + 6 affirmations sur l'article
  933 (nationalité ; 4 sur la rumeur → faux, en AR, FR, tunisien en lettres arabes et arabizi ;
  2 sur le texte de loi → vrai, en AR et FR). Traductions tunisiennes et arabizi rédigées par le
  Lot D, à valider.
- Corpus (non versionné) : `python -m rag_llm.build_tunifact_eval` (v1 par défaut) — export
  `tunifact_sentences_46.jsonl` du Lot A1 (698, 933, 937 complets) + 613, 797, 890 de v0 +
  30 phrases TArC ; 1re phrase de chaque article et fragments de moins de 15 caractères écartés.
  84 passages au total.
