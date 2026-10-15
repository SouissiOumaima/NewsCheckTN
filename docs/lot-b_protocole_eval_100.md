# Lot B — Protocole du jeu d'évaluation `eval_100`

## 1. Objectif

`eval_30` (34 phrases) ne permet plus de comparer le mode règles et le mode parseurs : après
EXP-B-003, il reste 6 et 7 erreurs, et une seule règle modifiée fait varier le score de plusieurs
points. De plus, les règles des expériences EXP-B-001 à EXP-B-003 ont été écrites en voyant ce jeu :
ses scores sont optimistes.

`eval_100` (environ 100 phrases) devient la **référence principale** (jeu de test). `eval_30`
reste un jeu de développement : on peut l'utiliser pour mettre au point des règles, pas pour
annoncer un résultat.

Principe : les phrases et leur annotation sont produites par une personne, **avant toute
exécution du système sur ces phrases**, puis le fichier est verrouillé.

## 2. Répartition cible

Proportionnelle à `eval_30` (10 / 10 / 5 / 5 / 4) :

| Groupe | `lang` | `script` | Phrases | Dont phrases réelles (cible) |
|--------|--------|----------|---------|------------------------------|
| Français | `fr` | `latin` | 30 | ≥ 15 |
| Arabe standard | `ar` | `arabic` | 30 | ≥ 15 |
| Tunisien, lettres arabes | `tn` | `arabic` | 15 | ≥ 5 |
| Tunisien, arabizi | `tn` | `arabizi` | 15 | ≥ 3 |
| Mixte FR / TN | `tn` | `mixed` | 10 | ≥ 2 |
| **Total** | | | **100** | **≥ 40** |

- **Affirmations** (`is_claim = true`) : 60 à 65 % des phrases (`eval_30` : 22 / 34), soit environ
  60 à 65. Le reste : opinions, questions, souhaits, hypothèses.
- **Phrases réelles** : phrases tirées telles quelles d'articles de presse, d'articles de
  fact-checking ou de publications publiques, avec leur origine (champ `origin`, section 5).
  Les autres sont rédigées pour le jeu (`origin.type = "rédigée"`).
- `lang` et `script` décrivent la langue et l'écriture **réelles** de la phrase, pas l'étiquette
  produite par le Lot A2.

### Sources des phrases réelles

État du Lot A1 au 2026-10-15 :
- branche `origin/lot-a1-data` (non fusionnée dans `main`), un seul scraper :
  `data/collect/tunifact_scraper.py` (tunifact.org), testé sur un seul article, langue fixée à `fr` ;
- aucune data card remplie, aucun fichier dans `data/processed/` ;
- **aucune liste de sources en arabe ou en tunisien** (fact-checkers ou presse) n'est encore disponible.

Conséquence : les sources des phrases réelles en arabe et en tunisien **sont à fixer avec le
Lot A1** (point de réunion). On n'en improvise pas ici. En attendant, seules les phrases
françaises peuvent s'appuyer sur la source déjà retenue par le Lot A1.

Règles pour toute phrase réelle :
- une phrase isolée (citation courte), jamais un article entier ; URL et date dans `origin` ;
- respecter les conditions d'utilisation des sites (mêmes règles que `data/README.md`) ;
- pas de contenu visant un particulier : seulement des personnes publiques ou des institutions.
  Dans une publication de réseau social, remplacer un nom de particulier par un rôle
  (« un habitant ») et le signaler dans `origin.note` ;
- ne pas corriger l'orthographe d'une phrase réelle (les fautes et variantes font partie de la mesure).

## 3. Phénomènes à couvrir

Une phrase peut couvrir plusieurs phénomènes. Les noms reprennent ceux de `eval_30` (guide
d'annotation, section 1) ; les nouveaux sont marqués *(nouveau)*. Ce sont des phénomènes
**linguistiques** : on ne crée pas de catégorie liée au système (« verbe hors lexique »…).

| Phénomène (`phenomena`) | Description | Minimum | Groupes concernés |
|-------------------------|-------------|---------|-------------------|
| `fait_chiffré` | affirmation avec nombre, pourcentage, montant ou date | 20 | tous |
| `opinion` | jugement, point de vue (`is_claim = false`) | 10 | tous |
| `question` | question directe | 6 | ≥ 3 groupes |
| `souhait` | souhait, espoir (« Inchallah », « يا ريت ») | 4 | ≥ 2 groupes |
| `hypothétique` | condition (« Si … », « إذا », « لو », « ken ») | 5 | ≥ 3 groupes |
| `rapporté` | verbe de parole + complétive (« a affirmé que », « قال إن », « 9al elli ») | 10 | tous |
| `source_citée` *(nouveau)* | source introduite par « selon », « d'après », « حسب », « وفق » | 6 | fr, ar, tn |
| `conditionnel_journalistique` | conditionnel de prudence (« aurait relevé ») | 5 | fr (+ mixte) |
| `futur_intention` *(nouveau)* | annonce ou intention (« va construire », « سوف », « bech ») | 6 | ≥ 3 groupes |
| `passif` | voix passive (dont passif arabe sans voyelles) | 5 | fr, ar |
| `copule` | « être » + attribut | 4 | fr, mixte |
| `phrase_nominale` | phrase arabe ou tunisienne sans verbe | 6 | ar, tn |
| `ordre_vso` *(nouveau)* | verbe arabe en tête de phrase (verbe-sujet-objet) | 8 | ar |
| `négation` | négation française ou arabe (« ne … pas », « لم », « لا », « لن ») | 6 | fr, ar |
| `négation_tn` *(nouveau)* | négation tunisienne « ما … ش » / « ma … ch », « mouch » | 5 | tn (les 3 écritures) |
| `complément_temps` *(nouveau)* | complément circonstanciel de temps | 10 | tous |
| `complément_lieu` *(nouveau)* | complément circonstanciel de lieu | 8 | tous |
| `coréférence` | pronom sujet à résoudre (avec `context`) | 10 | ≥ 4 groupes |
| `coréférence_affixe` *(nouveau)* | pronom affixe arabe ou tunisien (ـه، ـها، ـهم) à résoudre | 3 | ar, tn |
| `coordination` *(nouveau)* | deux affirmations coordonnées dans une phrase | 4 | ≥ 2 groupes |
| `code_switching` | alternance FR / TN dans la phrase | 10 | mixte |

Répartition minimale des modalités (gold) : `assertif` ≥ 35, `rapporté` ≥ 12, `opinion` ≥ 10,
`conditionnel` ≥ 6, `interrogatif` ≥ 6, `hypothétique` ≥ 5, `souhait` ≥ 4.

Cas sans règle d'annotation dans le guide actuel (à trancher et à ajouter au guide, section 6,
**avant** d'annoter ces phrases) :
- `coordination` : proposition principale = première proposition coordonnée (proposition à valider) ;
- `coréférence_affixe` : `resolved_text` remplace le pronom affixe par son antécédent, ou la phrase
  reste inchangée (à décider) ;
- `futur_intention` : le guide (section 2) compte une annonce datée comme affirmation ; une
  intention sans date reste à trancher.

## 4. Procédure

### 4.1 Avant de commencer
1. Relire `docs/lot-b_guide_annotation.md` et trancher les cas listés à la fin de la section 3.
2. Décider si l'on ajoute les champs gold facultatifs `source`, `time`, `location`
   (sortie détaillée depuis EXP-B-002). Par défaut : **non**. Le format reste celui de `eval_30`.
3. Copier le gabarit `tests/fixtures/linguistic_analysis/eval_100_template.jsonl` vers un fichier de
   travail **hors du dépôt**. Le fichier n'entre dans le dépôt qu'une fois verrouillé (étape 4.4).

### 4.2 Collecte et rédaction
- Réunir les phrases réelles (avec `origin`), puis compléter avec des phrases rédigées pour
  atteindre la répartition (section 2) et les minimums (section 3).
- Ne pas reprendre de phrases de `eval_30`, des tests (`tests/test_linguistic_analysis.py`), des
  exemples de la démo ou des documents du Lot B, ni de variantes proches de ces phrases.

### 4.3 Annotation, sans le système
Pendant toute la collecte et l'annotation, **ne pas exécuter le système sur ces phrases** :
pas de `linguistic_analysis.demo`, `evaluate.py`, `io_contract`, `pipeline.py`, API `/extract`
ou `/check`, ni notebook qui les appelle. Ne pas consulter non plus les fichiers
`evaluation/results/` produits sur ces phrases.

- Annoter chaque ligne selon le guide : `is_claim`, `subject`, `predicate`, `obj`, `modality`,
  et `resolved_text` pour les phrases de coréférence.
- `phenomena` : tous les phénomènes présents (section 3).
- Ne pas remplir `known_hard` : il dépend de la connaissance du système et transforme des échecs
  en tests indicatifs. Le champ reste réservé à `eval_30`.
- Noter à part chaque hésitation. Les cas tranchés vont dans le guide (section 6, « Cas discutés »).

### 4.4 Relecture croisée et verrouillage
1. **Double annotation** : une deuxième personne annote **sans voir** la première annotation au
   moins 30 phrases (6 par groupe, tirées au hasard). Mesures : accord sur `is_claim` et sur
   `modality` (exactitude et kappa de Cohen), sur `subject` / `predicate` / `obj` (correspondance
   exacte, formes repliées), calculées sans exécuter le système par
   `python -m linguistic_analysis.agreement annotation_a.jsonl annotation_b.jsonl`, qui liste aussi
   les désaccords.
   - Seuil : kappa ≥ 0.7 sur `is_claim`. En dessous, clarifier le guide puis réviser l'annotation.
   - Les désaccords sont tranchés à deux et ajoutés aux « Cas discutés » du guide.
2. **Contrôles automatiques sur le fichier seul** (sans exécuter le système) :
   `python -m linguistic_analysis.evaluate --eval-set <fichier> --validate`. Vérifie le format
   (JSON valide, champs obligatoires, langues / écritures autorisées, phénomènes connus, `id`
   uniques, `modality` dans `MODALITY_LABELS`, `context` + `resolved_text` pour `coréférence`,
   aucune valeur de gabarit `<…>` ni champ `_commentaire`) et affiche les effectifs par groupe,
   modalité et phénomène, à comparer aux minimums des sections 2 et 3.
3. **Verrouillage** :
   - placer le fichier dans `tests/fixtures/linguistic_analysis/eval_100.jsonl` ;
   - calculer son empreinte SHA-256 avec
     `python -m linguistic_analysis.evaluate --eval-set tests/fixtures/linguistic_analysis/eval_100.jsonl --sha256`
     et la noter dans la section 7 de ce document. Cette empreinte est calculée après avoir ramené
     les fins de ligne à LF : elle ne dépend pas du système (Windows ou Linux) ; elle peut donc
     différer de `sha256sum` ou `certutil` appliqués à une copie Windows en CRLF ;
   - un commit qui ne contient que ce fichier et la mise à jour de ce document :
     `test(lot-b): jeu d'évaluation eval_100 (verrouillé)`.

### 4.5 Après le verrouillage
- **Première exécution** : une seule fois, les deux modes et leur comparaison :
  `python -m linguistic_analysis.evaluate --eval-set tests/fixtures/linguistic_analysis/eval_100.jsonl --check-lock --compare`.
  L'évaluation est refusée si le fichier a changé depuis son verrouillage. Le résultat (scores
  par groupe et par phénomène avec effectifs, intervalles de confiance, différence parseurs −
  règles et son intervalle) est consigné tel quel dans une nouvelle entrée `EXP-B-NNN` de
  `experiments.md`, avec l'empreinte du fichier, le commit du code, la graine du bootstrap et la
  version de la normalisation du Lot A2 utilisée. Une différence dont l'intervalle contient 0
  est rapportée comme « non établie ».
- **Corrections du gold** : seulement pour une erreur d'annotation au regard du guide, jamais
  parce que le système produit autre chose. Chaque correction fait l'objet d'un commit séparé qui
  liste les `id`, la raison et la nouvelle empreinte (section 7).
- **Analyse d'erreurs** : autorisée. Mais toute règle modifiée après avoir vu les erreurs de
  `eval_100` rend les scores suivants optimistes. Ils sont alors rapportés comme un « 2ᵉ passage »,
  à côté du premier (comme EXP-B-001).
- Les phrases de `eval_100` ne sont jamais copiées dans les tests unitaires ni dans les lexiques.

## 5. Format

Même structure JSONL que `eval_30` : une ligne par phrase, encodage UTF-8.

```json
{"id": "fr-001", "lang": "fr", "script": "latin", "text": "…", "context": "…",
 "phenomena": ["fait_chiffré", "complément_temps"],
 "origin": {"type": "article", "source": "…", "url": "https://…", "date": "AAAA-MM-JJ", "note": "…"},
 "gold": {"is_claim": true, "subject": "…", "predicate": "…", "obj": "…",
          "modality": "assertif", "resolved_text": "…"}}
```

| Champ | Obligatoire | Contenu |
|-------|-------------|---------|
| `id` | oui | `fr-001` à `fr-030`, `ar-001` à `ar-030`, `tna-001` à `tna-015` (lettres arabes), `tnz-001` à `tnz-015` (arabizi), `mx-001` à `mx-010` |
| `lang` | oui | `fr`, `ar` ou `tn` |
| `script` | oui | `latin`, `arabic`, `arabizi` ou `mixed` |
| `text` | oui | la phrase évaluée (une seule phrase) |
| `context` | si `coréférence` | phrase(s) qui précèdent, nécessaires à la résolution |
| `phenomena` | oui | liste de la section 3 (au moins un élément) |
| `origin` | pour une phrase réelle | `type` : `article`, `fact-check`, `réseau_social` ou `rédigée` ; `source`, `url`, `date`, `note` (anonymisation…). Champ ignoré par l'évaluation actuelle |
| `gold.is_claim` | oui | `true` / `false` |
| `gold.subject`, `gold.predicate`, `gold.obj` | oui | extraits exacts de `text`, ou `null` ; évalués seulement si `is_claim = true` |
| `gold.modality` | oui | un label de `MODALITY_LABELS` (guide, section 4) |
| `gold.resolved_text` | si `coréférence` | phrase avec le pronom remplacé par son antécédent |

Les champs de `eval_30` sont repris à l'identique. Seul `origin` s'ajoute, au niveau de la phrase
et pas dans `gold`. `known_hard` n'est pas utilisé.

Gabarit : `tests/fixtures/linguistic_analysis/eval_100_template.jsonl`. Ses lignes sont des
exemples **fictifs** (valeurs entre chevrons), à supprimer. Le champ `_commentaire` sert seulement
au gabarit et ne doit pas figurer dans `eval_100.jsonl`.

## 6. Checklist « jeu prêt »

- [ ] Cas non couverts par le guide tranchés et ajoutés au guide (section 3), avant l'annotation
- [ ] 100 phrases (± 5) : FR 30, AR 30, TN lettres arabes 15, arabizi 15, mixte 10
- [ ] ≥ 40 phrases réelles avec `origin` complet ; sources validées avec le Lot A1
- [ ] Affirmations : 60 à 65 % ; minimums de modalités atteints (section 3)
- [ ] Chaque phénomène atteint son minimum (section 3)
- [ ] Aucune phrase reprise de `eval_30`, des tests, de la démo ou des documents du Lot B
- [ ] Annotation faite sans avoir exécuté le système sur ces phrases (déclaration de l'annotateur
      dans le commit de verrouillage)
- [ ] Double annotation d'au moins 30 phrases (`agreement.py`) ; kappa `is_claim` ≥ 0.7 ;
      désaccords tranchés et reportés au guide
- [ ] `evaluate.py --validate` sans erreur (format, `id` uniques, labels, coréférence, gabarit)
- [ ] Champs `_commentaire` et lignes d'exemple du gabarit supprimés
- [ ] Fichier verrouillé : empreinte (`evaluate.py --sha256`) notée en section 7, commit dédié,
      `evaluate.py --check-lock --validate` accepté

## 7. Verrouillage et historique

| Date | Événement | `id` concernés | SHA-256 de `eval_100.jsonl` |
|------|-----------|----------------|-----------------------------|
| — | — | — | — |
