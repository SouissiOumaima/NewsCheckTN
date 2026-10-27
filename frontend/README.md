# `frontend/` — Plateforme commune (Lot E, partagé)

**Base et tableau de bord : Membre 5 (Hadil) · Chaque lot complète sa propre page · Relecture : 2 membres**

Il n'y a pas de Membre 6 : la plateforme est construite par toute l'équipe. Membre 5 maintient la base
commune (en-tête, styles, accès à l'API, page d'accueil, tableau de bord d'évaluation) ; chaque lot
remplit la page qui le concerne.

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

## Pages

| Page | Fichier | Responsable | Route(s) API |
|---|---|---|---|
| Vérifier un texte | `index.html` | base commune | `POST /check` |
| Démo Bronze | `bronze.html` | intégration | `/normalize`, `/extract`, `/retrieve`, `/nli`, `/verdict` |
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
  - `NC.verdictBox(verdict)`, `NC.verdictChip(label)`, `NC.stanceChip(stance, conf)` : affichage
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
