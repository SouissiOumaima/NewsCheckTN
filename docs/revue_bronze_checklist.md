# Checklist finale — Revue Bronze

## Déjà automatisé dans le dépôt

- Route de démo classique `/bronze/check`, traçage complet et latence.
- Tests E2E API : succès, opinion filtrée, intégrité des citations.
- Audit reproductible Lot E et synthèse JSON dans `evaluation/results/`.
- Tableau web des évaluations : `/app/evaluation.html`.
- Contrats inter-lots : `docs/architecture.md` et `docs/lot-e_integration_bronze.md`.

## À faire par l'équipe avant la présentation

- [ ] Réaliser les 30 erreurs **réellement annotées** pour chaque composant
  principal qui les requiert ; ne pas remplacer ces observations par des exemples inventés.
- [ ] Finaliser une double annotation et calculer le kappa, puis compléter la data card.
- [ ] Préparer slides PDF et vidéo de secours de deux minutes.
- [ ] Créer le tag Git `bronze` sur le commit présenté et le noter sur la slide finale.
- [ ] Ajouter/valider la reproduction d'un résultat externe si elle est imposée par l'enseignant.
- [ ] Ajouter la déclaration d'usage IA, le Kanban/journal et les noms des responsables.

Ces derniers points demandent des données, des décisions et une validation humaine ; ils ne peuvent
pas être certifiés automatiquement par le code.
