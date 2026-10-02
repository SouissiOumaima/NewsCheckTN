# Architecture — NewsCheck TN

## Flux de données

```
str ──A2──► Document ──B──► list[Claim] ──C──► list[Claim] (vérifiables)
                                                   │
                     list[Evidence] (corpus A1) ───┤
                                                   ▼
                                     ──D──► list[Evidence] (top-k)
                                                   │
                                     ──C──► list[StanceResult] (NLI)
                                                   │
                                     ──D──► Verdict (label, explication, citations, incertitude, abstention)
```

Orchestration : `pipeline.check_text(text) -> list[Verdict]` (Lot E), exposée par `POST /check`.

## Contrats

Les types sont définis dans `common/schemas.py`. Les signatures des points d'entrée sont listées
dans `CONTRIBUTING.md` (section 4). Tant qu'un lot respecte sa signature, il peut changer librement
son implémentation interne sans impacter les autres.

## Principes

1. **Stubs d'abord** : chaque étape renvoie dès le départ un résultat valide, ce qui permet à chaque lot
   de développer et tester indépendamment, et au Lot E d'intégrer en continu.
2. **Abstention par défaut** : sans preuve décisive, le système répond `preuves_insuffisantes`
   plutôt que d'halluciner.
3. **Traçabilité** : tout verdict cite les `doc_id` des preuves ; toute expérience a une entrée dans `experiments.md`.
4. **Légèreté de la CI** : les dépendances lourdes sont importées paresseusement ; la CI n'installe que `requirements-dev.txt`.

## Langues

| Code | Langue | Particularités |
|------|--------|----------------|
| `fr` | Français | spaCy `fr_core_news_*` |
| `ar` | Arabe standard | Stanza `ar`, normalisation orthographique |
| `tn` | Tunisien | lettres arabes ou arabizi, code-switching avec le français |
