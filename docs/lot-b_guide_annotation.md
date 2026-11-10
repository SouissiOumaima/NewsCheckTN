# Lot B — Guide d'annotation (affirmations, SPO, modalité)

Ce guide fixe les règles utilisées pour annoter le jeu d'évaluation du Lot B
(`tests/fixtures/linguistic_analysis/eval_30.jsonl`). Toute nouvelle annotation doit le suivre ;
en cas de doute, ajouter l'exemple à la section « Cas discutés ».

## 1. Format d'une ligne

```json
{"id": "fr-01", "lang": "fr", "script": "latin", "text": "...", "context": "...",
 "phenomena": ["fait_chiffré"], "known_hard": {"spo": "raison"},
 "gold": {"is_claim": true, "subject": "...", "predicate": "...", "obj": "...",
          "modality": "assertif", "resolved_text": "..."}}
```

- `lang` / `script` : langue et écriture **réelles** de la phrase (pas l'étiquette produite par le Lot A2).
  Groupes d'évaluation : `fr-latin`, `ar-arabic`, `tn-arabic`, `tn-arabizi`, `tn-mixed` (code-switching FR/TN).
- `context` (facultatif) : phrases précédentes, nécessaires pour la coréférence.
- `phenomena` : phénomènes couverts (`fait_chiffré`, `opinion`, `question`, `rapporté`,
  `conditionnel_journalistique`, `copule`, `phrase_nominale`, `passif`, `négation`, `coréférence`,
  `code_switching`, `souhait`, `hypothétique`).
- `known_hard` (facultatif) : champ → raison, pour les cas jugés difficiles **avant** de lancer le
  système. Les tests correspondants sont indicatifs (`xfail`).
- Les valeurs `gold` s'écrivent dans l'orthographe habituelle ; l'évaluation compare des formes
  repliées (minuscules, arabe sans diacritiques, alef / ya / ta marbuta unifiés), comme la
  normalisation du Lot A2.

## 2. `is_claim` : est-ce une affirmation vérifiable ?

`true` si la phrase affirme quelque chose sur le monde qui peut être confronté à des sources,
même si l'affirmation est :
- rapportée (« Selon l'INS, … », « Le ministre a affirmé que … ») ;
- au conditionnel journalistique (« La banque aurait relevé son taux… ») ;
- introduite par un verbe d'opinion mais contenant une donnée précise
  (« Je pense que le chômage a atteint 16 % en 2023 ») ;
- une annonce datée (« Le projet commencera en septembre »).

`false` pour :
- une opinion ou un jugement de valeur (« Cette décision est injuste ») ;
- une question ;
- un souhait (« Inchallah les prix baisseront ») ;
- une hypothèse (« Si la sécheresse continue, la production baissera »).

## 3. Sujet, prédicat, objet

On annote le triplet de la **proposition principale**. Pour une affirmation rapportée, c'est
la proposition du verbe de parole (« Le ministre | a affirmé | le déficit avait baissé »),
mais avec « Selon X, … » la proposition principale est celle qui suit (« l'inflation | a reculé | à 7 % »).

- **Sujet** : groupe nominal complet, compléments du nom inclus (« Le taux de chômage en Tunisie »).
  Pronom sujet : on annote le pronom tel quel (la version résolue va dans `resolved_text`).
  Sujet absent ou impersonnel (« 9alou … ») : `null`.
- **Prédicat** : groupe verbal avec auxiliaires, négation et pronoms réfléchis
  (« n'a pas augmenté », « ont été inaugurées », « ما هبطتش »).
  Verbe modal + infinitif : les deux forment le prédicat (« pourraient augmenter »).
  Copule : la copule seule (« est »). Phrase nominale arabe sans verbe : prédicat implicite `"est"`.
- **Objet** : complément d'objet direct avec ses propres compléments ; à défaut, premier complément
  prépositionnel régi par le verbe (« de 12 % », « à 7 % », « par le gouvernement » au passif).
  Les compléments circonstanciels de **temps** et de **lieu** ne font pas partie de l'objet
  (« en 2024 », « depuis janvier », « fi Gafsa »). Copule : l'attribut. Discours rapporté :
  la complétive sans le complémenteur (« que », « إن », « elli »). Aucun objet : `null`.
- Les éléments sont des extraits **exacts** de la phrase, sans ponctuation de bord.
- Le triplet n'est évalué que pour les phrases `is_claim = true`.

## 4. Modalité

Un seul label, choisi selon cet ordre de priorité :

`interrogatif` > `souhait` > `hypothétique` > `conditionnel` > `rapporté` > `opinion` > `assertif`

| Label | Quand l'utiliser | Exemples |
|-------|------------------|----------|
| `interrogatif` | question directe | « … ? », « هل … », « Est-ce que … » |
| `souhait` | souhait, espoir, injonction, requête polie (« merci d'avance », « svp », « 3aychek ») | « يا ريت », « Inchallah », « J'espère que » |
| `hypothétique` | condition irréelle ou éventuelle | « Si … », « إذا », « لو », « ken » |
| `conditionnel` | conditionnel, dont journalistique | « aurait relevé », « pourraient » |
| `rapporté` | source citée ou verbe de parole + complétive | « Selon … », « حسب », « 9alou », « a affirmé que » |
| `opinion` | jugement, point de vue du locuteur | « Je trouve que », « في رأيي », « n7ess » |
| `assertif` | affirmation directe (défaut) | « Le prix du pain n'a pas augmenté » |

L'incertitude (peut-être, ربما, ymken) et le futur (bech, سوف) ne changent pas le label :
ils sont mesurés par le score de certitude, qui n'est pas annoté ici.

## 5. `resolved_text` (coréférence)

Pour une phrase dont le sujet est un pronom à résoudre, `resolved_text` est la phrase où **seul**
le pronom sujet est remplacé par son antécédent, tel qu'il apparaît dans le contexte
(« Elle a annoncé … » → « La ministre de la Santé a annoncé … »). Une conjonction collée au pronom
arabe est conservée (« وهو » → « والوزير »).

## 6. Cas discutés

- « Les prix tal3ou barcha » (affirmation vague, sans chiffre) : annotée `is_claim = true` (une hausse
  des prix est vérifiable), mais marquée difficile (frontière fait / opinion).
- Passif arabe sans voyelles (« أعلنت نتائج … ») : forme identique à l'actif « elle a annoncé » ;
  annoté selon le sens (passif), marqué difficile.
