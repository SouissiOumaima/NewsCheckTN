
# NewsCheck TN — Guide d'annotation
## Lot A1 — Classification des énoncés

**Version :** 1.0 (pilote)
**Statut :** Guide de travail à valider par l'équipe
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
- Absence de double annotation indépendante systématique.
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
