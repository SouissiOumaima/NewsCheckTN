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
- Configuration officielle actuelle du Lot D, annoncée le 22 novembre 2026 :
  Falcon-H1-3B GGUF Q4 avec JSON imposé, servi localement par Ollama (EXP-D-015).
  Voir le lancement et les prérequis dans `frontend/README.md`.
- Aya Expanse 8B (EXP-D-010) reste une référence historique. Son expérience et ses
  chiffres sont conservés ; le changement de modèle officiel ne réécrit aucun résultat.
- Le score de Falcon sur le test v1 provient d'un second passage sur le même jeu :
  il est déclaré optimiste, pas présenté comme un nouveau test jamais vu.

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
L'interface masque sa valeur numérique lorsque le moteur effectivement utilisé
est `llm` et affiche « incertitude non calibrée ». Pour le gabarit, l'indice reste
visible et est également signalé comme non calibré. Le schéma `Verdict` est inchangé.
Une citation autorisée n'atteste pas à elle seule du support sémantique.

## Validation

Tests avec générateur fictif : succès, citation hors liste, verdict sans citation,
JSON absent, panne, absence de preuve, refus d'une API externe, cohérence des routes.
La vérification du vrai NLI est séparée ; les tests n'exécutent aucun LLM ni e5-base.
Le verdict LLM et le retrieval hybride réels nécessitent leurs ressources sur la
machine de démo. Hadil a rapporté un essai complet Falcon sur son PC ; après les
fusions retenues, une répétition commune doit vérifier le commit, les modèles et
les replis. Aucun nouveau score scientifique n'est déduit des tests d'intégration.

## Préparation Gold et dépendances

La PR #32 précède le réalignement de la PR #33, qui apporte notamment
`LLM_RESPONSE_FORMAT=json`. Avant son intégration dans main, la démonstration
Falcon doit utiliser le code de `lot-d-falcon` ou une version qui inclut ces changements.
Définir cette variable sur une version qui l'ignore ne reproduit pas EXP-D-015.

Les runs Falcon EXP-D-014/015 utilisent le NLI Bronze. Hadil confirme le NLI
affiné graine 42 pour le Gold, déclaré dans le protocole et EXP-D-018 : cette
configuration est différente des runs historiques. La règle « tous les passages
cités sont neutres → abstention » a été évaluée sur le dev et n'est pas adoptée
(EXP-D-018). Elle n'est pas activée par cette mise à jour. Le juge Qwen reste
non validé (EXP-D-017) : les annotations humaines restent nécessaires.
Le résultat τ = 0 d'EXP-C-015 ne constitue pas un nouveau seuil à brancher.

EXP-C-012/013 restent hors évaluation jusqu'à la décision collective. Les nouveaux
articles et le jeu Gold doivent être autorisés, séparés du développement et gelés
avant la mesure. L'annotation humaine des verdicts s'effectue sans voir celle de Hadil.


## Relecture Lot D

Le rapport Lot E est dans `docs/report/06_integration_audit_lot-e_gold.md` ; le
parcours et la narration sont dans `docs/lot-e_demo_gold_75s.md`.

Les champs input/normalized et le helper _claims_from_doc sont repris de la
proposition lot-e-demo, sans importer sa seconde déclaration de /check/detail.
Une seule route et une seule normalisation sont exécutées par requête détaillée.
Une citation hors des preuves retrouvées, détectée au dernier contrôle Lot E,
produit citation_hors_liste, distinct de llm_unavailable.
