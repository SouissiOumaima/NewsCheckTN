# Lot A2 — Empreintes consignées avant la mesure unique (EXP-A2-020)

**Responsable : Abd Elmouhib Souri (Membre 2, Lot A2) · à commiter AVANT l'étape 10
(`normalization.gold_final`)**

Ce fichier fige, avant la mesure, les empreintes SHA-256 de tout ce que la mesure lit. Une
empreinte qui change après ce commit invalide la mesure. Procédure : `docs/lot-a2_protocole_gold.md`
§9 ; avenant 2 de `docs/lot-a2_modele_tn_protocole.md`.

Empreintes en minuscules (64 caractères hexadécimaux). Sous PowerShell :
`(Get-FileHash <fichier> -Algorithm SHA256).Hash.ToLower()`.

## 1. Rappel : empreintes déjà consignées (ne pas modifier)

| Élément | SHA-256 | Source |
|---|---|---|
| Liste ordonnée du test gelé (300) | `a579a57da9611c1218bcb24c3e78df6979c381e284ac25f8ccf9c9af37fdd252` | protocole du modèle tunisien, tirage du 2026-11-07 |
| Liste ordonnée de l'entraînement (800) | `5b4f40b94c7ac38ecae82afdf9ab76ea7cc1c478069db4dfdc0191bcd716b061` | idem |
| eval_30 (fichier) | `1d0bcfaa4b2a01fbd428fb18240174e309ac9877dc474a4dc1399e15e9dd34ce` | EXP-A2-011 |

## 2. Presse neuve (étape 2 : `gold_presse tirer`)

| Élément | SHA-256 | Source |
|---|---|---|
| Archive `ara_news_2020_10K.tar.gz` | `62e1c0a4ccae3c7a6f9cf6cbb398bae9b0d414b34fae58dbcc27fb928aa81d94` | sortie de `gold_presse tirer` (`lot-a2_gold_presse_20261122.json`) |
| Échantillon `presse_ara_news_2020_10K_300.txt` (300 phrases, graine 42) | `d78ff4f3d2290c7afdb8d5a81f764adf4e635be6bbc21066a59ba89852a6d5e7` | idem |

Année retenue : 2020  URL : `https://downloads.wortschatz-leipzig.de/corpora/ara_news_2020_10K.tar.gz`
Phrases dans l'archive : 10 000

## 3. Entrées (étape 3 : `gold_kaggle_inputs`, commit `d393517`, arbre propre)

| Élément | SHA-256 | Source |
|---|---|---|
| `final_train.tsv` (800 : 629 `t`, 171 `a` ; lex 312 ; seul fichier de textes envoyé sur Kaggle) | `39a3643bd82b63aa5bb740e068d702ade178891853912a53f8b4116fd6fab2bc` | `final_inputs.json` |
| `final_test.tsv` (300, sans étiquette, reste en local) | `fe68bd4549d051049c52538bf411d21947c4ced56bbc0c641b06feb3bb295bb0` | idem |
| `final_eval30.tsv` (34, reste en local) | `41ffaecdb5eaeeef00a7157912cdb4019c9afc3b9f870275abcb7cfb7615ab04` | idem |
| `final_presse.tsv` (300, reste en local) | `2e73e08b528ce87be1b1dcdc9db4fbda21dcf54b5cd4fba34d372845e776b2f2` | idem |
| `final_inputs.json` (envoyé sur Kaggle) | `9c17aa744b8ba429601f2980d118e0fed61407ec249001d54e6844fbab3383a7` | `Get-FileHash` |

`final_train.tsv` a la même empreinte que `kaggle_train.tsv` d'EXP-A2-015 : l'entraînement final
reçoit exactement les mêmes données que la validation croisée.

## 4. Entraînement final sur Kaggle (étape 5 : `marbert_final.ipynb`)

| Élément | SHA-256 | Source |
|---|---|---|
| `run_summary.json` (contient l'empreinte de chaque fichier de modèle) | `47815aca2801f4bbf89b6cd90c794aab541abcf2f68acda403787f165c366a66` | `Get-FileHash` |
| `marbert_final_graine1.zip` | `d9849b5707c2f8951a180e84abd408043e2632ff19f576edce1dc45be8de0358` | `Get-FileHash` |
| `marbert_final_graine2.zip` | `a5e530c6847d58ef086cc275c9cc283927776a2c7b04ba79c31a8e19b04f87b5` | `Get-FileHash` |
| `marbert_final_graine3.zip` | `9a4b78d8d4613d49190cb4a3a0f983302399d01dbc4adf33065b10f4673f4f3b` | `Get-FileHash` |

Exécution : session interactive Kaggle, le 2026-11-22 vers 13 h (`date_utc` de `run_summary.json` :
2026-11-22T12:17:12+00:00) ; durée 3.3 min.
Versions : torch 2.11.0+cu130 (Kaggle) / 2.11.0+cpu (local) ; transformers 5.20.2 (Kaggle) /
5.20.2 (local, identique).
Configuration enregistrée (identique à EXP-A2-015 et à l'avenant 2) : `UBC-NLP/MARBERTv2`, lr 2e-5,
4 époques, lots de 16, longueur 128, échauffement 0.1, décroissance 0.01, graines 1, 2, 3, seuil
de la cascade 0.30 ; 800 textes.
Pertes moyennes par époque : graine 1 : 0.5133, 0.3238, 0.1806, 0.1251 ; graine 2 : 0.5287,
0.3188, 0.1721, 0.1051 ; graine 3 : 0.5384, 0.3462, 0.1910, 0.1306.

## 5. Prédictions locales (étape 8 : `gold_predict_local`, commit `f00b9fc`, arbre propre)

| Élément | SHA-256 | Source |
|---|---|---|
| `predictions_test_graine1.tsv` | `ad3404584203eb768883be7789e0c6a7347179c37ec02db0aa31dd953fcd815f` | `lot-a2_gold_predictions_20261122.json` |
| `predictions_test_graine2.tsv` | `7f7f8a156b65986178e307602301273a11297226c00c5d26331b38126ca50202` | idem |
| `predictions_test_graine3.tsv` | `8ea9c1e287c8e75c75f8618324f71672047836d968097d5db065953d16333575` | idem |
| `predictions_eval_30_graine1.tsv` | `de0c58b4deeffe7bfbf03782aa668b787154e1f816dcf21a9c47f1727eaa29b6` | idem |
| `predictions_eval_30_graine2.tsv` | `4892724e8de5c0a25c199e7c536e43fdd44a2ca9b0840d3b97fda8a3adbaf076` | idem |
| `predictions_eval_30_graine3.tsv` | `f181b7c39d3ce33fef2262d6dcac3d4f54112a33476f8144931679f0fe35b54c` | idem |
| `predictions_presse_graine1.tsv` | `ccd245f91768df8f0c038656a26cc49490d81af26e9c19028ba8236647c1baf2` | idem |
| `predictions_presse_graine2.tsv` | `c0891d2ccb427d00dc83aeeb9d6100681b57124a444ce1e0e8f56a90009c9867` | idem |
| `predictions_presse_graine3.tsv` | `42f5d3a0b6ac04d60d00110e31b5127f72ec0d26f247c9a627c5a618a0f2695c` | idem |
| `lot-a2_gold_predictions_20261122.json` | `a94245a75f1466de690573463a072cd90a56ccf877e9edcea1ed3732809a53d9` | `Get-FileHash` |

## 6. Référence et manifeste (étape 9)

| Élément | SHA-256 | Source |
|---|---|---|
| Référence du test (`test_frozen_300_annotateur1.tsv`, 300 lignes : 255 `t`, 45 `a`, aucune « ? ») | `b30e7cd3324ded9b8114ed233b1dfd465c19736e23cb510a88fc97668cc62149` | sortie de `gold_agreement reference` ; identique au gel de 11 h 23 |
| Manifeste rempli (`manifeste.json`, hors dépôt) | `cdfac340343484650e56213bd6294c8fe2efe6f0661515bebe52cc7d84f9dd59` | calculé après contrôle par `gold_final.load_manifest` |

Statut de la référence : `annotateur1_seul`.

## 7. Écarts et incidents avant la mesure

a) Entraînement exécuté une seule fois, en session interactive Kaggle. Les versions enregistrées
   avec « Save Version » (restées en file d'attente) ne sont pas utilisées : si l'une a été
   exécutée, ses sorties sont ignorées.

b) GPU T4 x2 proposé par Kaggle, un seul utilisé (périphérique « cuda », sans DataParallel) ;
   EXP-A2-015 avait tourné sur un T4.

c) Inférence en local sur CPU (torch 2.11.0+cpu, même version que Kaggle). Les textes du test,
   d'eval_30 et de la presse n'ont jamais quitté le poste.

d) Antériorité : le protocole Gold `f0bb4d0` (2026-11-22 10:36) fixe déjà les 3 graines (§9) et
   la règle « annotateur 1 seul » (§8), avant le début de l'annotation du test (vers 10 h 48).
   L'avenant 2 (`f3bfe6a`, branche `lot-a2-modele-tn`) le reprend.

e) Les effectifs de prédictions `tn` par jeu et par graine (sortie de `gold_predict_local`,
   `lot-a2_gold_predictions_20261122.json`) étaient visibles avant la mesure. Sur la presse, sans
   étiquette, ils fixent à eux seuls le taux de fausses alertes : 25, 27 et 24 phrases sur 300
   (graines 1, 2, 3), contre 0 pour les règles. Sur le test, les effectifs de `tn` prédits (236,
   236, 250) ne donnent pas le score sans les étiquettes. Aucun réglage, aucun seuil ni aucun
   choix n'a suivi ; la mesure est lancée telle que prévue.
