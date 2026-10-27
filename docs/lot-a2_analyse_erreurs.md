# Lot A2 — Analyse d'erreurs de l'identification de langue

45 erreurs catégorisées sur les deux échantillons annotés de TSAC, étiquettes de référence après
adjudication (EXP-A2-009). Les textes ne sont pas versionnés (`data/interim/langid/`) : les lignes sont
désignées par leur numéro et par le ou les mots en cause.

## Résultats

| Échantillon | Classe | Bien classés | Erreurs |
| --- | --- | --- | --- |
| Lettres arabes (100 textes) | `a` (arabe standard) | 23 sur 23 | 0 |
| Lettres arabes | `t` (tunisien) | 41 sur 77 | 36 |
| Lettres latines (86 textes, `x` exclus) | `f` (français) | 12 sur 16 | 4 |
| Lettres latines | `t` (tunisien) | 65 sur 70 | 5 |

Toutes les erreurs en lettres arabes vont dans le même sens : du tunisien pris pour de l'arabe
standard. La règle est prudente (aucune presse classée tunisienne) au prix du rappel.

## Catégories

| Catégorie | Description | Erreurs | Piste |
| --- | --- | --- | --- |
| A1 | Mot ou forme tunisienne absente du lexique | 7 | Agrandir le lexique (candidats d'EXP-A2-004 au-delà des 78 retenus) |
| A2 | Négation contractée sans « ما » séparé (مـ…ش، …وش، معاش) | 4 | Élargir la règle de négation, en mesurant les fausses alertes sur la presse |
| A3 | Marque avec un préfixe ou un suffixe collé (ي، ال، هال، ـك، ـو) | 5 | Retirer les affixes courants avant la comparaison au lexique |
| A4 | Variante orthographique d'une marque (ص / س, espace, hamza, ا en tête) | 6 | Ajouter les variantes au lexique ou comparer après pliage |
| A5 | Marque absente du lexique par choix (ياسر prénom ; الي souvent pour إلى) | 3 | Compromis assumé : 0 fausse alerte sur la presse (EXP-A2-004) |
| A6 | Indice de construction, pas de mot (ordre des mots, « تحب + verbe ») | 2 | Hors de portée d'une règle à mots : modèle appris (Silver) |
| A7 | Texte très court, presque sans mot dialectal | 4 | Limite assumée |
| A8 | Étiquette discutable ou remise en question après coup | 5 | À revoir avec la seconde annotatrice |
| L1 | « bravo + nom » étiqueté `f` : le nom tunisien pousse le modèle vers `tn` | 4 | Règle du guide fragile : compter ces lignes à part |
| L2 | Texte de 1 à 3 mots, ou score sous le seuil prudent (5.0) | 5 | Prix assumé du seuil : 0 français classé arabizi |

21 des 36 erreurs en lettres arabes (A1 à A4) relèvent de causes réparables par des règles ;
A6 demande un modèle appris ; A5 et A7 sont des limites assumées ; A8 relève de l'annotation.

## Détail ligne par ligne

| Échantillon | Ligne | Catégorie | Mot(s) en cause |
| --- | --- | --- | --- |
| arabe | 1 | A2 | معجبكش |
| arabe | 5 | A3 | يراهم |
| arabe | 6 | A6 | الانسان هذا |
| arabe | 10 | A8 | حلو |
| arabe | 13 | A3 | نقولك ، آني |
| arabe | 14 | A1 | نتفرج ، توحشتك |
| arabe | 22 | A1 | كان ، لحاصيلو |
| arabe | 23 | A2 | تاخذوش |
| arabe | 25 | A4 | ما صط |
| arabe | 26 | A7 | 2 mots |
| arabe | 27 | A2 | محقهمش |
| arabe | 29 | A4 | ماصط |
| arabe | 30 | A4 | يعتك |
| arabe | 33 | A8 | حلوة |
| arabe | 38 | A5 | ياسر |
| arabe | 40 | A1 | تصوروا |
| arabe | 43 | A3 | كلو |
| arabe | 49 | A6 | ما خيب |
| arabe | 55 | A1 | حسيتها |
| arabe | 56 | A4 | إلي |
| arabe | 57 | A7 | nom + expression |
| arabe | 59 | A5 | ياسر |
| arabe | 60 | A1 | لقيت |
| arabe | 64 | A7 | 3 mots |
| arabe | 67 | A3 | يتفرجو |
| arabe | 68 | A7 | 4 mots |
| arabe | 69 | A4 | إلي ، ونتي |
| arabe | 73 | A1 | بالرسمي |
| arabe | 74 | A8 | étiquette remise en question |
| arabe | 75 | A3 | المساطة |
| arabe | 82 | A8 | étiquette remise en question |
| arabe | 86 | A8 | معاه en fin de phrase |
| arabe | 87 | A1 | تفدد |
| arabe | 90 | A5 | الي |
| arabe | 92 | A4 | انحب انقول |
| arabe | 94 | A2 | معاش ، هالمارك |
| latin | 4 | L1 | tounsi |
| latin | 27 | L2 | 1 mot |
| latin | 41 | L2 | 3 mots |
| latin | 67 | L1 | tounsi |
| latin | 70 | L1 | Elgharbi |
| latin | 84 | L2 | 3 mots |
| latin | 85 | L2 | 2 mots |
| latin | 90 | L1 | Meherziya |
| latin | 91 | L2 | 3 mots |

Reproduire : `python -m normalization.evaluate data/interim/langid/tsac_arabic_sample_reference.tsv --errors`
(même commande pour `tsac_latin_sample_reference.tsv`).
