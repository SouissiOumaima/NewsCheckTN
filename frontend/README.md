# `frontend/` — Lot E : Interface web

**Responsable : Membre 6 · Branche : `lot-e-integration`**

## Rôle
Interface permettant de coller un texte (FR / AR / tunisien), de lancer la vérification et d'afficher,
pour chaque affirmation : le verdict, l'explication, les preuves citées (avec lien) et le niveau d'incertitude.

## État actuel
`index.html` : page statique minimale (HTML + JS natif) qui appelle `POST /check` sur `http://localhost:8000`.
1. Lancer l'API : `uvicorn api.main:app --reload`
2. Ouvrir `frontend/index.html` dans le navigateur.

## Évolution
Le framework définitif est libre (React/Vite, Vue, Streamlit…). Si un projet Node est créé ici :
- `node_modules/` et `dist/` sont déjà ignorés par git ;
- documenter `npm install` / `npm run dev` dans ce README ;
- l'URL de l'API doit être configurable (variable d'environnement), pas codée en dur.

## Conventions
- Gérer le texte bidirectionnel (`dir="auto"`) pour l'arabe.
- Ne jamais afficher un verdict sans ses citations ; afficher clairement les abstentions.
