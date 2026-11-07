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

(aucun pour l'instant)
