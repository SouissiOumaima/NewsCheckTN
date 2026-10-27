# Carte de données — corpus utilisés par le Lot A2

Les données du projet (preuves, affirmations, annotations des verdicts) relèvent du Lot A1. Les jeux
ci-dessous servent uniquement à construire et à mesurer la normalisation et l'identification de
langue. Aucun n'est versionné : ils sont dans `data/raw/langid/` et `data/interim/langid/`, et chacun
les télécharge selon `normalization/README.md`.

## 1. Corpus publics

| Jeu | Contenu | Licence | Usage dans le Lot A2 |
| --- | --- | --- | --- |
| TSAC | commentaires Facebook tunisiens, lettres arabes et latines | LGPL-3.0 | lexique tunisien (EXP-A2-002, 004), échantillons annotés, exemples d'arabizi à chiffres |
| Tunizi | commentaires tunisiens en arabizi | CC BY 4.0 | exemples d'arabizi pour le modèle (EXP-A2-003) |
| UD French-GSD | phrases françaises (train, dev, test) | CC BY-SA 4.0 | exemples français (train), choix du seuil (dev), test consulté une fois (416 phrases) |
| UD Arabic-PADT | presse en arabe standard | voir la licence du dépôt UD | lexique (marques absentes de train), contrôle des fausses alertes (dev + test, 1 589 phrases) |

## 2. Jeux construits par le Lot A2

| Jeu | Construction | Taille | Statut |
| --- | --- | --- | --- |
| Échantillon TSAC en lettres arabes | tirage graine 13, 3 mots ou plus, sans doublon (`annotation sample arabic`) | 100 | annoté (`t` / `a` / `x`), double annotation, kappa 0,65, référence après adjudication |
| Échantillon TSAC en lettres latines | même tirage, sans chiffre d'arabizi (`annotation sample latin`) | 100 | annoté (`t` / `f` / `x`), double annotation, kappa 0,84, référence après adjudication |

Guide : `docs/lot-a2_guide_annotation.md`. Tirages vérifiables : `python -m normalization.annotation sample arabic --check`.

## 3. Jeu partagé

`tests/fixtures/linguistic_analysis/eval_30.jsonl` (Lot B) : 34 phrases rédigées (10 FR, 10 AR, 14 TN), étiquettes `lang` et `script` ; jeu de développement commun aux lots A2 et B.

## 4. Limites et précautions

- Bruit d'étiquette : Tunizi contient des commentaires en français ; UD French-GSD dev contient au moins une phrase anglaise.
- Contenu : commentaires publics, parfois injurieux ; ils peuvent citer des personnes. Ils ne sont ni redistribués ni versionnés, et le journal ne cite pas d'insultes.
- Représentativité : commentaires de réseaux sociaux (TSAC, Tunizi) et presse (PADT, GSD) ; les affirmations du projet (Lot A1) n'ont pas encore été mesurées.
