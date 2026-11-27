# Démonstration Gold du Lot E en 75 secondes

**Présentateur :** Achref Chabene. **Préparation :** 24 novembre 2026.
**Statut :** scénario prêt ; répétition complète et enregistrement final à réaliser avec Hadil.

## Objectif et configuration

Montrer le parcours réel de bout en bout et la traçabilité du verdict : texte normalisé, filtre Model 1, preuves, NLI, Falcon, citations et limites. Cette démo n'est pas une mesure scientifique. Elle utilise le PC de Hadil équipé d'Ollama/Falcon ; aucune connexion GPU distante n'est nécessaire.

Préparer la version intégrant #33, les corrections NLI de #39 et l'affichage de #41. Les PR encore ouvertes ne sont pas supposées présentes dans main. Vérifier la configuration réelle plutôt que le nom de la branche. Pour la nouvelle jauge,
intégrer aussi #45 et la transmission Lot E de `uncertainty_source` :
`LLM_UNCERTAINTY_MODE=nli`, `RERANKER=off`. Contrôler que la source vaut `nli`
avant d'annoncer un indicateur calculé. Une ancienne valeur fixe reste masquée.

- Model 1 : `CLAIM_DETECTOR_BACKEND=xlmr`, checkpoint seed 42.
- Recherche : `RETRIEVAL_METHOD=hybrid`, multilingual-e5-base.
- NLI Gold : `NLI_BACKEND=fine-tuned`, checkpoint EXP-C-011 seed 42.
- Verdict : `VERDICT_BACKEND=llm`, `LLM_PROVIDER=ollama`, Falcon-H1-3B GGUF Q4, `LLM_RESPONSE_FORMAT=json`.
- Corpus local autorisé ; `LLM_ALLOW_EXTERNAL=0` ; mode de calcul consigné.
- Juge Qwen et règle d'abstention Gold non activés, car non validés/non adoptés.

Les détails PowerShell sont dans `frontend/README.md`. Une variable seule ne prouve pas que le moteur attendu est chargé.

## Préparation avant de lancer le chronomètre

1. Vérifier Ollama, les checkpoints, le corpus, le cache e5 et le code du mode JSON. Démarrer l'API sur `127.0.0.1:8000` et attendre sa disponibilité.
2. Contrôler `/health` : NLI `fine-tuned`, statut `loaded`, Model 1 chargé. Si #39 n'est pas intégrée, ne pas prétendre que le nouveau champ existe : préparer d'abord la bonne version.
3. Faire une répétition hors présentation pour mesurer le temps réel et détecter un repli. Ne pas ajuster les paramètres avec le test gelé.
4. Conserver en privé la phrase française et la phrase tunisienne autorisées, leur provenance et leurs résultats de répétition. Choisir une phrase retenue par Model 1 ; ne pas promettre un label avant l'essai.
5. Ouvrir l'accueil `/app/` et la page `/app/lot-d.html` dans deux onglets. Agrandir l'affichage pour que le texte et le modèle soient lisibles. Éviter d'afficher le contenu intégral du corpus ou un chemin privé à l'écran.

## Parcours à montrer

| Temps cible | Action à l'écran | Point à expliquer |
|---|---|---|
| 0 à 8 s | Accueil déjà ouvert ; présenter la chaîne | Mon rôle relie les composants et vérifie leur fonctionnement ensemble |
| 8 à 18 s | Saisir la phrase autorisée et lancer Vérifier | Normalisation, langue et filtre Model 1 |
| 18 à 40 s | Pendant le calcul, expliquer les étapes ; montrer le texte normalisé dès qu'il apparaît | Recherche hybride et positions NLI ; ne pas masquer un délai réel |
| 40 à 58 s | Montrer le verdict, le modèle utilisé, les temps et l'éventuel repli | Distinguer Falcon d'un résultat gabarit |
| 58 à 68 s | Dans la page Lot D, montrer un passage cité préparé lors de la répétition | Une référence valide doit aussi être pertinente |
| 68 à 75 s | Conclure sur la limite et les contrôles humains | Incertitude non calibrée ; abstention et juge non validés |

L'accueil affiche le verdict et les identifiants cités ; la page Lot D permet d'examiner le texte des passages. Un résultat préparé dans le second onglet doit être annoncé comme issu de la répétition, sans le faire passer pour une requête qui vient d'être lancée. La page Lot D teste une affirmation directement et ne démontre pas le filtre Model 1.

## Texte à dire en français

Voici NewsCheck TN. Mon rôle est de relier les modèles à l'API et à l'interface, puis de vérifier leur fonctionnement ensemble.

Je saisis une affirmation. Le système normalise le texte, détecte la langue, puis Model 1 garde les phrases à vérifier.

La recherche hybride retrouve des passages. Le NLI affiné indique s'ils soutiennent, contredisent ou ne permettent pas de trancher.

Falcon produit un verdict avec une explication et des citations. Je vérifie ici le modèle réellement utilisé, les passages cités et les éventuels replis.

Les temps de chaque étape sont visibles. L'incertitude du LLM n'est pas calibrée.

Une limite reste importante : un bon verdict peut reposer sur des citations peu pertinentes. Le juge automatique et la nouvelle règle d'abstention ne sont pas validés pour être activés. Nous conservons donc une vérification humaine.

## Si le direct dépasse le temps disponible

Le plafond de 75 secondes inclut les manipulations et le calcul. Si le temps observé lors de la répétition dépasse ce plafond, utiliser une capture Falcon réellement enregistrée sur le PC de Hadil, en annonçant « exécution préenregistrée ». Conserver les latences réelles ; ne pas simuler une nouvelle inférence.

L'ancienne vidéo Silver avec Aya/Colab reste historique et ne doit pas être réétiquetée comme une vidéo Falcon Gold. Aucun nouvel enregistrement Falcon n'est fourni par ce scénario.

## Contrôle avant la revue

- Le moteur affiché correspond au moteur annoncé ; un repli est nommé.
- Aucun chiffre de test n'est déduit des exemples montrés.
- Aucun extrait privé n'est publié sans validation de son usage.
- Les résultats de l'audit sont attribués au Lot D : 17/21 verdicts justes, dont 8 seulement fidèles (8/17), sur le test v1 déjà utilisé (EXP-D-016).
- L'annotation indépendante est réalisée sans IA ; aucun accord humain n'est inventé.
- Les réécritures NLI suspendues ne sont pas utilisées.
