# Frontend NewsCheck TN — description détaillée

## 1. Rôle du frontend

Le frontend est la partie visible de NewsCheck TN. Il permet de tester chaque
lot séparément, puis de visualiser l'enchaînement complet d'une vérification.
Il ne contient pas de logique de machine learning : chaque action appelle une
route de l'API FastAPI et affiche la réponse de manière lisible.

L'application est servie par l'API à l'adresse :

```text
http://127.0.0.1:8000/app/
```

La racine `http://127.0.0.1:8000/` ne contient pas de page web ; un `404` à
cette adresse est donc normal.

## 2. Lancer la démonstration

Depuis la racine du dépôt :

```powershell
uvicorn api.main:app --reload
```

Puis ouvrir `http://127.0.0.1:8000/app/` dans le navigateur. Les pages sont
des fichiers HTML/CSS/JavaScript natifs : aucun serveur Node, build ou
installation frontend supplémentaire n'est nécessaire.

## 3. Navigation

Toutes les pages partagent un menu, le style graphique et le contrôle de
connexion à l'API. L'adresse de l'API peut être modifiée depuis le bouton
« changer » dans l'en-tête ; le choix est mémorisé dans le navigateur.

| Page | Adresse | Rôle |
| --- | --- | --- |
| Accueil | `/app/` | Vérification complète d'un texte via le pipeline principal. |
| Démo Bronze | `/app/bronze.html` | Démonstration guidée des cinq étapes classiques. |
| A1 · Données | `/app/lot-a1.html` | Taille du corpus, sources et exemples de passages chargés. |
| A2 · Normalisation | `/app/lot-a2.html` | Normalisation Unicode et identification de langue/écriture. |
| B · Affirmations | `/app/lot-b.html` | Extraction des affirmations, triplet SPO et modalité. |
| C · Modèles et NLI | `/app/lot-c.html` | Test de Model 1 et comparaison affirmation/preuve par NLI. |
| D · Preuves et verdict | `/app/lot-d.html` | Recherche de passages, position et verdict avec citations. |
| Évaluation | `/app/evaluation.html` | Lecture des fichiers de résultats présents dans `evaluation/results/`. |

## 4. Page d'accueil — vérification complète

La page d'accueil accepte un texte en français, arabe standard, tunisien ou
arabizi. Elle propose quatre exemples rapides, puis appelle `POST /check`.

Pour chaque affirmation retenue, elle affiche :

- le texte de l'affirmation ;
- sa langue et sa modalité ;
- le verdict (`vrai`, `faux`, `trompeur` ou `preuves_insuffisantes`) ;
- les citations utilisées ;
- le niveau d'incertitude ;
- une indication d'abstention lorsqu'aucune preuve suffisamment pertinente ou
  décisive n'a été trouvée.

## 5. Démo Bronze — parcours recommandé pour l'oral

La page `/app/bronze.html` est la page la plus adaptée à une démonstration du
palier Bronze. Elle exécute les briques classiques sans demander au jury de
naviguer d'une page à une autre.

### Entrée

L'utilisateur fournit une phrase ou un court texte et choisit le nombre maximal
de passages BM25 à récupérer. Trois exemples sont proposés : une preuve
disponible, un exemple sur le chômage et un exemple sans preuve.

### Étape 1 — A2 : normalisation et langue

La page appelle `POST /normalize`. Elle affiche :

- le texte normalisé ;
- la langue détectée (`fr`, `ar`, `tn` ou `unk`) ;
- l'écriture (`latin`, `arabic`, `arabizi` ou `mixed`).

### Étape 2 — B + C : affirmation retenue

La page appelle `POST /extract/bronze`. Le système segmente le texte et garde
les affirmations assertives par règles, sans filtre Model 1 appris. Ainsi, une
affirmation claire ne bloque pas la démonstration complète à cause d'une erreur
du classifieur. La démo affiche :

- l'affirmation choisie ;
- la modalité ;
- le score de vérifiabilité `P(AFFIRMATION)`.

Si aucune affirmation n'est retenue, les étapes suivantes s'arrêtent
explicitement : une opinion, question ou hypothèse ne doit pas recevoir un
verdict factuel.

### Étape 3 — D : recherche BM25

La page appelle `POST /retrieve` avec l'affirmation retenue. Elle présente :

- le rang de chaque passage ;
- son identifiant et sa source ;
- son score BM25 ;
- son texte.

L'absence de passage est affichée clairement. Elle peut mener à l'abstention
du verdict, ce qui est un comportement attendu et non une panne.

### Étape 4 — C : position par lexique

Pour chaque passage BM25, la page appelle `POST /nli`. Le composant Bronze
retourne l'une des trois positions :

- `supports` : le passage soutient l'affirmation ;
- `refutes` : le passage la contredit ;
- `neutral` : le passage ne permet pas de trancher.

La page affiche aussi la confiance associée. Le backend Bronze utilise des
indices explicables : recouvrement lexical, nombres, marqueurs de démenti et
négation.

### Étape 5 — D : verdict par gabarit

La page appelle `POST /verdict`. Elle affiche le verdict, l'explication, les
identifiants des passages cités et l'incertitude. Le système s'abstient si :

- aucune preuve n'est retrouvée ;
- les preuves sont sous le seuil de pertinence ;
- aucune position n'est décisive ;
- les preuves décisives se contredisent trop fortement.

## 6. Pages de lots

### A1 — Données et corpus

La page A1 appelle `GET /corpus/stats`. Elle affiche le nombre de passages,
les sources disponibles et quelques extraits. Si seulement deux passages sont
chargés, elle prévient que l'API utilise l'échantillon de démonstration.

### A2 — Normalisation

La page A2 propose des exemples français, arabe, tunisien et arabizi. Elle
montre la différence entre texte brut et texte normalisé, ainsi que la langue
et l'écriture détectées.

### B — Extraction

La page B affiche chaque affirmation détectée avec son sujet, prédicat, objet,
modalité et score de vérifiabilité. Elle est utile pour expliquer pourquoi une
phrase est envoyée ou non vers la recherche de preuves.

### C — Model 1 et NLI

La page C présente les indicateurs Model 1 (Macro-F1, accuracy, scores par
langue) fournis par `GET /model-c/model1`. Elle permet aussi :

- de tester une phrase avec `POST /extract` ;
- de comparer manuellement une affirmation et une preuve avec `POST /nli`.

### D — Preuves et verdict

La page D permet de choisir une affirmation, une langue, le nombre de passages
et le moteur de position. Elle appelle `POST /verdict/detail` et affiche, dans
la même vue, le verdict et chaque preuve avec son rang, score, position et
statut de citation.

### Évaluation

La page d'évaluation appelle `GET /results`. Elle affiche les fichiers JSON
présents dans `evaluation/results/`, par exemple les métriques de démonstration
Bronze et les analyses d'erreurs Model 1.

## 7. Routes utilisées par le frontend

| Route | Méthode | Utilisation |
| --- | --- | --- |
| `/health` | GET | Vérifie que l'API est disponible. |
| `/normalize` | POST | A2 : normalisation, langue, écriture. |
| `/extract` | POST | B + C : affirmations retenues avec le filtre Model 1. |
| `/extract/bronze` | POST | B : affirmations assertives à règles pour la Démo Bronze. |
| `/retrieve` | POST | D : passages BM25/dense/hybrides selon la configuration. |
| `/nli` | POST | C : position d'une preuve face à une affirmation. |
| `/verdict` | POST | D : verdict simple avec citations. |
| `/verdict/detail` | POST | D : verdict et détail de toutes les preuves. |
| `/check` | POST | Pipeline complet de l'accueil. |
| `/corpus/stats` | GET | A1 : description du corpus chargé. |
| `/model-c/model1` | GET | C : informations et scores Model 1. |
| `/results` | GET | Évaluation : résultats JSON légers. |

## 8. Corpus réel et limites de la démo

Sans variable d'environnement, l'API utilise un petit corpus d'exemple. C'est
suffisant pour montrer le fonctionnement technique, mais insuffisant pour une
évaluation réelle ou pour couvrir tous les sujets.

Pour utiliser le corpus Tunifact préparé localement :

```powershell
python -m rag_llm.build_tunifact_eval
$env:EVIDENCE_CORPUS="data/interim/lot_d/evidence_tunifact_v1.jsonl"
uvicorn api.main:app --reload
```

Les verdicts doivent toujours être lus avec leurs citations. Une abstention
signifie que le système préfère ne pas conclure plutôt que d'inventer une
preuve.

## 9. Fichiers techniques

| Fichier | Contenu |
| --- | --- |
| `frontend/assets/style.css` | Thème, cartes, tableaux, couleurs, affichage arabe. |
| `frontend/assets/app.js` | Navigation, appels API, gestion d'erreurs et composants de verdict. |
| `frontend/index.html` | Vérification complète. |
| `frontend/bronze.html` | Démo guidée du palier Bronze. |
| `frontend/lot-*.html` | Pages dédiées aux lots. |
| `frontend/evaluation.html` | Tableau des résultats disponibles. |
| `api/main.py` | Routes FastAPI consommées par les pages. |

## 10. Phrase courte pour présenter le frontend

> « Le frontend permet de tester chaque lot indépendamment et de suivre, sur
> la Démo Bronze, le chemin complet d'une affirmation : normalisation,
> extraction, recherche BM25, comparaison lexicale avec les preuves, puis
> verdict cité ou abstention. »
