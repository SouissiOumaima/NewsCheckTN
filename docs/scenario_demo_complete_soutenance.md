# Scénario complet de démonstration NewsCheck TN

Durée cible : 7 à 9 minutes. Lancer d'abord, depuis la racine du dépôt :

```powershell
uvicorn api.main:app --reload
```

Puis ouvrir `http://127.0.0.1:8000/app/`. Pour filmer, mettre le navigateur en plein écran,
faire `Ctrl + F5`, puis suivre les étapes ci-dessous dans l'ordre. Ne pas montrer une capture
statique : attendre le résultat de chaque appel API.

## 0. Introduction et carte du système — 30 secondes

### Écran

`/app/` — page **Vérifier un texte**.

### Ce que je dis

> Notre projet NewsCheck TN transforme un texte en verdict justifié. Le parcours est :
> normalisation et identification de langue par le Lot A2, extraction des affirmations par le
> Lot B, détection et position par les modèles du Lot C, recherche de preuves BM25 et verdict
> cité par le Lot D. Le Lot E intègre ces briques dans une API, un frontend et un tableau de bord.
> Lorsqu'il n'y a pas de preuve fiable, le système s'abstient.

## 1. Lot A1 — Données et corpus — 45 secondes

### Écran

Cliquer **A1 · Données**. La page appelle `GET /corpus/stats`.

### Ce que je montre

- La taille du corpus chargé.
- Les sources et un exemple de passage.
- Si la page indique `échantillon`, préciser que la démo utilise trois passages pédagogiques.

### Ce que je dis

> Le Lot A1 fournit les passages de preuve. Chaque passage possède un identifiant, un texte,
> une source, et éventuellement une URL ou une date. Le pipeline ne doit jamais inventer une
> source : les citations finales reprennent seulement les identifiants provenant de ce corpus.

## 2. Lot A2 — Normalisation et langue — 45 secondes

### Écran

Cliquer **A2 · Normalisation**.

### Texte à coller

```text
سعر الخبز المدعم 190 مليما
```

### Résultat à vérifier

- Langue : `ar`.
- Écriture : `arabic`.
- Le nombre `190` reste présent après normalisation.

### Ce que je dis

> Le Lot A2 nettoie le texte sans supprimer l'information factuelle, puis identifie la langue et
> l'écriture. C'est indispensable avant les règles et la recherche : par exemple, ici le texte est
> arabe et le nombre 190 est conservé.

## 3. Lot B — Extraction d'affirmation — 45 secondes

### Écran

Cliquer **B · Affirmations**.

### Texte à coller

```text
Le taux de chômage en Tunisie était de 16,4 % au deuxième trimestre 2023.
```

### Résultat à vérifier

- Une affirmation est détectée.
- Modalité : `assertif`.
- Le texte de la claim est affiché ; le triplet sujet, prédicat, objet est affiché si la règle
  l'extrait avec confiance.

### Ce que je dis

> Le Lot B conserve les propositions factuelles et écarte les questions, les souhaits et les avis.
> Cette phrase peut être vérifiée avec une source, donc elle est transmise à la recherche de preuves.

## 4. Lot C — Model 1 et NLI — 1 minute 15 secondes

### Écran

Cliquer **C · Modèles et NLI**.

### Test Model 1

Coller :

```text
Tunis est la capitale de la Tunisie.
```

Puis cliquer **Détecter**.

Dire :

> Model 1 classe une phrase en AFFIRMATION, OPINION ou AUTRE. Une affirmation retenue devient un
> candidat à vérifier. La baseline classique de la revue est TF-IDF de caractères plus régression
> logistique ; le modèle avancé ne fait pas partie de la démo Bronze.

Tester ensuite une opinion :

```text
Je pense que Tunis est magnifique.
```

Dire :

> Cette phrase contient un jugement. Elle ne doit pas être présentée comme un fait à vérifier.

### Test Model 2 NLI

Dans **Affirmation**, coller :

```text
Le taux de chômage en Tunisie était de 25 % en 2023.
```

Dans **Passage de preuve**, coller :

```text
Selon l'INS, le taux de chômage en Tunisie était de 16,4 % en 2023.
```

Cliquer **Comparer**. Attendu : `refutes`.

Dire :

> Le NLI ne cherche pas encore une source : il compare une affirmation et un passage. Ici les deux
> phrases parlent du même indicateur et de la même année, mais 25 % est différent de 16,4 %, donc
> le passage contredit l'affirmation.

## 5. Lot D — Preuves et verdict — 1 minute

### Écran

Cliquer **D · Preuves et verdict**.

### Claim à saisir

```text
Tunis est la capitale de la Tunisie.
```

### Ce que je montre

- Le top-k de passages BM25.
- Pour chaque passage : score, source et position NLI.
- Le verdict final et ses citations.

### Ce que je dis

> BM25 est la recherche classique par termes : elle sélectionne les passages qui peuvent servir de
> preuve. Le NLI positionne ensuite chaque passage. Enfin le gabarit du Lot D produit un verdict
> avec des citations. La règle importante est : sans preuve décisive, le verdict est une abstention.

## 6. Démo Bronze intégrée — 2 minutes 30 secondes

### Écran

Cliquer **Démo Bronze**. Cette page appelle `POST /bronze/check` et montre le chemin classique :
normalisation, extraction par règles, BM25, NLI lexical, gabarit et latence.

### Scénario A — confirmation vraie

Cliquer **preuve disponible** ou coller :

```text
Tunis est la capitale de la Tunisie.
```

Attendu :

- Claim assertive.
- Preuve BM25 `sample-002`.
- Position `supports`.
- Verdict **Vrai** avec citation.

À dire :

> Ici nous avons le parcours complet : la preuve est retrouvée, elle soutient la claim, et le
> verdict est vrai avec la citation sample-002. La latence totale est affichée à droite.

### Scénario B — contradiction numérique

Cliquer **chômage** puis remplacer `16,4` par `25`, ou coller :

```text
Le taux de chômage en Tunisie était de 25 % au deuxième trimestre 2023.
```

Attendu :

- Preuve `sample-001` avec `16,4 %`.
- Position `refutes`.
- Verdict **Faux** avec citation.

À dire :

> Le retrieval trouve la source INS pertinente. La règle NLI compare les valeurs factuelles et
> détecte que 25 % contredit 16,4 %. Le système ne confond donc pas une année commune avec une
> valeur identique.

### Scénario C — arabe qui fonctionne

Cliquer **pain arabe** ou coller :

```text
سعر الخبز المدعم 190 مليما
```

Attendu :

- Langue `ar`, écriture `arabic`.
- Preuve `sample-003`.
- Position `supports`.
- Verdict **Vrai**.

À dire :

> Cet exemple prouve que la chaîne conserve l'arabe dans la normalisation, la recherche BM25 et
> l'affichage. La source est explicitement marquée comme exemple pédagogique ; elle sert à démontrer
> le flux, pas à prétendre qu'il s'agit d'une enquête officielle.

### Scénario D — pas de preuve

Cliquer **sans preuve** ou coller :

```text
Un nouvel aéroport a été inauguré à Kairouan en 2026.
```

Attendu :

- Claim détectée.
- Zéro preuve BM25 pertinente.
- Verdict **Preuves insuffisantes** et abstention.

À dire :

> L'absence de preuve ne devient jamais vrai ou faux. Le comportement sûr du système est
> l'abstention, avec une explication explicite.

### Scénario E — opinion filtrée

Coller :

```text
Je pense que Tunis est magnifique.
```

Attendu : **Filtré**, sans recherche ni verdict.

À dire :

> Ce n'est pas une panne. Une opinion est filtrée avant BM25 car elle n'est pas une affirmation
> factuelle dans le périmètre Bronze.

## 7. Lot E — Intégration et évaluation — 1 minute

### Écran

Cliquer **Évaluation**.

### Ce que je montre

- Filtre par lot E ou tous les lots.
- `EXP-E-002` : audit d'intégration Bronze.
- Les résultats B, C et D sont aussi visibles.

### Ce que je dis

> Le Lot E relie les lots et vérifie qu'ils fonctionnent ensemble. L'audit EXP-E-002 contient quatre
> contrôles : vrai, contradiction numérique, absence de preuve et opinion filtrée. Le résultat est
> 4 sur 4, zéro citation invalide. Ce score valide une intégration ; il ne remplace pas les métriques
> scientifiques des lots B, C et D sur leurs jeux dédiés.

## Conclusion — 20 secondes

> La démonstration montre une chaîne complète, observable et reproductible. Chaque étape est visible,
> les verdicts citent des preuves, la latence est mesurée, les erreurs et les abstentions sont assumées.
> La version de démo Bronze reste classique : règles, BM25, NLI lexical et gabarit, sans LLM.

## Checklist avant de filmer ou présenter

- [ ] API lancée et `GET /health` affiche 200.
- [ ] Ouvrir `/app/` puis faire `Ctrl + F5`.
- [ ] Vérifier les cinq scénarios Bronze dans l'ordre A à E.
- [ ] Vérifier que le bouton **pain arabe** donne `Vrai` et `sample-003`.
- [ ] Garder visible la zone latence au moins une fois.
- [ ] Ne pas annoncer le score de l'audit E2E comme score général du système.
- [ ] En cas de panne de corpus, expliquer qu'un corpus manquant produit une erreur claire ou une
  abstention, jamais une source inventée.
