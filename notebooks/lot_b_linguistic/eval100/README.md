# Préparation du jeu `eval_100` (Lot B)

Scripts de préparation des phrases candidates et du lot de double annotation, décrits dans
`docs/lot-b_protocole_eval_100.md` (section 2). **Aucune donnée n'est versionnée** : les sources
sont téléchargées dans un dossier de travail hors du dépôt, passé en argument à chaque script.
Les scripts ne font ni annotation ni appel au système d'extraction ; pendant toute la préparation
et l'annotation, ne lancer ni `evaluate.py`, ni la démo, ni `pipeline.py` sur ces phrases.

Lancer chaque script avec `python -I`, depuis ce dossier ou un autre, en lui donnant les chemins.

| Ordre | Script | Entrée | Sortie |
|-------|--------|--------|--------|
| 1 | `filter_xfact.py --xfact-dir <d> [--delete-originals]` | TSV de github.com/utahnlp/x-fact (`data/x-fact/`) | `xfact_ar_fr.tsv` (arabe et français seulement) |
| 2 | `sample_pool.py --arafacts-dir <d> --xfact-file <f> --out-dir <d>` | `AraFacts.csv`, `AraFacts_2.csv` (gitlab.com/bigirqu/AraFacts), `xfact_ar_fr.tsv` | `eval100_pool.jsonl` (`id`, `text`, `origin`) et rapport |
| 3 | `extract_checkthat.py --archive <zip> --out-dir <d> [--delete-archive]` | `CT21-AR-Train-T1-v2.zip` (gitlab.com/checkthat_lab/clef2021-checkthat-lab, tâche 1A arabe) | TSV texte + labels (les JSON de profils ne sont pas extraits) |
| 4 | `an_sentences.py --archives-dir <d> --out <f>` | archives `AN_*.taz` de echanges.dila.gouv.fr/OPENDATA/Debats/AN/ | `an_phrases.jsonl` |
| 5 | `build_batch.py --pool <f> --checkthat-dir <d> --out-dir <d> [--an <f>] --repo <chemins>` | sorties 2, 3 et 4 | CSV pour l'annotateur, correspondance id → origine, contrôle |

Graine par défaut : 20261016 (`--seed`). Licences et limites des sources : protocole, section 2.
Le fichier de correspondance (étape 5) reste un fichier de travail : il ne doit pas être transmis à
l'annotateur, qui ne reçoit que le CSV et la feuille de consignes.
