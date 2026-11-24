# Intégration et audit du Lot E pour le Gold

**Auteur :** Achref Chabene — Lot E et contribution Model 1.
**Point de situation :** 24 novembre 2026.
**Statut :** section de rapport préparée ; intégration finale et répétition commune encore à valider.

## Contribution et périmètre

Mon rôle est de relier les composants à une application traçable et de vérifier leur fonctionnement ensemble. La contribution Gold consolide l'observabilité, la configuration locale Falcon, la distinction entre verdict correct et explication fidèle, ainsi que la traçabilité des versions et des replis. Elle ne constitue pas une nouvelle campagne d'entraînement ou de mesure des modèles.

Le parcours passe par la normalisation et l'identification de langue du Lot A2, l'extraction du Lot B, le filtre Model 1, la recherche hybride du Lot D et le NLI du Lot C. Le verdict est produit par Falcon ou par un gabarit de repli. L'API expose les étapes et l'interface rend visibles les moteurs réellement utilisés, les temps de traitement, les citations et les raisons d'un repli.

## Architecture et contrats

| Composant | Configuration retenue pour la préparation Gold | Contrôle attendu |
|---|---|---|
| Model 1 | XLM-R et LoRA, checkpoint seed 42 | Moteur chargé ; candidats et phrases retenues visibles |
| Recherche | BM25 et multilingual-e5-base, fusion hybride | Corpus local identifié ; passages retrouvés et leurs identifiants |
| NLI | mDeBERTa affiné, EXP-C-011 seed 42 | Backend fine-tuned réellement chargé ; positions supports, refutes, neutral |
| Verdict | Falcon-H1-3B GGUF Q4 via Ollama, JSON imposé | verdict_engine.used = llm ; modèle annoncé ; absence ou raison de repli |
| Repli | Gabarit du Lot D | Repli affiché, sans le compter comme une réponse de Falcon |

`POST /check/detail` fournit le texte normalisé, la langue, l'écriture, le nombre de candidats et de phrases retenues, puis les preuves, positions, verdicts, moteurs et temps par étape. `POST /verdict/detail` permet d'examiner une affirmation sans repasser par le filtre Model 1. Les contrats des routes historiques et le schéma `Verdict` restent conservés.

La PR #39 précharge le NLI au démarrage et ajoute son état dans `/health`. Le coût de chargement est déplacé avant la première requête ; aucun gain de vitesse chiffré sur modèle réel n'est revendiqué. La PR #41 affiche le modèle du verdict et remplace la valeur fixe d'incertitude du LLM par « incertitude non calibrée ». Le gabarit conserve son indice avec la même réserve de calibration.

## Configuration et versions scientifiques

Falcon-H1-3B avec JSON est le modèle officiel actuel annoncé par le Lot D. Aya Expanse 8B reste un résultat historique d'EXP-D-010. Le score Falcon d'EXP-D-015 provient d'un second passage sur le test v1 et reste déclaré optimiste.

Les expériences Falcon EXP-D-014/015 utilisent le NLI Bronze. Le NLI affiné seed 42 est confirmé par Hadil pour le Gold et déclaré dans EXP-D-018. Les deux configurations ne sont pas interchangeables : la présence du checkpoint affiné dans une démo n'attribue pas rétroactivement les scores historiques à ce moteur.

Le mode JSON de Falcon dépend de la PR #33. Définir `LLM_RESPONSE_FORMAT=json` sur une ancienne version qui ignore cette option ne reproduit pas l'expérience. La PR #41 reste donc en brouillon tant que ses dépendances et ses relectures ne sont pas terminées. La PR #39 peut être revue indépendamment.

## Vérifications techniques et portée des tests

| Livrable | Preuve disponible | Limite de la vérification |
|---|---|---|
| API NLI #39, f1c28db | 15 tests API ; suite hors slow : 695 réussis, 77 désélectionnés, 6 échecs attendus ; Ruff et CI OK | Pas de mesure GPU ni de benchmark de latence réelle |
| Affichage Falcon #41, 4c07584 | 26 tests API et sélecteur ; contrôles JavaScript du rendu, des replis et de l'échappement ; Ruff et CI OK | Modèles réels non exécutés dans cette vérification |
| Gold NLI #34, b8483d0 | Bug de changement de moteur identifié puis corrigé ; deux tests de non-régression ; PR fusionnée | EXP-C-012/013 restent hors évaluation |
| Livraisons des autres lots | Reviews de code et contrôles ciblés documentés dans les PR | Une review ne certifie pas une expérience privée non reproduite |

Ces nombres sont rattachés à des branches et commits précis. Ils ne sont pas additionnés et ne décrivent pas le total de tests du futur `main`. Les tests avec générateurs fictifs vérifient les contrats, les refus et les replis ; ils ne prouvent ni la qualité des preuves ni la fidélité d'un modèle réel.

Les contrôles d'intégration vérifient notamment les sorties JSON invalides, les citations hors liste, les verdicts sans citation, les pannes et l'absence de preuves. Un appel à un fournisseur distant est bloqué par défaut. Le service Ollama de la démo reste sur loopback ; aucun endpoint distant n'est nécessaire à la configuration retenue.

## Audit du verdict et résultats du Lot D

Les résultats suivants sont attribués au Lot D. Ils proviennent du journal de la branche `lot-d-gold`, commit `24bc73b`, et non d'une mesure exécutée par le Lot E.

| Expérience | Résultat rapporté | Conséquence pour l'intégration |
|---|---|---|
| EXP-D-016, audit humain du test v1 | 17 verdicts justes sur 21 ; 8 justes et fidèles ; 29 passages cités pertinents sur 39 | Séparer exactitude, fidélité et pertinence ; ne pas réduire l'audit au bon label |
| EXP-D-017, juge Qwen local | Juge non validé ; les analyses d'accord et leurs limites sont conservées dans le journal | Ne pas automatiser l'approbation des verdicts avec ce juge |
| EXP-D-018, règle d'abstention sur dev | Règle non adoptée ; absence d'amélioration selon le critère fixé | Ne pas brancher cette règle comme une amélioration Gold validée |

EXP-D-016 est un audit descriptif d'exécutions déjà enregistrées sur un ancien test. Il ne constitue pas une nouvelle mesure indépendante sur un jeu jamais vu. Les 39 passages sont des occurrences de citations, pas la taille du corpus de preuves. Une citation appartenant à la liste autorisée peut rester hors sujet ; une bonne réponse ne garantit pas une justification fidèle.

Une seconde annotation indépendante de verdicts a été demandée à Achref, avec un outil HTML local et un guide. Les décisions doivent être prises sans IA ni accès aux annotations de Hadil. Ce rapport ne présente aucun coefficient d'accord attribué à Achref tant que la réception et la comparaison de son fichier ne sont pas établies.

## Contribution Model 1 et limites de provenance

Les prédictions des seeds 42, 123 et 2026 ont été exportées pour la comparaison avec le Lot B, avec le split `claim_detection_multiclass_600_seed42` et les empreintes. Le sous-ensemble P061–P600 du test contient 112 textes : 23 FR, 29 AR, 60 TN. Il ne forme pas un jeu de 112 textes tunisiens.

Les 540 textes P061–P600 sont synthétiques, générés avec ChatGPT puis annotés par Achref. Les consignes, dates et version exacte non retrouvées restent non documentées. Aucun lien non établi avec les identifiants du corpus A1 TArC/TuniFact n'est revendiqué. Ces exports ne sont pas une nouvelle mesure d'apprentissage Gold.

## Confidentialité et limites scientifiques

Les corpus, traces et annotations restent hors des ajouts de cette contribution ; les démonstrations ne doivent pas servir à republier des passages privés. L'exposition signalée sur des branches historiques doit être traitée collectivement et ne peut pas être considérée résolue par une simple mise à jour documentaire.

Les réécritures NLI EXP-C-012/013 restent suspendues jusqu'à la décision avec l'encadrante. Leurs protocoles ne sont pas présentés comme des résultats mesurés. Les arbitrages A1 ouverts et la traçabilité des annotations initiales restent distincts d'une approbation technique de PR.

Le système peut encore filtrer à tort une phrase en arabizi, produire un verdict avec des citations peu pertinentes, ou échouer à s'abstenir. Les scores et comparaisons par langue doivent être accompagnés de leurs effectifs. L'incertitude affichée n'est pas une probabilité calibrée.

## Conditions de finalisation

1. Résoudre les conflits et terminer les revues de #32/#33, puis actualiser et relire #41 ; terminer la revue de #39.
2. Répéter le parcours complet sur le PC de Hadil avec le code retenu, et consigner commit, modèles, corpus, latences à froid/à chaud et replis.
3. Documenter la seconde annotation et sa comparaison sans inventer de validation ou d'indépendance.
4. Consolider le tableau de bord, les résultats et les réserves avec les responsables de lots, sans relancer un test gelé pour régler le système.

La contribution d'intégration est développée et ses changements sont publiés. La clôture Gold de bout en bout reste conditionnée à ces validations. Le scénario de présentation est décrit dans `docs/lot-e_demo_gold_75s.md`.

## Références

- [PR #39 API NLI](https://github.com/SouissiOumaima/NewsCheckTN/pull/39)
- [PR #41 interface et configuration Falcon](https://github.com/SouissiOumaima/NewsCheckTN/pull/41)
- [Journal Gold Lot D au commit 24bc73b](https://github.com/SouissiOumaima/NewsCheckTN/blob/24bc73b/experiments.md) : EXP-D-016, EXP-D-017, EXP-D-018.
- [Journal NLI Gold](https://github.com/SouissiOumaima/NewsCheckTN/pull/34) : EXP-C-012 à EXP-C-016.
