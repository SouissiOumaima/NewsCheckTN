# Lot D — Protocole : re-ranker et incertitude calculée (EXP-D-020, EXP-D-021)

**Responsable : Hadil Lajili (Membre 5, Lot D) · Version 1 · 2026-11-27**

Ce fichier est écrit et commité **avant toute mesure** de ces deux expériences. Il complète le
protocole Gold (`docs/lot-d_protocole_gold.md`). Deux demandes de la fiche de rôle du Lot D ne sont
pas encore couvertes : le **re-ranking** des passages (S5) et le **calcul du niveau
d'incertitude** du verdict (S6). Aujourd'hui, la recherche hybride s'arrête à la fusion RRF, et
l'incertitude affichée est une valeur fixe, présentée comme « non calibrée ».

## 1. Système de départ (fixé)

| Élément | Valeur |
|---------|--------|
| Recherche | hybride BM25 + e5-base, fusion RRF (k = 60), 20 candidats par méthode, top 5 (EXP-D-008) |
| NLI | NLI affiné du Lot C (checkpoint graine 42, EXP-C-011), `NLI_BACKEND=fine-tuned` |
| Verdict | Falcon-H1-3B + JSON, prompt v1, température 0.3, graines 13 / 42 / 2026 (EXP-D-015) |
| Données externes | aucune API ; tout tourne en local |

## 2. Jeux de données et statut

| Jeu | Contenu | Statut pour ces expériences |
|-----|---------|-----------------------------|
| **Dev** | 20 affirmations fictives, 15 passages ; + 10 phrases hors sujet (SHA-256 `16006c44…`) | contrôle ; la recherche y est déjà presque parfaite (rappel@5 hybride 0.944, EXP-D-008) |
| **Test Tunifact v1** | 21 affirmations (18 avec preuve, 65 passages de référence), 84 passages | déjà utilisé (recherche : EXP-D-008 ; verdict : EXP-D-010, EXP-D-015 ; audit : EXP-D-016) |

Le dev est trop petit et trop facile pour **comparer** des méthodes de recherche. Il n'existe pas
d'autre jeu de recherche disponible avant la fin du projet (le test v2 n'est pas prêt). Les
mesures sur le test v1 sont donc faites **une seule fois**, sans aucun paramètre réglé dessus, et
déclarées comme une nouvelle utilisation d'un jeu déjà vu. Tous les choix (modèle, nombre de
candidats, formule) sont fixés ici, avant la mesure.

## 3. EXP-D-020 — Re-ranker

**Méthode.** Les 20 meilleurs passages de la fusion RRF sont reclassés par un **cross-encoder** :
il lit chaque paire (affirmation, passage) et donne un score de pertinence. On garde les 5
premiers. Sur le dev, qui n'a que 15 passages, tous les passages sont reclassés.

**Modèle (fixé a priori).** `BAAI/bge-reranker-v2-m3` (multilingue, licence Apache 2.0, environ
568 M paramètres, base XLM-RoBERTa), sur le CPU, longueur maximale 512 jetons, score ramené entre
0 et 1 par une sigmoïde. Aucun autre modèle n'est mesuré sur le test.

**Règle de repli, fixée maintenant et décidée sur le dev seulement.** Si le temps moyen du
re-ranking dépasse **15 secondes par affirmation** sur le dev, sur le PC de démonstration (GTX 1650,
CPU), on prend à la place `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingue, arabe et
français inclus, beaucoup plus léger). Ce choix dépend **uniquement de la vitesse**, jamais d'un
score.

**Mesures.** Rappel@5 et MRR, en tout et par langue (fr, ar, tn), avant et après le re-ranker ;
bootstrap apparié (10 000 tirages, graine 42) ; temps par affirmation.

**Décision (fixée maintenant).** Le re-ranker est **adopté** si, sur le test v1 :
1. le rappel@5 augmente, avec une valeur p unilatérale < 0.05 au bootstrap apparié ;
2. et le rappel@5 du dev ne baisse pas.

Sinon, il n'est pas adopté, et le résultat est écrit tel quel. S'il est adopté, son effet sur le
verdict est mesuré sur le dev seulement (Falcon, 30 phrases, 3 graines) : il ne doit pas faire
perdre plus d'une bonne réponse (graine 42). Aucun nouveau verdict n'est généré sur le test v1.

## 4. EXP-D-021 — Incertitude calculée à partir du NLI

**Formule (fixée maintenant).** Pour un verdict de Falcon, on regarde les positions et les
confiances du NLI affiné sur les passages :

| Verdict | Position attendue | Soutien `s` |
|---------|-------------------|-------------|
| vrai | « soutient » | la plus haute confiance parmi les passages **cités** qui soutiennent (0 s'il n'y en a pas) |
| faux | « contredit » | la plus haute confiance parmi les passages **cités** qui contredisent (0 s'il n'y en a pas) |
| trompeur | « soutient » ou « contredit » | la plus haute confiance parmi les passages **cités** qui soutiennent ou contredisent |
| preuves insuffisantes | « neutre » | la moyenne, sur les **5 passages proposés**, de la confiance s'il est neutre, et de 0 sinon |

**Incertitude u = 1 − s**, entre 0 et 1. Un verdict que les passages cités soutiennent nettement a
une incertitude basse ; un verdict « faux » sans aucun passage qui contredit a une incertitude de 1.
La formule n'a aucun paramètre réglé. Elle n'utilise que les sorties du NLI déjà calculées par le
pipeline : aucun appel supplémentaire à Falcon.

**Données.** Aucune nouvelle génération de Falcon :
- dev : les 30 verdicts d'EXP-D-018 (graine 42), relus depuis le cache ; le NLI est recalculé
  (déterministe) ;
- test v1 : les 21 verdicts d'EXP-D-015 (graine 42) ; recherche et NLI affiné recalculés.
  **Descriptif seulement.**

**Cibles.**
1. **Principale** : le verdict est **faux** (différent du verdict de référence).
2. **Secondaire** (descriptive) : le verdict est **mauvais**, c'est-à-dire faux **ou** jugé
   infidèle dans l'annotation humaine (EXP-D-016 pour le test, EXP-D-017 pour le dev).

**Mesures.** AUROC (l'incertitude classe-t-elle les verdicts faux au-dessus des justes ?), avec
IC 95 % par bootstrap (10 000 tirages, graine 42) ; score de Brier et erreur de calibration (ECE,
5 classes) à titre descriptif ; comparaison avec la valeur fixe actuelle (AUROC 0.5 par définition).

**Décision (fixée maintenant).** L'incertitude calculée est **adoptée** pour l'affichage si, sur le
dev, l'AUROC de la cible principale a une **borne basse de l'IC 95 % supérieure à 0.5**. Même
adoptée, elle est affichée comme « incertitude estimée par le NLI (indicateur de classement, non
calibré) » : avec 30 verdicts, on ne peut pas prétendre à une probabilité calibrée. Sinon, on garde
l'affichage actuel (« incertitude non calibrée »), et le résultat est écrit tel quel.

## 5. Ordre, identifiants, intégration

| Étape | Identifiant |
|-------|-------------|
| Re-ranker : vitesse et contrôle sur le dev, puis mesure unique sur le test v1 | EXP-D-020 |
| Incertitude : mesure sur le dev (décision), puis rapport descriptif sur le test v1 | EXP-D-021 |

Les deux expériences sont indépendantes : l'incertitude est mesurée sur le pipeline **sans**
re-ranker (celui des verdicts déjà générés). Chaque identifiant reçoit son entrée dans
`experiments.md`, même si le résultat est négatif. Si l'un des deux est adopté, son branchement
dans l'API (`RERANKER=...`, champ d'incertitude) est fait avec le Lot E (Achref), désactivable,
et décrit dans le README.

## 6. Interdits

- Choisir le modèle, le nombre de candidats ou la formule d'après un résultat sur le test v1.
- Relancer la mesure du test v1 ; toute relance est déclarée.
- Mesurer d'autres modèles de re-ranking sur le test v1.
- Présenter l'incertitude comme une probabilité calibrée.
- Mettre sur GitHub les sorties, caches, corpus ou annotations.
