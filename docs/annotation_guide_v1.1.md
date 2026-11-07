
# NewsCheck TN — Guide d'annotation
## Lot A1 — Classification des énoncés

**Version :** 1.1 (proposition Bronze — 07/11/2026)
**Statut :** Proposition révisée — en attente de validation par l'équipe
**Langues :** Français, arabe standard, tunisien et Arabizi

---

## 1. Objectif

Ce guide définit les règles d'annotation des phrases du corpus
multilingue NewsCheck TN.

Chaque phrase doit être classée dans une seule catégorie :

- AFFIRMATION
- OPINION
- AUTRE

L'objectif est de distinguer les affirmations potentiellement
vérifiables des jugements subjectifs et des autres énoncés.

IMPORTANT :
La classification ne détermine jamais si une information est vraie
ou fausse.

## 2. Catégories d'annotation

### 2.1 AFFIRMATION

Une AFFIRMATION présente une information factuelle qui pourrait,
en principe, être vérifiée à partir de preuves ou de sources.

Exemples :

- FR : Le taux de chômage a augmenté en 2025.
- AR : ارتفعت نسبة البطالة في تونس سنة 2025.
- Arabizi : El batala zadet fi Tounes fi 2025.

Ces exemples sont fictifs et ne constituent pas des faits vérifiés.

Règles :
- Les statistiques et les dates sont généralement des affirmations.
- Une information rapportée peut être une affirmation.
- Une rumeur peut contenir une affirmation, même si elle est fausse.
- Une affirmation négative reste une affirmation.
- Une prédiction mesurable peut être annotée AFFIRMATION,
  avec une note sur sa vérifiabilité future.

### 2.2 OPINION

Une OPINION exprime une appréciation, un jugement de valeur,
une préférence ou une évaluation subjective.

Exemples :

- FR : Je trouve que ce service est excellent.
- AR : أعتقد أن هذا القرار غير مناسب.
- Arabizi : Ena nchouf el 9arar hedha ghalet.

Règles :
- Les préférences personnelles sont des opinions.
- Les jugements de valeur sans critère vérifiable sont des opinions.
- Une critique subjective reste une opinion.
- La présence de "je pense" ne suffit pas à classer OPINION
  si la proposition porte sur un fait vérifiable.

### 2.3 AUTRE

La catégorie AUTRE comprend les énoncés qui ne présentent
ni affirmation factuelle identifiable ni opinion explicite.

Exemples :

- FR : Bonjour à tous !
- AR : متى تبدأ الامتحانات؟
- Arabizi : Chnowa wa9t el examen ?

Règles :
- Les salutations sont AUTRE.
- Les questions neutres sont AUTRE.
- Les instructions simples sont AUTRE.
- Les fragments incomplets sans proposition identifiable sont AUTRE.

## 3. Règles de décision

### Règle 1 — Identifier la proposition principale

Lire la phrase entière et identifier son intention dominante.

### Règle 2 — Distinguer vérifiabilité et vérité

Une affirmation peut être vraie, fausse ou non vérifiée.

Exemple :
"Le ministère a publié un communiqué."

Annotation : AFFIRMATION.

Cette annotation ne confirme pas l'existence du communiqué.

### Règle 3 — Informations rapportées

Exemple :
"Un journal affirme que 10 000 personnes ont quitté le pays."

Annotation : AFFIRMATION.

La phrase affirme qu'un journal a publié une information.
Elle ne prouve pas que les 10 000 départs ont eu lieu.

### Règle 4 — Phrases mixtes

Si une phrase contient un fait et une opinion :

- Identifier la proposition dominante.
- Si plusieurs propositions sont indépendantes et de types
  différents, marquer le cas pour révision.
- Ne pas supprimer ni modifier le texte original.

### Règle 5 — Questions rhétoriques

Une question neutre est AUTRE.

Une question rhétorique exprimant clairement un jugement
peut être OPINION.

Si l'intention est ambiguë, demander une seconde annotation.

### Règle 6 — Langues et écritures

Annoter le sens de la phrase, indépendamment de sa langue.

Groupes linguistiques autorisés :

- fr-latin : français en alphabet latin
- ar-arabic : arabe standard en alphabet arabe
- tn-arabic : tunisien en alphabet arabe
- tn-arabizi : tunisien en caractères latins et chiffres
- tn-mixed : mélange linguistique ou graphique tunisien

Exemples de chiffres Arabizi :
- 3 peut représenter ع
- 7 peut représenter ح
- 9 peut représenter ق

Ces conventions varient selon les personnes et les contextes.

## 4. Processus d'annotation

Pour chaque phrase :

1. Lire le texte complet.
2. Identifier la langue et le groupe linguistique.
3. Déterminer si la phrase présente un fait vérifiable.
4. Sinon, déterminer si elle exprime une opinion.
5. Sinon, utiliser AUTRE.
6. Conserver la source et l'identifiant.
7. Documenter les cas ambigus.

Ne pas modifier silencieusement les phrases originales.

## 5. Format JSONL

Chaque ligne du fichier représente un objet JSON indépendant.

Exemple :

{
  "id": "exemple-001",
  "doc_id": "exemple",
  "text": "Le ministère a publié un communiqué.",
  "lang": "fr",
  "script": "latin",
  "source": "exemple fictif",
  "url": null,
  "date": null,
  "groupe_linguistique": "fr-latin",
  "decision": "CONSERVER",
  "raison": "Énoncé factuel potentiellement vérifiable",
  "annotation": "AFFIRMATION"
}

Les champs requis pour le contrôle du pilote sont :
- id
- text
- source
- groupe_linguistique
- decision
- annotation

Les autres métadonnées doivent être conservées lorsqu'elles
sont disponibles.

## 6. Critères de qualité

Avant de valider un corpus :

- Vérifier que les lignes sont des JSON valides.
- Vérifier que les identifiants sont uniques.
- Vérifier les annotations autorisées.
- Vérifier les groupes linguistiques.
- Vérifier que les textes ne sont pas vides.
- Vérifier la traçabilité des sources.
- Examiner manuellement les cas ambigus.

La validation automatique ne garantit pas la qualité
sémantique des annotations.

## 7. Corpus pilote

### TArC

30 phrases :
- 18 AFFIRMATION
- 7 OPINION
- 5 AUTRE

### Tunifact

30 phrases :
- 30 AFFIRMATION
- 0 OPINION
- 0 AUTRE

### Total

60 phrases :
- 48 AFFIRMATION
- 7 OPINION
- 5 AUTRE

Ce pilote est déséquilibré en faveur des affirmations.

La collecte suivante devra renforcer la diversité des
catégories, des sujets, des sources et des groupes linguistiques.

## 8. Traçabilité et reformulations

Le corpus contient deux types de textes :

1. Des extraits conservés depuis les sources.
2. Des phrases reformulées pour l'exercice de classification.

Ces types doivent rester distinguables.

Pour toute nouvelle collecte, utiliser un champ supplémentaire :

- text_origin : "original" ou "reformulation"

Les phrases reformulées ne doivent jamais être présentées
comme des citations exactes.

Conserver les liens vers les articles d'origine.

Les droits de réutilisation et les licences des sources doivent
être vérifiés avant toute redistribution du corpus.

## 9. Limites du pilote

- Seulement 60 phrases.
- Forte proportion d'AFFIRMATION.
- Sources et thèmes encore limités.
- Présence de reformulations.
- Absence de double annotation indépendante systématique dans le pilote historique de 60 phrases. Une double annotation de 100 phrases a ensuite été réalisée.
- Dates manquantes dans certaines métadonnées.

Le pilote valide principalement le processus technique
et constitue une base pour améliorer la méthode d'annotation.

## 10. Prochaines étapes

- Faire relire le guide par l'équipe.
- Réviser les exemples ambigus.
- Préparer une Data Card.
- Étendre progressivement le corpus vers 600 phrases.
- Construire 300 paires NLI.
- Réaliser une validation humaine de qualité.
- Documenter les licences et les conditions de diffusion.

---

## 11. Protocole de double annotation — palier Bronze (ajout v1.1)

**Objectif :** comparer, pour les mêmes 100 identifiants, deux annotations
réalisées indépendamment par Ghofran et Achref selon les trois labels définis
dans la section 2.

1. Figer la liste des 100 identifiants et la version des textes avant comparaison.
2. Vérifier que chaque fichier contient exactement un enregistrement par identifiant,
   sans texte vide et avec un label autorisé.
3. Joindre les fichiers par `id` et vérifier que les textes correspondent ;
   ne jamais aligner simplement par numéro de ligne.
4. Conserver les annotations initiales séparées et ne pas les modifier
   après découverte des désaccords.
5. Produire un tableau des accords et désaccords, une matrice de confusion
   et le calcul de Cohen's Kappa.
6. Examiner les désaccords en réunion, documenter leur justification et
   produire un label arbitré dans une colonne distincte.
7. Archiver les versions originales, la comparaison et le compte rendu d'arbitrage.

**Colonnes recommandées pour la comparaison :**
`id`, `text`, `annotation_ghofran`, `annotation_achref`, `accord`,
`annotation_arbitree`, `motif_arbitrage`.

**Important :** la double annotation des 100 exemples est une tâche
à vérifier sur les deux fichiers réels ; elle n'est pas attestée par le
présent guide.

## 12. Mesure d'accord — Cohen's Kappa (ajout v1.1)

Pour les 100 exemples communs et correctement alignés :

- Accord observé : `Po = nombre d'accords / N`.
- Accord attendu par hasard à partir des marges :
  `Pe = somme, pour chaque label, de (proportion Ghofran × proportion Achref)`.
- `Kappa = (Po - Pe) / (1 - Pe)` si `Pe != 1`.

Publier **N**, le nombre d'accords, le pourcentage d'accord brut, les
distributions de labels de chaque annotateur, la matrice de confusion,
`Po`, `Pe` et `Kappa` (avec au moins trois décimales).

Si `Pe = 1`, le Kappa est indéfini : ne pas le remplacer par 1.
Ne pas calculer le Kappa sur les labels arbitrés ; utiliser les
annotations indépendantes originales.

L'interprétation doit tenir compte du déséquilibre des classes et
des désaccords observés. Aucun seuil d'acceptation Bronze n'est
fixé ici sans accord de l'équipe.

## 13. Cas limites et décisions reproductibles (ajout v1.1)

Les exemples ci-dessous sont **fictifs** et illustrent les règles,
sans établir de vérité factuelle.

| Exemple | Label recommandé | Justification |
| --- | --- | --- |
| « Je pense que le chômage a augmenté en 2025. » | AFFIRMATION | « Je pense » introduit une proposition factuelle potentiellement vérifiable. |
| « Cette décision est injuste. » | OPINION | Jugement de valeur sans critère objectif explicite. |
| « Est-ce que le taux de chômage a augmenté ? » | AUTRE | Question neutre, sans assertion explicite. |
| « Le ministère n'a publié aucun communiqué. » | AFFIRMATION | Proposition négative vérifiable. |
| « Le chômage augmentera de 2 points en 2027. » | AFFIRMATION | Prédiction quantifiable, à vérifier ultérieurement ; noter la temporalité. |
| « Quelle décision catastrophique ! » | OPINION | Évaluation subjective explicite. |
| « Le taux a augmenté et cette hausse est scandaleuse. » | À réviser | Fait et opinion indépendants ; conserver le texte et documenter l'arbitrage. |
| « El batala zadet fi Tounes. » | AFFIRMATION | Proposition factuelle en Arabizi ; la langue ne change pas la règle. |

**Précision :** une information attribuée à une source peut être annotée
AFFIRMATION parce que l'attribution est vérifiable ; cela ne valide
pas automatiquement le contenu rapporté. Une phrase ambiguë doit être
signalée pour révision, sans inventer un quatrième label final.

## 14. Format, traçabilité et contrôles Bronze (ajout v1.1)

Pour chaque exemple final, les champs requis de la section 5 restent :
`id`, `text`, `source`, `groupe_linguistique`, `decision`, `annotation`.

Pour toute **nouvelle** collecte ou reformulation, documenter aussi :
`text_origin` (`original` ou `reformulation`), `doc_id` et, si disponibles,
`url`, `date`, `lang`, `script`. Les valeurs absentes doivent être
explicites ou documentées ; ne pas fabriquer de métadonnées.

Vérifications minimales du corpus de 600 phrases :
- exactement 600 lignes JSONL si tel est le livrable final convenu ;
- identifiants uniques, champs requis présents et textes non vides ;
- labels parmi `AFFIRMATION`, `OPINION`, `AUTRE` ;
- groupes linguistiques parmi les cinq codes de la section 3 ;
- répartition par label, langue, source et origine du texte ;
- contrôle des doublons exacts et revue des quasi-doublons ;
- cohérence entre `decision` et les règles d'inclusion du corpus ;
- conservation de la provenance et signalement des licences non vérifiées.

Le nombre de 600 et les répartitions doivent être établis par audit
du fichier final, pas déduits des statistiques du pilote.

## 15. Journal de validation Bronze (ajout v1.1)

| Livrable | État au 07/11/2026 | Preuve à archiver |
| --- | --- | --- |
| Guide d'annotation v1.1 | Proposition rédigée ; approbation en attente | Relecture et accord de l'équipe |
| Double annotation 100 exemples | Réalisée : 69 accords, 31 désaccords | Fichier de comparaison par ID |
| Premier Cohen's Kappa | Calculé : environ 0,34 | Script, matrice, résultats |
| Corpus 600 phrases | À auditer | Rapport de validation JSONL |
| Base de preuves v1 | À auditer | Schéma, provenance, langues, doublons |
| Corpus NLI 300 paires | Contrôle du fichier final à confirmer | Audit de traçabilité et labels |
| Data Card et carte du système | À relire | Versions validées |
| Tunisien / Arabizi | Couverture à mesurer | Statistiques et exemples manquants |
| Livraison Lot C et démo | À préparer | Schémas, splits, scénarios, manifeste |

## 16. Historique des versions

- **v1.0 :** guide pilote initial, avec statistiques historiques sur 60 phrases.
- **v1.1 (proposition initiale du 27/10/2026, révisée le 07/11/2026) :** ajout du protocole de double
  annotation, du calcul de Cohen's Kappa, des cas limites et des
  contrôles Bronze ; aucune validation d'équipe ni résultat statistique
  n'est présumé.
