# Lot B — Analyse d'erreurs, palier Bronze (EXP-B-001)

Jeu : `tests/fixtures/linguistic_analysis/eval_30.jsonl` (34 phrases ; 22 affirmations).
Classement détaillé : `tests/fixtures/linguistic_analysis/error_categories.json` (vérifié par les tests).
Reproduire :

```bash
python -m linguistic_analysis.evaluate --rules --errors   # mode règles (conditions de la CI)
python -m linguistic_analysis.evaluate --errors           # mode parseurs (spaCy FR, Stanza AR)
```

Une **erreur** = une phrase × un champ faux (`is_claim`, `modality`, `subject`, `predicate`, `obj`,
`resolved_text`). Le triplet n'est compté que pour les affirmations du gold. Chaque erreur reçoit
**une** catégorie principale :

| Code | Catégorie |
|------|-----------|
| E1 | segmentation / tokenisation (dont arabizi et clitiques) |
| E2 | erreur du parseur (POS ou dépendance fausse sur une phrase de la bonne langue) |
| E3 | lexique incomplet (verbe, marqueur d'opinion ou de modalité absent) |
| E4 | règle SPO inadaptée (objet, copule, passif, phrase nominale, ordre des mots) |
| E5 | modalité mal priorisée ou mal ciblée |
| E6 | coréférence (mauvais antécédent ou absence de résolution) |
| E7 | effet du traitement amont (normalisation, identification de langue) |
| E8 | ambiguïté réelle ou annotation discutable |

Critère E7 : l'erreur est classée E7 seulement si elle **disparaît lorsque la phrase est traitée
selon sa langue réelle** (par exemple, correcte en mode règles mais fausse lorsque la phrase
tunisienne passe par le modèle de l'arabe standard). Sinon : E2 (arbre faux) ou E4 (règle).

## 1. Résultats (2ᵉ passage)

| Mode | Détection (exact. / macro-F1) | Modalité | Sujet | Prédicat | Objet | Triplet complet | Coréf. (3) |
|------|------------------------------|----------|-------|----------|-------|-----------------|------------|
| règles | 1.00 / 1.00 | 1.00 | 0.59 | 0.68 | 0.64 | 0.46 | 0.67 |
| parseurs | 1.00 / 1.00 | 1.00 | 0.91 | 0.86 | 0.50 | 0.46 | 1.00 |

Correspondance partielle (F1 de tokens), sujet / prédicat / objet :
règles 0.63 / 0.68 / 0.71 ; parseurs 0.91 / 0.89 / 0.64.

Triplet complet exact par groupe :

| Groupe | n | règles | parseurs |
|--------|---|--------|----------|
| fr-latin | 10 | 0.50 | 0.50 |
| ar-arabic | 10 | 0.29 | 0.43 |
| tn-arabic | 5 | 0.50 | 0.00 |
| tn-arabizi | 5 | 0.67 | 0.67 |
| tn-mixed | 4 | 0.50 | 0.50 |

Le 1ᵉʳ passage (avant correction) donnait : règles — détection 0.97, modalité 0.97, triplet 0.41 ;
parseurs — détection 0.97, modalité 1.00, triplet 0.46 (voir section 4).

## 2. Répartition des erreurs

### Mode règles (25 erreurs)

| Cat. | fr-latin | ar-arabic | tn-arabic | tn-arabizi | tn-mixed | Total |
|------|---------:|----------:|----------:|-----------:|---------:|------:|
| E1 | 0 | 0 | 2 | 0 | 0 | 2 |
| E2 | 0 | 0 | 0 | 0 | 0 | 0 |
| E3 | 3 | 8 | 0 | 0 | 2 | 13 |
| E4 | 3 | 5 | 0 | 1 | 0 | 9 |
| E5 | 0 | 0 | 0 | 0 | 0 | 0 |
| E6 | 0 | 1 | 0 | 0 | 0 | 1 |
| E7 | 0 | 0 | 0 | 0 | 0 | 0 |
| E8 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | 6 | 14 | 2 | 1 | 2 | **25** |

### Mode parseurs (16 erreurs)

| Cat. | fr-latin | ar-arabic | tn-arabic | tn-arabizi | tn-mixed | Total |
|------|---------:|----------:|----------:|-----------:|---------:|------:|
| E1 | 0 | 0 | 0 | 0 | 0 | 0 |
| E2 | 4 | 0 | 2 | 0 | 0 | 6 |
| E3 | 0 | 0 | 0 | 0 | 2 | 2 |
| E4 | 2 | 3 | 0 | 1 | 0 | 6 |
| E5 | 0 | 0 | 0 | 0 | 0 | 0 |
| E6 | 0 | 0 | 0 | 0 | 0 | 0 |
| E7 | 0 | 1 | 1 | 0 | 0 | 2 |
| E8 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | 6 | 4 | 3 | 1 | 2 | **16** |

Lecture : sans parseur, l'essentiel des erreurs vient du **lexique verbal** (E3, surtout en arabe
standard) ; avec parseur, il reste surtout des **erreurs de choix de l'objet** (E4) et des
**erreurs d'arbre** (E2). La détection d'affirmation et la modalité ne produisent plus d'erreur.

## 3. Exemples commentés

### E1 — Segmentation / tokenisation
- **tn-a4** (règles) — « الأسعار ما هبطتش الشهر هذا. » (les prix n'ont pas baissé ce mois-ci)
  - sortie : aucun triplet ; attendu : sujet « الأسعار », prédicat « ما هبطتش » ;
  - cause : la négation dialectale ما…ش colle le suffixe ش au verbe ; « هبطتش » n'est pas reconnu
    alors que « هبطت » est dans le lexique ;
  - correction : segmenter le suffixe ش (et le préfixe ما) avant la recherche lexicale.
- Seul cas observé dans ce jeu.

### E2 — Erreur du parseur
- **fr-02** (spaCy) — « Trois nouvelles stations de dessalement ont été inaugurées par le gouvernement. »
  - sortie : aucun triplet ; attendu : « Trois nouvelles stations de dessalement | ont été inaugurées | par le gouvernement » ;
  - cause : spaCy fait de « stations » la racine, analyse « inaugurées » comme modifieur du nom (`acl`)
    et « dessalement » comme adverbe ; il n'y a ni verbe racine ni sujet ;
  - correction : repli sur les règles lorsque l'arbre n'a pas de racine verbale alors qu'un verbe fini existe.
- **tn-a4** (Stanza) — même phrase qu'en E1
  - sortie : prédicat « هبطتش » (sans « ما »), objet « الشهر » ; attendu : « ما هبطتش », pas d'objet ;
  - cause : « ما » étiqueté déterminant (`DET/obl`) au lieu de négation ; « الشهر » (temps) étiqueté `obj` ;
  - correction : traiter « ما » devant un verbe comme négation, quelle que soit l'étiquette.

### E3 — Lexique incomplet
- **ar-01** (règles) — « ارتفع عدد السياح الوافدين على تونس بنسبة 15 بالمئة. »
  - sortie : aucun triplet ; attendu : « عدد السياح الوافدين على تونس | ارتفع | بنسبة 15 بالمئة » ;
  - cause : le lexique verbal du mode règles ne contient que des verbes tunisiens fréquents ;
    « ارتفع » (a augmenté) en est absent — de même « تراجع », « ترتفع » (ar-03, ar-06) ;
  - correction : lexique de verbes de l'arabe standard (presse économique) ou repérage morphologique
    des formes verbales (schèmes, préfixes de l'inaccompli).
- **fr-07** (règles) — « La banque centrale aurait relevé son taux directeur la semaine dernière. »
  - sortie : aucun triplet ; cause : « aurait » absent de la liste des auxiliaires ;
  - correction : ajouter les auxiliaires au conditionnel et au futur (aurait, serait, aura, sera…).

### E4 — Règle SPO inadaptée
- **fr-05** (spaCy) — « Selon l'Institut national de la statistique, l'inflation a reculé à 7 %. »
  - sortie : objet « Selon l'Institut national de la statistique » ; attendu : « à 7 % » ;
  - cause : la règle prend le premier complément `obl*` ; la source (`obl:mod`) précède le complément
    régi « à 7 % » (`obl:arg`) ; même erreur en arabe avec « حسب البنك المركزي » (ar-03) ;
  - correction : préférer `obl:arg` et exclure les compléments introduits par selon / d'après / حسب / وفق.
- **fr-03** (spaCy et règles) — « Le prix du pain n'a pas augmenté depuis janvier. »
  - sortie : objet « depuis janvier » ; attendu : aucun objet ;
  - cause : les compléments de temps et de lieu ne sont pas distingués (aussi ar-05, ar-06, fr-01, tn-z1) ;
  - correction : exclure de l'objet les `obl` temporels / locatifs (prépositions depuis, en + année,
    pendant ; noms يوم, الشهر, السنة ; fi + lieu) — en mode règles, couper l'objet à ces marqueurs.

### E5 — Modalité
- Aucune erreur au 2ᵉ passage.
- 1ᵉʳ passage, **ar-09** — « إذا استمر الجفاف فإن الإنتاج الفلاحي سينخفض. » (si la sécheresse continue,
  la production baissera) : modalité `hypothétique` correcte, mais phrase classée affirmation, car la
  décision ne tenait compte que de l'opinion ; corrigé par `ExtractedClaim.is_claim`, qui exclut les
  modalités non factuelles.

### E6 — Coréférence
- **ar-10** (règles) — contexte « زار رئيس الحكومة ولاية قفصة. », phrase « هو أعلن عن مشاريع جديدة في الجهة. »
  - sortie : phrase inchangée ; attendu : « رئيس الحكومة أعلن عن مشاريع جديدة في الجهة. » ;
  - cause : en ordre verbe-sujet-objet sans complémenteur, le sujet du contexte est réduit à
    « رئيس » (sans article), donc non retenu comme mention définie : abstention ;
  - correction : étendre le sujet à l'annexion (إضافة) « رئيس الحكومة ».
- Hors de ce jeu (fixture de développement) : « Selon le ministère de la Santé, 120 nouveaux cas ont
  été enregistrés. Il a appelé à la vigilance. » — l'antécédent est la source, non couverte au Bronze.

### E7 — Effet du traitement amont (point à discuter avec le Lot A2)
- **ar-01** (Stanza) — la normalisation remplace ة par ه : « نسبة » devient « نسبه », que Stanza
  découpe en « نسب » + pronom « ه » ; « 15 » devient alors l'objet au lieu de « بنسبة 15 بالمئة ».
- **tn-a1** (Stanza) — « الوزارة قالت اللي سوم الزيت هبط 20 بالمية. » est étiquetée arabe standard en
  amont, donc analysée par le modèle de l'arabe standard, qui ne connaît pas le complémenteur tunisien
  « اللي » ; la même phrase est correcte en mode règles.
- Pistes à discuter : disposer, en plus du texte normalisé pour la recherche, d'une version qui
  conserve le tā' marbūṭa (ou d'un alignement avec le texte brut) ; distinguer arabe standard et
  tunisien en lettres arabes, ou marquer la langue par segment.

### E8 — Ambiguïté ou annotation discutable
- Aucune erreur classée E8 dans ce passage. Deux annotations restent discutables, sans erreur du
  système : **mx-2** « Les prix tal3ou barcha… » (affirmation vague, sans chiffre) et **ar-05**
  « أعلنت نتائج الامتحانات… » (passif non vocalisé, identique à l'actif « elle a annoncé »).
- Le jeu a été annoté par une seule personne : une double annotation permettrait de mesurer l'accord
  et de mieux distinguer E8 des autres catégories.

## 4. Erreurs du 1ᵉʳ passage, corrigées avant le 2ᵉ

| Phrase | Champ | Catégorie | Correction (générale, gold inchangé) |
|--------|-------|-----------|---------------------------------------|
| ar-09 | is_claim | E5 | `is_claim` exclut les modalités hypothétique / interrogatif / souhait / opinion |
| ar-04 | modality (règles) | E4 | ordre verbe-sujet-objet + verbe de parole : sujet jusqu'au complémenteur |
| fr-05 | obj (règles) | hors taxonomie (défaut d'implémentation) | « % » n'est plus retiré en bord de groupe |

Ces corrections ont été faites après avoir vu les erreurs du jeu : les scores du 2ᵉ passage sont
donc optimistes ; il faut les citer avec ceux du 1ᵉʳ passage.

## 5. Priorités pour le palier Silver

| Priorité | Action | Erreurs visées | Impact | Effort |
|----------|--------|----------------|--------|--------|
| 1 | Objet : exclure les compléments de temps / lieu et les sources (selon, حسب), préférer `obl:arg` | E4 : 6 (parseurs), 4 (règles) | élevé | faible |
| 2 | Lexique verbal du mode règles : verbes de l'arabe standard, auxiliaires au conditionnel, flexions tunisiennes (tal3ou…) ou repérage morphologique | E3 : 13 (règles), 2 (parseurs) | élevé (mode CI, tunisien) | moyen |
| 3 | Points amont à discuter en réunion : tā' marbūṭa, langue par segment, arabe standard / tunisien | E7 : 2 (+ effets sur les sujets) | moyen | dépend du Lot A2 |
| 4 | Repli sur les règles quand l'arbre est incohérent (pas de racine verbale) ; négation « ما » forcée | E2 : 6 | moyen | moyen |
| 5 | Segmentation des clitiques dialectaux (ما…ش) | E1 : 2 | faible à moyen | faible |
| 6 | Sujet verbe-sujet-objet étendu à l'annexion pour la coréférence | E6 : 1 | faible | faible |

À compléter au palier Silver : un jeu plus grand (environ 100 phrases), en partie tiré d'articles réels,
avec une double annotation.
