# Lot E — Intégration Silver C / D

## Périmètre

Les composants des PR #21 et #25 sont fusionnés dans main. Cette branche
reprend uniquement les changements du Lot E au-dessus de ces composants. Aucune mesure sur le test
scientifique n'est relancée par ce travail d'intégration.

## Sélection explicite

- `VERDICT_BACKEND=gabarit` : défaut, même verdict classique qu'avant.
- `VERDICT_BACKEND=llm` : appelle llm_verdict du Lot D ; son Verdict conserve
  le schéma partagé. Le moteur local est réutilisé entre requêtes.
- `RETRIEVAL_METHOD=hybrid`, `EMBEDDING_MODEL=intfloat/multilingual-e5-base`
  activent la recherche hybride ; dépendance sentence-transformers.
- `NLI_BACKEND=fine-tuned` active le checkpoint de PR #21, à installer localement
  dans models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed42/.
- `LLM_PROVIDER=hf`, `LLM_MODEL=CohereLabs/aya-expanse-8b` : modèle officiel
  EXP-D-010, à exécuter sur une machine GPU compatible avec les dépendances du
  notebook Lot D et avec l'accès au modèle accordé. Ne pas lancer le 8B sur CPU
  sans vérifier les ressources. La configuration seule ne prouve pas son chargement.

Les variables doivent être exportées dans le processus qui lance l'API ;
ce projet ne charge pas automatiquement un fichier .env.

## Confidentialité

Le message sollicitant l'accord de l'équipe sur Gemini ne vaut pas accord.
Le défaut `LLM_ALLOW_EXTERNAL=0` interdit la construction d'un générateur distant
pour openai/ollama, même si une clé est définie. Seules les adresses loopback
localhost, 127.0.0.1 ou ::1 sont traitées comme locales. Une instance distante
requiert `LLM_ALLOW_EXTERNAL=1`, à définir uniquement après autorisation de l'équipe.
Aucune API externe n'est appelée pendant les tests d'intégration.
L'exécution sur Colab implique un hébergement cloud : elle ne doit pas être décrite
comme conservant les fichiers exclusivement sur le poste de l'équipe.

## Routes et observabilité

`/check` et `/verdict` gardent leur contrat historique et utilisent le même sélecteur.
`/verdict/detail` expose verdict_engine et nli_engine en plus des preuves.
`/check/detail` appelle pipeline.check_text_detail et expose input, normalized
(texte, langue et écriture du document réellement utilisé), candidats, affirmations retenues,
preuves/positions, verdict,
moteurs et timings_ms. L'accueil utilise cette trace ; la page Lot D montre le
moteur demandé, le moteur utilisé et la raison d'un repli.
Le client ne peut pas autoriser une API distante via le corps de sa requête.

Aucune preuve : pas d'appel LLM, abstention. Sortie invalide : gabarit du Lot D.
Échec d'initialisation ou de génération : gabarit et llm_unavailable, sans révéler
l'erreur fournisseur, les clés ni la réponse brute. API distante non autorisée :
gabarit et external_provider_not_authorized. Ces raisons sont visibles dans la
trace ; elles ne doivent pas être comptées comme des résultats du modèle LLM.
L'incertitude fixe du LLM du Lot D n'est pas une probabilité calibrée.
Une citation autorisée n'atteste pas à elle seule du support sémantique.

## Validation

Tests avec générateur fictif : succès, citation hors liste, verdict sans citation,
JSON absent, panne, absence de preuve, refus d'une API externe, cohérence des routes.
La vérification du vrai NLI est séparée ; les tests n'exécutent pas Aya 8B ni e5-base.
Le verdict LLM et le retrieval hybride réels nécessitent encore leurs ressources
sur la machine de démo. Comparaison Gemini EXP-D-009 distincte d'Aya officiel
EXP-D-010 ; aucun nouveau score scientifique n'est déduit de ces tests.


## Relecture Lot D

Les champs input/normalized et le helper _claims_from_doc sont repris de la
proposition lot-e-demo, sans importer sa seconde déclaration de /check/detail.
Une seule route et une seule normalisation sont exécutées par requête détaillée.
Une citation hors des preuves retrouvées, détectée au dernier contrôle Lot E,
produit citation_hors_liste, distinct de llm_unavailable.
