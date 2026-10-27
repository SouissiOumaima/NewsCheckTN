# Analyse d'erreurs — Model 1 (30 exemples)

## Protocole

Les exemples proviennent exclusivement du test gelé de 120 phrases. Le
checkpoint retenu pour l'application est **seed42** : il a 25 erreurs. Pour
atteindre les 30 exemples demandés sans inventer de cas, cinq erreurs dont
l'ID n'était pas déjà présent ont été ajoutées depuis **seed2026**. Le seed est
donc consigné pour chaque ligne. Les textes et labels de référence ne sont pas
modifiés.

Répartition linguistique des 30 erreurs : TN 22, AR 6, FR 2. Les proportions
ne constituent pas à elles seules une mesure par langue, mais elles confirment
que le tunisien (arabizi et mixte) est la priorité d'amélioration.

| ID | Seed | Gold → prédiction | Catégorie | Pourquoi le modèle se trompe |
| --- | --- | --- | --- | --- |
| P25 | 42 | AUTRE → OPINION | ambiguïté de check-worthiness | Budget personnel et contrainte d'achat : le ton « non problemo » ressemble à un avis, mais ce n'est pas une affirmation publique à vérifier. |
| P30 | 42 | OPINION → AUTRE | langue/script | Les comparatifs et jugements (« ar5es », « mieu », « behi ») sont dilués dans un texte TN mixte. |
| P43 | 42 | OPINION → AFFIRMATION | opinion vs affirmation | Le récit personnel contient des faits, mais « ce n'est pas normal » est le jugement déterminant. |
| P54 | 42 | OPINION → AUTRE | langue/script | L'opinion (« je vois », « lèzm ») est exprimée dans un mélange FR/TN peu représenté. |
| P067 | 42 | AUTRE → AFFIRMATION | modalité hypothétique | Le conditionnel introduit par « Si » est ignoré, avec confiance très élevée (0,990). |
| P095 | 42 | AUTRE → AFFIRMATION | modalité hypothétique | Même défaut en arabe : « إذا استمر » pose une condition, non un fait présent. |
| P131 | 42 | OPINION → AUTRE | opinion en arabizi | Insulte/jugement conversationnel sans marqueur français explicite ; le modèle le traite comme fragment. |
| P137 | 42 | OPINION → AFFIRMATION | opinion en arabizi | La situation factuelle masque le jugement « 3ib » (honteux/inacceptable). |
| P145 | 42 | AUTRE → AFFIRMATION | modalité hypothétique | Le marqueur tunisien « si » et le futur `bech` ne sont pas suffisamment appris. |
| P154 | 42 | AUTRE → OPINION | modalité hypothétique | La condition arabe tunisienne « كان ما... » est confondue avec une opinion. |
| P257 | 42 | AUTRE → AFFIRMATION | modalité hypothétique | La conséquence plausible est prédite comme fait malgré « Si ». |
| P289 | 42 | AFFIRMATION → OPINION | négation / langue arabe | Une assertion négative vérifiable (« non présent dans ses livres ») est assimilée à un avis. |
| P343 | 42 | OPINION → AUTRE | opinion brève | « كلام فارغ » est un jugement complet selon le guide, mais le modèle le voit comme fragment. |
| P350 | 42 | AUTRE → AFFIRMATION | interrogatif | La question directe en arabe est prise pour une proposition factuelle. |
| P357 | 42 | AUTRE → OPINION | souhait | « ليت » exprime un souhait, pas l'opinion du locuteur sur un fait. |
| P417 | 42 | AFFIRMATION → AUTRE | discours rapporté | Le marqueur TN `sma3t elli` (« j'ai entendu que ») n'est pas reconnu comme parole rapportée. |
| P435 | 42 | OPINION → AUTRE | opinion en arabizi | « ma ya3mel chay » est un jugement politique, classé à tort comme énoncé incomplet. |
| P437 | 42 | OPINION → AFFIRMATION | opinion normative | `n9oul` et `lezmou` portent une recommandation, mais le modèle privilégie sa forme déclarative. |
| P441 | 42 | OPINION → AFFIRMATION | opinion en arabizi | L'adjectif évaluatif `5ayeb` est ignoré ; erreur très confiante (0,993). |
| P446 | 42 | OPINION → AFFIRMATION | opinion figurée | La métaphore pessimiste « el bled mechya lel louta » est traitée comme fait. |
| P448 | 42 | OPINION → AUTRE | opinion + souhait | Le désir `n7eb` et le pessimisme `ma famech amal` créent un cas mixte mal séparé. |
| P484 | 42 | AUTRE → AFFIRMATION | portée de la vérifiabilité | Achat personnel au passé : phrase factuelle, mais hors des affirmations check-worthy visées. |
| P507 | 42 | AFFIRMATION → OPINION | tunisien en écriture arabe | Rupture de stock concrète, classée opinion probablement à cause de la forme dialectale. |
| P555 | 42 | AUTRE → AFFIRMATION | modalité hypothétique | La condition `كان تزيد الأسعار` est ignorée. |
| P597 | 42 | AUTRE → AFFIRMATION | souhait | `inchallah` devrait être un signal fort de souhait. |
| P363 | 2026 | AUTRE → OPINION | modalité hypothétique | La condition `إذا تواصل` est transformée en opinion. |
| P411 | 2026 | AFFIRMATION → AUTRE | arabizi | Deux affirmations courtes (« mer agitée », « baignade interdite ») ne sont pas reconnues dans le dialecte. |
| P470 | 2026 | AUTRE → AFFIRMATION | modalité hypothétique | `ken` (« si ») n'empêche pas la prédiction factuelle. |
| P535 | 2026 | OPINION → AFFIRMATION | opinion en arabe tunisien | « ظلم » (injuste) est un jugement de valeur pris comme fait. |
| P585 | 2026 | OPINION → AFFIRMATION | langue/script | `nul` est un jugement français dans une phrase TN mixte ; le mélange perturbe le modèle. |

## Causes regroupées

| Cause dominante | Nombre | Observation |
| --- | ---: | --- |
| Conditionnel / hypothétique | 8 | `si`, `إذا`, `كان`, `ken` doivent être mieux représentés au train. |
| Opinion, surtout TN arabizi/mixte | 13 | Les marqueurs évaluatifs (`5ayeb`, `nul`, `3ib`, `ظلم`) et normatifs doivent être enrichis. |
| Question, souhait, rapporté | 4 | Les indicateurs `؟`, `ليت`, `inchallah`, `sma3t elli` sont sous-appris. |
| Assertion directe / portée check-worthy | 5 | Négation, dialecte et événements personnels posent une frontière d'annotation délicate. |

## Décision

Ne pas modifier le modèle à partir de ces 30 exemples seuls : ils appartiennent
au test gelé. Ils servent à définir les données supplémentaires à annoter pour
une itération future : davantage de TN arabizi/mixte, de conditionnels et de
souhaits/questions, puis un nouveau jeu de développement distinct du test.
