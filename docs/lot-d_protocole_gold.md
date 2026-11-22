# Lot D — Protocole Gold : audit du verdict

**Responsable : Hadil Lajili (Membre 5, Lot D) · Version 1 (brouillon) · 2026-11-22**

Ce fichier est écrit et commité **avant toute mesure du Gold**. Une mesure faite avant son
commit ne compte pas. Une règle changée après une mesure sur le test doit être déclarée comme
telle dans `experiments.md`.

## 1. Système audité

| Élément | Valeur (fixée) |
|---------|----------------|
| LLM du verdict | Falcon-H1-3B-Instruct, GGUF Q4_K_M, Ollama local (EXP-D-015) |
| Format | JSON imposé (`LLM_RESPONSE_FORMAT=json`), prompt v1, température 0.3 |
| Graines | 13, 42, 2026 |
| Recherche | hybride BM25 + e5-base, RRF k = 60, top 5 (EXP-D-008) |
| NLI | **NLI affiné du Lot C** (checkpoint graine 42, EXP-C-011), `NLI_BACKEND=fine-tuned`, préchargé par l'API (PR #39) ; choix proposé par Wiem (Lot C) le 2026-11-22 |
| Données externes | aucune : `LLM_ALLOW_EXTERNAL=0`, aucune API |

Aya Expanse 8B (EXP-D-010) n'est plus utilisé ; son entrée reste dans `experiments.md` comme historique.

**Changement de configuration par rapport à EXP-D-014/015 (Bronze → affiné), déclaré ici.** Le
système principal n'affiche pas les positions NLI au LLM (`show_nli = False`) : les réponses de
Falcon ne changent pas. Le NLI ne sert qu'au repli sur le gabarit (sortie rejetée, 3 % des cas
dans EXP-D-015) et à la règle R-abst (section 5).

## 2. Questions

1. **Citations** : les passages cités par le verdict sont-ils **pertinents** ? Le verdict
   contient-il des **faits inventés**, absents des passages cités ?
2. **Fidélité** : l'explication dit-elle ce que disent les passages cités ?
3. **Abstention** : une règle sans seuil réglé (section 5) corrige-t-elle les verdicts émis sans
   preuve (phrases hors sujet, affirmations sans passage utile) sans perdre les bons verdicts ?
4. **LLM-juge** : un LLM local peut-il remplacer l'annotation humaine pour les questions 1 et 2 ?
   On le vérifie par son accord avec des décisions humaines.

## 3. Jeux de données

| Jeu | Contenu | Usage autorisé |
|-----|---------|----------------|
| **Dev** | 20 affirmations fictives (`tests/fixtures/rag_llm/claims_dev.jsonl`) + **10 phrases hors sujet** rédigées (5 fr, 3 ar, 2 tn) | mettre au point le prompt du juge et la règle d'abstention ; autant de passages que nécessaire |
| **Test v1 (déjà vu)** | Tunifact v1 : 21 affirmations, 84 passages, gelé le 2026-10-23 | **audit descriptif seulement** des sorties existantes d'EXP-D-015 ; aucun nouveau passage, aucune décision |
| **Test v2 (jamais vu)** | nouvelles affirmations tirées d'articles **absents** de Tunifact v1, cible 30 (10 fr, 10 ar, 10 tn) + 5 phrases hors sujet | **un seul passage**, après toutes les décisions du dev |

Règles pour le test v2 :
- les affirmations, leur langue et leur verdict de référence sont écrits par une personne **avant**
  toute exécution du système ; puis le fichier est gelé avec son SHA-256 (même méthode que
  `rag_llm.freeze_test`) et ce gel est commité ;
- les articles viennent du Lot A1 (Ghofran) ; leur provenance est notée ; le corpus n'est pas
  versionné (droits non confirmés), comme pour Tunifact v1 ;
- si le test v2 n'est pas prêt à temps, le Gold est rapporté sur le dev et l'audit descriptif du
  test v1, et l'absence du test v2 est écrite comme une limite.

## 4. Annotation humaine

Unité : un **verdict** de Falcon (graine 42) et chacun des passages qu'il cite.

| Étiquette | Valeurs | Question posée |
|-----------|---------|----------------|
| `pertinence` (par passage cité) | `pertinent` / `non_pertinent` | Le passage parle-t-il du fait de l'affirmation (même événement, même chiffre, même personne) ? |
| `invente` (par verdict) | `oui` / `non` | L'explication affirme-t-elle un fait absent de tous les passages cités ? |
| `fidelite` (par verdict) | `fidele` / `infidele` | Chaque phrase de l'explication est-elle soutenue par un passage cité ? (un seul point non soutenu → `infidele`) |

- Annotation faite **sans voir** l'avis du juge, et avant de lancer le juge sur le même jeu.
- Annotatrice principale : Hadil. **Seconde annotatrice : Wiem Saafi** (accord du 2026-11-22),
  sur 10 verdicts du dev, sans outil d'IA, avec le guide `docs/lot-d_guide_annotation_verdict.md`.
  On mesure l'accord entre humains (kappa de Cohen). Les deux annotatrices travaillent sans voir
  les étiquettes de l'autre.
- Les annotations restent privées (`evaluation/results/lot-d_*`, hors GitHub), comme les traces.

## 5. Règle d'abstention évaluée

**R-abst** : si **tous** les passages cités par le verdict ont la position NLI `neutre`, le
verdict devient `preuves_insuffisantes`. Aucun seuil n'est réglé (comme EXP-C-015, τ = 0).

Comparaison : Falcon sans règle contre Falcon + R-abst, sur les mêmes sorties (la règle
s'applique après le LLM : aucune nouvelle génération n'est nécessaire).

**Décision (fixée maintenant)** : R-abst est adoptée pour le test v2 si, sur le dev,
1. l'abstention justifiée augmente (affirmations sans preuve et phrases hors sujet), **et**
2. l'exactitude sur les affirmations qui ont une preuve ne baisse pas de plus d'**une** affirmation.

Sinon, elle n'est pas adoptée, et le résultat est écrit tel quel.

Point d'attention (Lot C, EXP-C-016) : quand le NLI affiné se trompe, il répond surtout `neutral`
(7 erreurs sur 10). R-abst risque donc de s'appliquer plus souvent qu'avec Bronze, y compris sur
des affirmations qui ont une preuve. C'est précisément ce que vérifie la condition 2 sur le dev ;
on rapporte aussi le nombre d'affirmations avec preuve transformées à tort en abstention.

## 6. LLM-juge

- Modèle : **différent de Falcon** (un modèle ne juge pas ses propres verdicts), ≤ 8 Md de
  paramètres, local (Ollama, GPU 4 Go), multilingue fr / ar. **Modèle fixé : `qwen2.5:3b-instruct`**
  (Ollama, ID 357c53fb659c, 2,2 Go, 100 % GPU, contexte 4 096 jetons ; essai sur le PC le 2026-11-22).
  Choisi **avant** de voir ses accords, et non changé ensuite.
- Falcon et le juge ne tiennent pas ensemble sur 4 Go : on génère d'abord tous les verdicts, puis
  on lance le juge sur les sorties enregistrées.
- Limite connue avant mesure : à l'essai, une consigne en deux langues n'a reçu qu'une réponse en
  arabe ; le respect du format JSON et le tunisien sont vérifiés sur la moitié de mise au point du dev.
- Il reçoit l'affirmation, l'explication et les passages cités ; il rend en JSON les trois
  étiquettes de la section 4. Prompt versionné (`rag_llm/prompts/juge_v1.txt`), température 0.
- Le prompt est mis au point sur la **moitié** du dev (graine de tirage 42), puis mesuré sur
  l'autre moitié du dev sans modification.
- **Validation (fixée maintenant)** : le juge est déclaré validé pour une étiquette si son kappa
  de Cohen avec l'annotation humaine est **≥ 0.60** sur la moitié de mesure du dev. Une étiquette
  non validée n'est pas notée par le juge sur le test v2 : elle reste annotée à la main.
- Sur le test v2, on rapporte de nouveau l'accord juge / humain : c'est la vraie mesure de validité.

## 7. Mesures et statistiques

| Mesure | Définition |
|--------|------------|
| Citations valides | part des citations présentes dans P1..P5 (déjà contrôlé par le code) |
| Précision des citations | part des passages cités jugés `pertinent` |
| Taux d'invention | part des verdicts avec `invente = oui` |
| Fidélité | part des verdicts `fidele` |
| Abstention justifiée, couverture, précision sélective, exactitude | comme EXP-D-010 (`evaluate_verdict`) |
| Accord juge / humain | kappa de Cohen et accord brut, par étiquette |

- 3 graines (13, 42, 2026) pour le verdict ; annotation humaine sur la graine 42.
- Intervalles : bootstrap apparié, 10 000 tirages, graine 42 ; IC à 95 % du kappa par bootstrap.
- Résultats par langue (fr, ar, tn) ; les effectifs sont petits : ils sont toujours écrits à côté.

## 8. Ordre et identifiants

| Étape | Jeu | Identifiant réservé |
|-------|-----|---------------------|
| Audit descriptif des sorties d'EXP-D-015 (pertinence, invention, fidélité) | test v1 | EXP-D-016 |
| Mise au point puis mesure du juge | dev | EXP-D-017 |
| R-abst sans règle / avec règle | dev | EXP-D-018 |
| Passage unique : Falcon (+ R-abst si adoptée), annotation, juge | test v2 | EXP-D-019 |

Chaque identifiant reçoit son entrée dans `experiments.md`, même si le résultat est négatif.

## 9. Interdits

- Régler quoi que ce soit (prompt, règle, modèle, seuil) sur le test v1 ou le test v2.
- Relancer le test v2 après le premier passage ; toute relance est déclarée comme 2e passage.
- Utiliser Falcon comme juge, ou une API externe.
- Mettre sur GitHub les sorties, caches, traces, annotations ou le corpus.
- Présenter l'incertitude fixe de 0.40 comme une probabilité calibrée.

## 10. Points à fixer avant le commit

1. ~~NLI~~ : fixé (affiné, EXP-C-011, proposé par Wiem le 2026-11-22 ; à confirmer par Achref pour la démo).
2. ~~Modèle du juge~~ : fixé (`qwen2.5:3b-instruct`, 100 % GPU, essai du 2026-11-22).
3. ~~Seconde annotatrice~~ : Wiem, 10 verdicts du dev.
4. Test v2 : articles disponibles auprès du Lot A1, et date de gel.
