# Lot A2 — Protocole : modèle appris pour le tunisien en lettres arabes

Statut : **pré-inscrit**. Ce protocole est commité **avant** tout tirage annoté et tout entraînement.
Toute modification ultérieure est datée dans la section « Écarts au protocole », avec sa raison.

## 1. Question

Un modèle arabe pré-entraîné, affiné sur des commentaires annotés, relève-t-il le rappel du tunisien
en lettres arabes (0.53 avec le lexique de 78 marques, EXP-A2-011) sans perdre en précision ?

## 2. Données

| Jeu | Contenu | Rôle | Règle |
|---|---|---|---|
| Test gelé (nouveau) | 300 commentaires TSAC en lettres arabes, jamais annotés, tirés avec la graine 20261107 | Mesure unique, à la fin | Annoté par deux personnes, adjugé, empreinte SHA-256 consignée avant l'entraînement ; jamais ouvert pour régler quoi que ce soit |
| Entraînement | 800 autres commentaires, disjoints du test | Affinage, validation croisée, choix du seuil | 20 % annotés deux fois (kappa) |
| Dev existant (EXP-A2-009) | 100 + 86 textes de référence | Peut rejoindre l'entraînement | Ne sert plus de point de comparaison |
| eval_30 (34 phrases, commit 85fb77d) | Test gelé du Lot B | Non-régression uniquement | Lancé une seule fois, à la fin |
| Presse neuve | Leipzig, arabe, News d'une année jamais utilisée (pas 2022), hors corpus maghrébins | Fausses alertes | Mesure unique, à la fin |

Tirage : `python -X utf8 -m normalization.model_tn_data draw`. Annotation : guide
`docs/lot-a2_guide_annotation.md` (étiquettes `t`, `a`, `f`, `x`). Aucun texte n'est versionné.

Limite connue : le test vient de TSAC, comme les marques du lexique ; la baseline peut en être
légèrement avantagée.

## 3. Méthode

- **Baseline** : pipeline actuel (lexique de 78 marques et négation), inchangé.
- **Modèle** : `UBC-NLP/MARBERTv2`, affiné en classification binaire `tn` / `ar` sur les textes en
  lettres arabes (étiquettes `f` et `x` exclues).
- **Architecture en cascade** : marque du lexique trouvée → `tn` ; sinon, décision du modèle avec un
  seuil de probabilité.
- **Réglage** : validation croisée à 5 plis sur l'entraînement uniquement ; 5 graines ; hyperparamètres
  et seuil choisis sur la moyenne des plis ; seuil choisi pour une précision `tn` d'au moins 0.90.
- **Calcul** : GPU Kaggle ; données en jeu de données privé ; aucun poids de modèle dans le dépôt.

## 4. Critères de réussite (fixés avant)

Sur le **nouveau test gelé** (300 textes), la cascade doit atteindre :

1. rappel `tn` (lettres arabes) **≥ 0.70** ;
2. précision `tn` **≥ 0.90** ;
3. **≤ 1 %** de fausses alertes sur la presse neuve ;
4. sur eval_30 : aucune baisse du macro-F1 (0.94).

Les quatre conditions sont nécessaires. Sinon : résultat consigné tel quel, modèle non intégré.
Chaque score est donné avec un intervalle de confiance à 95 % (bootstrap, 1 000 tirages).

Précision : les critères portent sur la moyenne des 3 graines, voir avenant 2 (§5, f3bfe6a).

## Tirage (fait le 2026-11-07, après le commit 1ef3b39 de ce protocole)

- Commande : `python -X utf8 -m normalization.model_tn_data draw` ; graine 20261107.
- Réserve : 5 735 commentaires TSAC en lettres arabes, jamais annotés (après les filtres de
  `annotation.candidates`).
- Test gelé : 300 textes ; SHA-256 de la liste ordonnée
  `a579a57da9611c1218bcb24c3e78df6979c381e284ac25f8ccf9c9af37fdd252`.
- Entraînement : 800 textes ; SHA-256
  `5b4f40b94c7ac38ecae82afdf9ab76ea7cc1c478069db4dfdc0191bcd716b061`.
- Fichiers non versionnés : `data/interim/langid/model_tn/`.

## 5. Écarts au protocole

### Avenant 1 — 2026-11-15 : pré-annotation assistée par un LLM (consigne de l'enseignante)

Écart au protocole, décidé avant toute annotation des jeux tirés :
- Ordre : l'entraînement (800 textes) est annoté en premier ; le test gelé (300) attend la seconde
  annotatrice et n'est lu par aucun modèle avant la mesure finale.
- Entraînement, hors textes communs (640 textes, lignes 161 à 800) : un LLM (Gemini, via Google AI
  Studio) propose une étiquette ; l'annotateur la valide ou la corrige, texte par texte. La
  proposition et la décision humaine sont toutes deux conservées.
- Test gelé (300 textes) et textes communs du kappa (160, lignes 1 à 160 de l'entraînement) :
  annotation sans assistance, par les deux annotateurs, sans voir aucune proposition du LLM (évite
  le biais d'ancrage sur la référence).
- Étiquettes : celles du guide (`t`, `a`, `f`, `x`) ; un texte français éventuellement classé `x`
  avant cette correction est sans effet sur l'entraînement (`f` et `x` sont tous deux exclus, §3).
- Prompt, modèle, version et température (0) fixés avant le premier appel : modèle `gemini-4-hydrogen` (Google AI Studio, 2026-11-15), température 0, prompt conservé hors dépôt avec les exports.
- Les textes envoyés au LLM sont des commentaires publics de TSAC (LGPL-3.0) ; aucune donnée privée,
  aucune clé dans Git.
- Mesure ajoutée : accord LLM / humain sur l'entraînement assisté (part des propositions corrigées),
  calculée après l'annotation.
- Traçabilité : la pré-annotation assistée de cet avenant a envoyé des textes TSAC (commentaires
  publics, aucune donnée privée) au service externe Gemini (Google AI Studio). Le nombre exact de
  textes envoyés n'est pas établi ; des propositions ont été conservées pour 20 textes sur 640
  (note d'exécution ci-dessus). Cet envoi n'avait pas été signalé à l'équipe au moment des faits ;
  il est consigné ici le 2026-11-22, à la demande de la relecture de #31. Le test gelé et les
  textes du kappa n'ont jamais été envoyés.

### Note d'exécution — 2026-11-15 : assistance du LLM presque absente

- Entraînement, lignes 161 à 800 (640 textes) : la proposition du LLM n'a été obtenue et affichée
  que pour 20 textes ; pour les 620 autres, les appels ont échoué (probablement le quota) et
  aucune proposition n'a été affichée. Ces 620 textes ont donc été annotés sans assistance,
  comme les 160 textes communs.
- Conséquence : l'accord LLM / humain ne peut pas être mesuré sur l'annotation elle-même
  (20 textes seulement, trop peu pour conclure). Aucun effet sur les étiquettes : chaque étiquette
  est une décision humaine, et l'absence de proposition exclut tout biais d'ancrage.
- Entraînement (annotateur 1) : 800 / 800 ; colonne `mode` de l'export « assisté » pour les 640,
  proposition présente pour 20 seulement (trace dans `*_llm.tsv`).

### Avenant 2 — 2026-11-22 : graines de l'entraînement final et annotation unique du test

Écart au protocole, décidé le 2026-11-22, avant toute annotation du test gelé et avant tout
entraînement final. Il est repris dans `docs/lot-a2_protocole_gold.md` (§8 et §9).

- **Graines de l'entraînement final** : la section 3 ne fixait pas les graines de l'entraînement
  final. La cascade (configuration figée d'EXP-A2-015 : lr 2e-5, 4 époques, seuil 0.30) est
  entraînée une fois sur les 800 textes avec 3 graines (1, 2, 3). Les critères de la section 4
  sont jugés sur la moyenne des 3 graines ; on rapporte aussi la moyenne ± écart-type et un IC
  bootstrap (1 000 tirages) par graine.
- **Annotation unique du test** : la section 2 exige un test « annoté par deux personnes,
  adjugé ». Si la seconde annotation du test n'est pas complète au moment de la mesure, la
  référence est l'annotation de l'annotateur 1 seul, faite sans assistance. Dans ce cas :
  aucun kappa n'est rapporté pour le test (mention « accord humain non mesuré ») ; le résultat
  est qualifié d'indicatif ; on ne conclut pas « critères atteints » ou « non atteints » au sens
  de la section 4. Si seuls les 160 textes communs sont doublement annotés, leur kappa est
  rapporté.
- Aucun autre élément du protocole ne change (jeux, empreintes, critères, cascade).
