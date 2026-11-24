# `frontend/` — Lot E : Interface web

**Responsable : Membre 6 · Branche : `lot-e-integration`**

Une page par lot (`lot-a1.html` … `lot-d.html`), une page d'accueil (`index.html`) et un tableau de
bord d'évaluation (`evaluation.html`), avec des styles et un accès à l'API communs (`assets/`).

## Lancer la plateforme

Depuis la racine du dépôt :

```bash
uvicorn api.main:app --reload
```

Puis ouvrir **http://localhost:8000/app/**. Les pages sont servies par l'API elle-même : pas de
serveur à part, pas de Node, pas de problème de CORS.

### Utiliser un vrai corpus de preuves

Par défaut l'API lit `data/processed/evidence_corpus.jsonl`, et sinon 2 passages d'exemple. Pour
travailler sur un corpus **non versionné** (par exemple Tunifact, dont les droits de redistribution ne
sont pas confirmés), on ne le copie pas dans `data/processed/` (ce dossier n'est pas ignoré par Git) :
on indique son chemin avec la variable `EVIDENCE_CORPUS`.

PowerShell :

```powershell
python -m rag_llm.build_tunifact_eval          # crée data/interim/lot_d/evidence_tunifact_v1.jsonl
$env:EVIDENCE_CORPUS="data/interim/lot_d/evidence_tunifact_v1.jsonl"; uvicorn api.main:app --reload
```

bash :

```bash
EVIDENCE_CORPUS=data/interim/lot_d/evidence_tunifact_v1.jsonl uvicorn api.main:app --reload
```

Si le chemin de `EVIDENCE_CORPUS` est faux ou si le fichier est invalide, l'API répond par une erreur
claire (code 503, avec le fichier et le numéro de ligne) au lieu de retomber en silence sur l'échantillon.
Le fichier `data/processed/evidence_corpus*.jsonl` est ignoré par Git, pour ne jamais versionner par
erreur un corpus dont les droits ne sont pas confirmés.

## Démonstration Falcon locale

Le modèle officiel actuel du Lot D est Falcon-H1-3B + JSON (EXP-D-015).
Aya 8B (EXP-D-010) reste historique ; les résultats existants ne sont pas réécrits.
Le score de Falcon est optimiste car issu d'un second passage sur le même test.

**Prérequis :** utiliser une version intégrant la PR #33 (`lot-d-falcon` tant que
non fusionnée), installer Ollama et le modèle sur le PC qui lance l'API, préparer
les checkpoints Model 1/NLI et le corpus privé. Ollama doit répondre sur le port 11434.
Le chargement initial des modèles publics peut nécessiter le réseau ; préparer
les caches avant une démonstration hors connexion. Ne pas versionner les modèles
ni les passages Tunifact.

Depuis la racine du dépôt, dans PowerShell :

```powershell
$env:VERDICT_BACKEND = "llm"
$env:LLM_PROVIDER = "ollama"
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY = "ollama"
$env:LLM_MODEL = "hf.co/tiiuae/Falcon-H1-3B-Instruct-GGUF:Q4_K_M"
$env:LLM_RESPONSE_FORMAT = "json"
$env:LLM_MIN_INTERVAL = "0"
$env:LLM_ALLOW_EXTERNAL = "0"
$env:CLAIM_DETECTOR_BACKEND = "xlmr"
$env:CLAIM_DETECTOR_CHECKPOINT = "models/checkpoints/claim_detection_xlmr_lora_seed42"
$env:RETRIEVAL_METHOD = "hybrid"
$env:EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
$env:EVIDENCE_CORPUS = "data/interim/lot_d/evidence_tunifact_v1.jsonl"
# Bronze dans les expériences Falcon existantes ; affiné confirmé pour le Gold.
$env:NLI_BACKEND = "bronze"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Ouvrir `http://127.0.0.1:8000/app/`. Les variables doivent être définies dans le
processus qui lance l'API : `.env` n'est pas chargé automatiquement.

Pour l'essai Gold confirmé par le Lot D (EXP-D-018), remplacer `NLI_BACKEND`
par `fine-tuned` et définir `NLI_FINETUNED_MODEL` vers
`models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed42`. Redémarrer l'API et
consigner ce changement ; il ne reproduit pas les runs Falcon avec Bronze.
Sur la GTX 1650 de Hadil, les encodeurs peuvent rester sur CPU pour réserver le
GPU au serveur Ollama ; la configuration matérielle fait partie de la trace.

Vérifier dans `/check/detail` le NLI actif, `verdict_engine.used=llm`, le modèle
Falcon et l'absence de repli. Un résultat gabarit n'est pas une exécution Falcon.
L'interface affiche le moteur et le modèle réels et masque l'incertitude fixe du
LLM au profit de « incertitude non calibrée ». Une citation présente dans les
passages retrouvés peut rester hors sujet : montrer aussi cette limite.

La règle d'abstention Gold n'est pas activée ici : elle n'a pas été adoptée après
la mesure sur dev (EXP-D-018). Le juge Qwen n'est pas validé (EXP-D-017).
Les réécritures NLI EXP-C-012/013 restent suspendues.

## Pages

| Page | Fichier | Responsable | Route(s) API |
|---|---|---|---|
| Vérifier un texte | `index.html` | base commune | `POST /check` |
| A1 · Données | `lot-a1.html` | Lot A1 | `GET /corpus/stats` |
| A2 · Normalisation | `lot-a2.html` | Lot A2 | `POST /normalize` |
| B · Affirmations | `lot-b.html` | Lot B | `POST /extract` |
| C · Modèles et NLI | `lot-c.html` | Lot C | `POST /nli` |
| D · Preuves et verdict | `lot-d.html` | Lot D | `POST /verdict/detail` |
| Évaluation | `evaluation.html` | base commune | `GET /results` |

Les pages A1, A2, B et C sont des **pages de départ** (marquées « à compléter ») : elles appellent déjà
la route de leur lot et affichent la réponse brute. Chaque lot les enrichit.

Le tableau de bord d'évaluation lit tous les fichiers de `evaluation/results/` (format commun décrit
dans `evaluation/README.md`) : un lot qui écrit ses résultats dans ce format apparaît automatiquement,
sans toucher au frontend.

## Fichiers communs

- `assets/style.css` : couleurs (thème clair et sombre), composants `.card`, `.btn`, `.chip`, `.tag`,
  `.verdict-chip`, `.verdict`, `.ev` (passage), `.kpi`, `table.t`, `.notice`, `.tiles` / `.tile`.
  Style « moderne et coloré » : dégradé violet → bleu (`--grad`), cartes très arrondies, puces en pilule.
- `assets/app.js` : objet global `NC`.
  - `NC.init("<id>")` dessine l'en-tête et le pied de page, et vérifie que l'API répond.
  - `NC.api("/route")` fait un GET ; `NC.api("/route", corps)` fait un POST JSON. Les erreurs sont
    renvoyées sous forme de message lisible.
  - `NC.text(s)` affiche un texte avec `dir="auto"` et la police arabe si besoin ; `NC.esc(s)` échappe
    le HTML ; `NC.fmt(x, 2)` formate un nombre à la française.
  - `NC.verdictBox(verdict, verdict_engine)`, `NC.verdictChip(label)`, `NC.stanceChip(stance, conf)` : affichage
    standard d'un verdict et d'une position.

L'adresse de l'API se change dans l'en-tête (« changer ») ; le choix est gardé dans le navigateur.

## Ajouter ou compléter une page

1. Copier une page de départ (par exemple `lot-b.html`) et garder la structure :
   `<main class="page">`, `page-head`, puis des `.card`.
2. Si c'est une nouvelle page, ajouter **une ligne** dans `NC.PAGES` (`assets/app.js`), avec une icône et une courte description : elle
   apparaît alors dans le menu de toutes les pages.
3. Si la page a besoin d'une nouvelle route, l'ajouter dans `api/main.py` avec un test dans
   `tests/test_api.py`.
4. Vérifier dans le navigateur (thème clair et sombre, texte arabe), puis ouvrir une PR.

## Conventions

- HTML, CSS et JavaScript natifs, sans étape de build. Pas de nouvelle dépendance sans accord de l'équipe.
- Couleurs uniquement via les variables de `style.css` (pas de couleur en dur dans les pages).
- Tout texte venant des données passe par `NC.text` ou `NC.esc` (arabe, et sécurité).
- Ne jamais afficher un verdict sans ses citations ; afficher clairement les abstentions.
- Aucune donnée réelle dans `frontend/` : les exemples des pages sont fictifs ou très courts.
