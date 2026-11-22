# Lot D — Guide d'annotation des verdicts (Gold)

**Pour : les annotatrices du protocole Gold du Lot D (`docs/lot-d_protocole_gold.md`) · Version 1 · 2026-11-22**

Durée : environ 3 minutes par verdict. **Sans outil d'IA**, et sans regarder les étiquettes de
l'autre annotatrice.

## Ce que vous recevez

Un fichier `annotation_<prénom>.csv` (envoyé en privé, jamais sur GitHub). Une ligne par verdict :

| Colonne | Contenu |
|---------|---------|
| `claim_id` | identifiant de l'affirmation |
| `affirmation` | le texte à vérifier |
| `verdict` | ce qu'a répondu le système : `vrai`, `faux`, `trompeur` ou `preuves_insuffisantes` |
| `explication` | la phrase d'explication du système |
| `citations` | les passages cités (P1…P5) |
| `P1` … `P5` | le texte de chaque passage proposé au système |

Vous remplissez les colonnes vides : `pertinence_P1` … `pertinence_P5` (seulement pour les passages
**cités**), `invente`, `fidelite`, et éventuellement `commentaire`.

## Les 3 questions

### 1. `pertinence_Px` — pour chaque passage cité

> Le passage parle-t-il **du même fait** que l'affirmation ?

- `pertinent` : même sujet **et** même fait (même chiffre, même événement, même personne, même
  période). Il peut confirmer **ou** contredire l'affirmation : ce qui compte, c'est qu'il en parle.
- `non_pertinent` : autre sujet, ou même thème général mais un autre fait.

### 2. `invente` — pour le verdict

> L'explication affirme-t-elle un fait qui n'est dans **aucun** des passages cités ?

- `oui` : au moins un chiffre, un nom, une date ou un fait absent des passages cités.
- `non` : tout ce que dit l'explication vient des passages cités (une reformulation est permise).

### 3. `fidelite` — pour le verdict

> Chaque phrase de l'explication est-elle **soutenue** par un passage cité, et la conclusion
> (`vrai`, `faux`…) découle-t-elle de ces passages ?

- `fidele` : oui pour toutes les phrases et pour la conclusion.
- `infidele` : au moins un point non soutenu, ou une conclusion que les passages ne permettent pas.

Un verdict `preuves_insuffisantes` sans citation : `invente` = `non` ; `fidelite` = `fidele` si
l'explication dit seulement que les passages ne suffisent pas.

**On ne juge pas** si le verdict est juste dans le monde réel, seulement s'il est fondé sur les
passages cités. Ne cherchez rien sur internet.

## Exemples (données fictives du dev)

**Exemple A**
- Affirmation : « Le chômage en Tunisie a atteint 25 % en 2025. »
- Verdict : `faux` · Citations : P1
- P1 : « Selon l'Institut national de la statistique, le taux de chômage en Tunisie s'est établi à 16 % au deuxième trimestre 2025. »
- Explication : « Selon l'INS, le chômage était de 16 % au deuxième trimestre 2025, pas 25 %. »
- → `pertinence_P1` = `pertinent` · `invente` = `non` · `fidelite` = `fidele`

**Exemple B**
- Affirmation : « Le prix du café a augmenté de 40 % cette année. »
- Verdict : `faux` · Citations : P1
- P1 : « Le prix de la baguette subventionnée reste fixé à 190 millimes. »
- Explication : « Le prix est resté stable selon les autorités. »
- → `pertinence_P1` = `non_pertinent` (le pain, pas le café) · `invente` = `oui` (« les autorités »,
  « stable » pour le café : absent du passage) · `fidelite` = `infidele`

**Exemple C**
- Affirmation : « Les barrages sont remplis à 80 %. »
- Verdict : `faux` · Citations : P1, P3
- P1 : « Le taux de remplissage des barrages a atteint 35 % de leur capacité totale au mois de mars 2025. »
- P3 : « Le nombre de touristes arrivés en Tunisie a dépassé 9 millions en 2024. »
- Explication : « Les barrages étaient remplis à 35 % en mars 2025. »
- → `pertinence_P1` = `pertinent` · `pertinence_P3` = `non_pertinent` · `invente` = `non` · `fidelite` = `fidele`

## En cas de doute

Choisissez l'étiquette la plus prudente (`non_pertinent`, `oui` pour `invente`, `infidele`) et
écrivez la raison dans `commentaire`. Les désaccords sont discutés **après** le calcul de l'accord,
sans modifier les étiquettes déjà rendues.
