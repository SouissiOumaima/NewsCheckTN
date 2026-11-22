# 2.b Normalisation et identification de la langue (Lot A2)

**Auteur :** Abd Elmouhib Souri — Lot A2 (normalisation, identification de la langue et de l'écriture, bruit)
**Statut :** version v0 pour le palier Silver (2026-11-15). Chaque chiffre renvoie à une entrée de
`experiments.md` (EXP-A2-…).

## 1. Rôle dans le pipeline

Le Lot A2 est la première étape du pipeline NewsCheck TN. Chaque texte (article, commentaire,
affirmation) passe par une seule fonction, utilisée par tous les lots :

```
normalize(text) -> Document(raw_text, text, lang ∈ {fr, ar, tn, unk}, script)
```

La langue (`fr` français, `ar` arabe standard, `tn` tunisien) et l'écriture (lettres arabes, lettres
latines, arabizi, mixte) permettent aux autres lots de traiter chaque texte selon sa langue et de
présenter leurs résultats **par langue et par écriture**, comme l'exige le sujet.

## 2. Données

| Rôle | Jeu | Taille |
|---|---|---|
| Test gelé | eval_30 (Lot B), gelé au commit `85fb77d`, SHA-256 `1d0bcfaa…` | 34 phrases : 10 FR, 10 AR, 5 TN en lettres arabes, 5 en arabizi, 4 mixtes |
| Mise au point (dev) | Commentaires TSAC annotés par deux personnes, désaccords adjugés | 100 en lettres arabes (kappa 0,65) ; 86 en lettres latines (kappa 0,84) |
| Fausses alertes | Presse : UD Arabic-PADT, UD French-GSD | 680 + 416 phrases de test |
| Référence d'arabe standard (Silver) | Leipzig, News 2022 | 300 000 phrases |

Les corpus TSAC et Tunizi sont des corpus de sentiment : seuls leurs textes sont utilisés, jamais leurs
étiquettes. Le détail (licences, empreintes, citations) est dans `normalization/DATA_CARD.md`.

## 3. Méthode

1. **Normalisation** : formes de lettres arabes unifiées, diacritiques retirés ; les nombres ne sont
   jamais modifiés (29 textes sur 29 conservés).
2. **Écriture** : part de lettres arabes ; les chiffres dans un mot (3, 7, 9, 8) signalent l'arabizi.
3. **Langue** :
   - tunisien en lettres arabes : lexique de 78 marques dialectales et négation « ma…ch ». Choix
     motivé par la rareté du tunisien annoté et par l'explicabilité de chaque décision ;
   - arabizi : régression logistique sur des n-grammes de caractères (1 à 4), poids exportés en JSON ;
     seuil réglé sur des données françaises de développement.
4. **Bruit** : modèle de langue à n-grammes de caractères (ordre 4), un par écriture ; les textes
   suspects sont signalés, jamais supprimés.

**Métrique** : macro-F1, qui donne le même poids à chaque langue ; l'exactitude favoriserait la classe
majoritaire (environ 77 % de tunisien dans le dev en lettres arabes).

## 4. Résultats par langue et par écriture

**Test gelé (N = 34, 3 classes)** : macro-F1 **0,94**, contre 0,50 pour la baseline « alphabet seul »
(lettres arabes → arabe standard, sinon français) et 0,19 pour la classe majoritaire (EXP-A2-011).

| Langue / écriture | Rappel sur le test gelé |
|---|---|
| Français, lettres latines | 10/10 |
| Arabe standard, lettres arabes | 10/10 |
| Tunisien, lettres arabes | 4/5 |
| Tunisien, arabizi | 5/5 |
| Tunisien, mixte | 3/4 |

**Commentaires réels (dev, 2 classes par écriture)** : macro-F1 0,63 en lettres arabes, 0,83 en lettres
latines. En lettres arabes, le rappel du tunisien est de **0,53**, pour une précision de **1,00**.

**Fausses alertes** : 0 phrase de presse sur 680 classée tunisienne, 0 phrase française sur 416 classée
arabizi.

**Bruit** : 99 % des textes artificiellement bruités repérés (AUC ≥ 0,99) pour 5 % de fausses alertes ;
limite : un encodage abîmé en lettres latines reste presque invisible (AUC 0,53) (EXP-A2-010).

**Significativité (bootstrap apparié, 1 000 tirages, EXP-A2-014)** : sur eval_30, l'écart avec la
baseline « alphabet seul » est de +0,45 [IC 95 % +0,34 ; +0,55] ; sur le dev, +0,44 [+0,36 ; +0,52]
en lettres arabes et +0,67 [+0,56 ; +0,78] en lettres latines ; p < 0,001 dans tous les cas.

## 5. Expériences du palier Silver

**EXP-A2-012 (résultat négatif).** Seuil du lexique (12, 8, 6, 4 textes) croisé avec le retrait des
affixes (8 configurations), réglé sur une moitié fixe du dev et sur la presse de développement. Aucune
configuration ne relève le rappel sans fausse alerte : le filtre « absent de PADT train » est trop petit
pour écarter les mots rares d'arabe standard. Les affixes seuls n'apportent rien.

**EXP-A2-013 (gain confirmé, non activé).** Les candidats du lexique sont filtrés par 300 000 phrases
d'arabe standard (Leipzig). La configuration retenue sur la moitié « reglage » est mesurée une seule
fois sur des données jamais vues :

| Jeu | Macro-F1 | Rappel tn | Précision tn | Fausses alertes |
|---|---|---|---|---|
| Dev, moitié « mesure » (N = 53) | 0,61 → **0,68** | 0,51 → **0,61** | 1,00 → 1,00 | — |
| Test gelé (N = 34) | 0,94 → 0,94 | 0,86 → 0,86 | 1,00 → 1,00 | — |
| Presse de test (680) | — | — | — | 0 → **1** |

Le critère d'adoption, fixé avant la mesure, exigeait 0 fausse alerte : la configuration n'est **pas
activée**. L'alerte vient d'un seul mot ajouté, un nom de famille. La liste extraite automatiquement
mêle aussi des noms propres, des injures, des fautes de frappe et des mots d'arabe standard : elle doit
être relue par un humain avant toute intégration.

**EXP-A2-014 (stabilité, baseline neuronale, courbe d'apprentissage).** Le modèle arabizi est
réentraîné avec 3 graines (13, 42, 2026), qui changent les 10 % d'arabizi mis de côté et le découpage
du français. Le seuil est choisi sur le français de dev, et la mesure porte sur l'arabizi mis de côté
(7 360 textes) et sur le français de test (416 phrases et leurs 5 premiers mots, soit 816 textes),
jamais utilisés pour choisir. La baseline neuronale est un perceptron multicouche (64 neurones) sur
les mêmes n-grammes.

| Modèle (3 graines) | Macro-F1 | Rappel arabizi | Fausses alertes (sur 816) |
|---|---|---|---|
| Régression logistique (livrée) | **0,834 ± 0,001** | 0,911 ± 0,001 | 0 |
| Perceptron multicouche | 0,800 ± 0,091 | 0,878 ± 0,078 | 0 |

Le modèle livré est stable ; le perceptron ne fait pas mieux et dépend fortement de la graine (de 0,70
à 0,87) : la régression logistique est conservée. Le macro-F1 est tiré vers le bas par la classe
française, car les 9 % d'arabizi manqués sont classés français ; la précision de l'arabizi reste
de 1,00.

| Part de l'apprentissage | 10 % | 25 % | 50 % | 100 % |
|---|---|---|---|---|
| Macro-F1 (3 graines) | 0,755 ± 0,015 | 0,806 ± 0,028 | 0,829 ± 0,025 | 0,834 ± 0,001 |

La courbe plafonne après 50 % (+0,005) : ajouter de l'arabizi apporterait peu ; la marge de progrès
est dans les textes courts et proches du français.

Ces deux expériences constituent l'**ablation** du Lot A2 : seuil du lexique, retrait des affixes et
filtre par une référence d'arabe standard, soit 20 configurations réglées sur le dev, chacune
consignée, y compris les configurations écartées.

## 6. Support multilingue aux autres lots

L'outil `normalization.tag_lang` (tâche S8 du plan) ajoute la langue et l'écriture de chaque texte
d'un fichier local (JSONL ou CSV), par exemple les champs `claim` et `evidence` du corpus NLI du Lot C.
Il n'affiche que des comptes, jamais de texte, et les données restent sur le poste de chaque lot.

## 7. Limites

- Le tunisien en lettres arabes reste le point faible : un mot absent du lexique, comme « لقيت »
  (« j'ai trouvé »), est lu comme de l'arabe standard. Le compromis est volontaire : la précision passe
  avant le rappel, pour ne jamais classer la presse en tunisien.
- Le test gelé est petit (5 phrases en tunisien en lettres arabes, une phrase pèse 0,2 de rappel) et
  annoté par une seule personne ; les scores du dev sont optimistes, ce jeu ayant servi à la mise au
  point.
- Les données d'apprentissage sont des commentaires de réseaux sociaux et de la presse ; les
  affirmations du projet n'ont pas encore été mesurées par langue.

## 8. Suite : un modèle appris pour le tunisien en lettres arabes

Un protocole a été **pré-inscrit avant toute donnée** (`docs/lot-a2_modele_tn_protocole.md`) :
affinage de MARBERTv2 en cascade (marque du lexique trouvée → tunisien ; sinon, décision du modèle),
validation croisée à 5 plis et 5 graines sur l'entraînement uniquement.

- Critères de réussite fixés à l'avance, sur un nouveau test gelé : rappel ≥ 0,70, précision ≥ 0,90,
  au plus 1 % de fausses alertes sur une presse neuve, aucune baisse sur eval_30.
- Jeux tirés et gelés : 300 textes de test (SHA-256 `a579a57d…`) et 800 d'entraînement (SHA-256
  `5b4f40b9…`).
- Double annotation : non obtenue à la date du Gold, test annoté par une seule personne (EXP-A2-019) ;
  résultats de la mesure unique en section 9.

## 9. Palier Gold

Protocole pré-inscrit avant toute mesure (`docs/lot-a2_protocole_gold.md`, commit `f0bb4d0`) ;
empreintes de tout ce que lit la mesure unique figées avant elle (`f4dd17e`). Toutes les mesures
sont faites sur le dev, sauf la mesure unique sur le test gelé.

| Question | Résultat | Entrée |
|---|---|---|
| Robustesse (INV) : 10 perturbations de surface | règles : 1 bascule sur 1 314 textes perturbés ; robustes sur 12 couples (perturbation × écriture) sur 15, indéterminées sur 3 faute d'effectif ; idempotence et cohérence sans échec ; « alphabet seul » fragile aux URL ; fastText fragile sur 5 perturbations latines | EXP-A2-016 |
| Baseline externe forte : fastText lid.176 | macro-F1 0.185 (lettres arabes) et 0.250 (lettres latines), contre 0.628 et 0.831 pour les règles ; écarts +0.44 et +0.58, IC au-dessus de 0 ; rappel du tunisien nul | EXP-A2-017 |
| Fuites entre jeux | aucun doublon, aucun texte commun entre test, entraînement, dev et eval_30 ; quasi-doublons non cherchés | EXP-A2-018 |
| Accord entre annotateurs | non mesuré : test annoté par une seule personne, seconde annotation non reçue | EXP-A2-019 |
| Mesure unique de la cascade lexique → MARBERTv2 (test, 300 textes) | rappel du tunisien 0.898 ± 0.021 (lexique seul 0.392), précision 0.952 ± 0.011 (0.980) ; fausses alertes sur une presse neuve 8.4 % (règles 0 %) ; macro-F1 eval_30 0.913 contre 0.943 ; critères 1 et 2 atteints, 3 et 4 non atteints | EXP-A2-020 |

**Décision.** La cascade relève fortement le rappel du tunisien en lettres arabes, mais elle classe
en tunisien de la presse en arabe standard et baisse le score sur eval_30. Deux des quatre
conditions fixées avant manquent : elle n'est **pas intégrée** à `normalize.py`, qui garde les
règles (bibliothèque standard seulement). Le résultat est **indicatif** : la référence du test
vient d'un seul annotateur.

**Limites.**
- Une seule personne a annoté le test, l'entraînement et écrit le lexique ; l'accord humain n'est
  pas mesuré.
- Le dev qui sert à INV et à fastText a servi à la mise au point des règles : ces chiffres sont
  optimistes.
- La presse neuve vient d'une seule année (2020) et d'une seule source.
- Hypothèse non vérifiée : le modèle, entraîné sur des commentaires seulement, aurait appris le
  registre plutôt que le dialecte. Suite : négatifs de presse à l'entraînement et seuil réglé sur un
  dev de presse distinct, dans une nouvelle expérience.
- L'arabizi est identifié mais pas converti en lettres arabes (aucun jeu de référence de
  translittération).
