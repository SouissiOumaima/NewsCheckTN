# Analyse de 30 erreurs — Model 1

Source : `errors_30_cross_seed.jsonl`. Chaque ligne est une prédiction fausse ; les catégories sont dérivées du gold label et de la modalité, puis restent à relire pour l'oral.

- Nombre d'erreurs : **30**
- Seeds : seed2026 = 5, seed42 = 25

## Répartition

| Catégorie | n |
| --- | ---: |
| affirmation non reconnue | 3 |
| autre confusion | 2 |
| discours rapporte non reconnu | 1 |
| hypothese non reconnue | 8 |
| opinion non reconnue | 7 |
| opinion pris pour autre | 6 |
| question non reconnue | 1 |
| souhait non reconnu | 2 |

## Exemples à présenter

- **autre confusion** — `P25` : gold `AUTRE`, prédit `OPINION` ; « Mon budget et de 25 mD , l'age max est de 4 ans , diesel ou mazout non problemo »
- **opinion pris pour autre** — `P30` : gold `OPINION`, prédit `AUTRE` ; « heyla la laguna mais la decote .. Une megane classique ph2 1.6 ar5es w tient mieu la cote en plus spacieuse w jawek behi »
- **opinion non reconnue** — `P43` : gold `OPINION`, prédit `AFFIRMATION` ; « Ce n'est pas normal , ena 3echtha el 7keya hethi des deux côtés : jadti mel bou tbajalna 3la wled bnetha w ta3tina dima lina a7na el 7ajet el behiya lkol .. »
- **hypothese non reconnue** — `P067` : gold `AUTRE`, prédit `AFFIRMATION` ; « Si la pluie continue, les cours pourraient être suspendus dans le gouvernorat de Jendouba. »
- **affirmation non reconnue** — `P289` : gold `AFFIRMATION`, prédit `OPINION` ; « النص المنسوب إلى الكاتب غير موجود في أي من كتبه. »
- **question non reconnue** — `P350` : gold `AUTRE`, prédit `AFFIRMATION` ; « كم يبلغ سعر تذكرة القطار إلى صفاقس؟ »
- **souhait non reconnu** — `P357` : gold `AUTRE`, prédit `OPINION` ; « ليت المسؤولين يستمعون إلى المواطنين. »
- **discours rapporte non reconnu** — `P417` : gold `AFFIRMATION`, prédit `AUTRE` ; « sma3t elli el sou9 bech ytsakker »

## Registre complet

| ID | Gold | Prédit | Modalité | Seed | Catégorie |
| --- | --- | --- | --- | --- | --- |
| P25 | AUTRE | OPINION | assertif | seed42 | autre confusion |
| P30 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P43 | OPINION | AFFIRMATION | opinion | seed42 | opinion non reconnue |
| P54 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P067 | AUTRE | AFFIRMATION | hypothétique | seed42 | hypothese non reconnue |
| P095 | AUTRE | AFFIRMATION | hypothétique | seed42 | hypothese non reconnue |
| P131 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P137 | OPINION | AFFIRMATION | opinion | seed42 | opinion non reconnue |
| P145 | AUTRE | AFFIRMATION | hypothétique | seed42 | hypothese non reconnue |
| P154 | AUTRE | OPINION | hypothétique | seed42 | hypothese non reconnue |
| P257 | AUTRE | AFFIRMATION | hypothétique | seed42 | hypothese non reconnue |
| P289 | AFFIRMATION | OPINION | assertif | seed42 | affirmation non reconnue |
| P343 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P350 | AUTRE | AFFIRMATION | interrogatif | seed42 | question non reconnue |
| P357 | AUTRE | OPINION | souhait | seed42 | souhait non reconnu |
| P417 | AFFIRMATION | AUTRE | rapporté | seed42 | discours rapporte non reconnu |
| P435 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P437 | OPINION | AFFIRMATION | opinion | seed42 | opinion non reconnue |
| P441 | OPINION | AFFIRMATION | opinion | seed42 | opinion non reconnue |
| P446 | OPINION | AFFIRMATION | opinion | seed42 | opinion non reconnue |
| P448 | OPINION | AUTRE | opinion | seed42 | opinion pris pour autre |
| P484 | AUTRE | AFFIRMATION | assertif | seed42 | autre confusion |
| P507 | AFFIRMATION | OPINION | assertif | seed42 | affirmation non reconnue |
| P555 | AUTRE | AFFIRMATION | hypothétique | seed42 | hypothese non reconnue |
| P597 | AUTRE | AFFIRMATION | souhait | seed42 | souhait non reconnu |
| P363 | AUTRE | OPINION | hypothétique | seed2026 | hypothese non reconnue |
| P411 | AFFIRMATION | AUTRE | assertif | seed2026 | affirmation non reconnue |
| P470 | AUTRE | AFFIRMATION | hypothétique | seed2026 | hypothese non reconnue |
| P535 | OPINION | AFFIRMATION | opinion | seed2026 | opinion non reconnue |
| P585 | OPINION | AFFIRMATION | opinion | seed2026 | opinion non reconnue |
