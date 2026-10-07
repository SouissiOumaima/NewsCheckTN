# `normalization/` — Lot A2 : Normalisation & multilinguisme

**Responsable : Membre 2 · Branche : `lot-a2-normalization`**

## Rôle
Transformer tout texte d'entrée en une forme propre et homogène, utilisée par tous les lots suivants :
- **normalisation** Unicode, espaces, ponctuation ;
- **arabe** : diacritiques, tatweel, variantes d'alef / ya / ta marbuta ;
- **tunisien** : arabizi (`3`=ع, `7`=ح, `9`=ق, `5`=خ, `2`=ء…) → lettres arabes, code-switching FR/TN ;
- **identification de langue** : `fr`, `ar` (MSA), `tn` (dialecte), et du script (arabe / latin / arabizi / mixte) ;
- **perplexité** (modèle de langue n-gram / KenLM) pour mesurer la « dialectalité » ou filtrer le bruit.

## Entrées / sorties
- Entrée : `str` (texte brut).
- Sortie : `common.schemas.Document` (`raw_text`, `text`, `lang`, `script`).
- Point d'entrée : `normalization.normalize.normalize(text: str) -> Document`.

## Organisation suggérée
| Fichier | Contenu |
|---------|---------|
| `normalize.py` | Point d'entrée + règles de normalisation |
| `arabizi.py` | Table de translittération et désambiguïsation |
| `langid.py` | Identification de langue : marques dialectales en lettres arabes (lexique `resources/tn_markers.txt`) |
| `perplexity.py` | Modèles de langue et calcul de perplexité |
| `evaluate.py` | Évaluation langue / script sur un jeu JSONL (`python -m normalization.evaluate --errors`) |
| `resources/` | Lexiques, tables de correspondance (petits fichiers uniquement) |

## Conventions
- Les fonctions sont **pures** (pas d'effet de bord) et **idempotentes** : `normalize(normalize(x).text).text == normalize(x).text`.
- Ne jamais perdre l'information d'origine : `raw_text` est conservé pour l'affichage et les spans.
- Les modèles téléchargés (ex. `lid.176.bin`) vont dans `models/checkpoints/` (non versionné), avec la commande de téléchargement documentée ici.
- Évaluation : précision de l'identification de langue par classe, à consigner dans `experiments.md`.
