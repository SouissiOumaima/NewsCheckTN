# Carte de données — corpus utilisés par le Lot A2

Version finale (palier Silver, 2026-11-14). Les données du projet (preuves, affirmations, annotations
des verdicts) relèvent du Lot A1. Les jeux ci-dessous servent uniquement à construire et à mesurer la
normalisation, l'identification de la langue et de l'écriture, et la détection du bruit. Aucun n'est
versionné : ils sont dans `data/raw/langid/` et `data/interim/langid/` (ignorés par Git), et chacun les
télécharge selon `normalization/README.md`. Chaque chiffre cité renvoie à une entrée de
`experiments.md`.

## 1. Corpus publics

| Jeu | Contenu | Licence | Usage dans le Lot A2 |
| --- | --- | --- | --- |
| TSAC | commentaires Facebook tunisiens, lettres arabes et latines | LGPL-3.0 | lexique tunisien (EXP-A2-002, 004) ; échantillons annotés ; candidats du lexique élargi (EXP-A2-012, 013) ; modèle de perplexité (EXP-A2-010) ; réserve du modèle appris |
| Tunizi | commentaires tunisiens en arabizi | CC BY 4.0 | exemples d'arabizi pour le modèle à n-grammes (EXP-A2-003, 006) ; modèle de perplexité (EXP-A2-010) |
| UD French-GSD | phrases françaises (train 14 450, dev 1 476, test 416) | CC BY-SA 4.0 | exemples français (train) ; choix du seuil arabizi (dev) ; test consulté pour les fausses alertes (416 phrases) |
| UD Arabic-PADT | presse en arabe standard (dev 909, test 680) | CC BY-NC-SA 3.0 | filtre du lexique (mots absents de train) ; réglage des fausses alertes (dev) ; contrôle des fausses alertes (test) |
| Leipzig Corpora Collection, arabe, News 2022, 300K | 300 000 phrases de presse en arabe standard | CC BY (corpus téléchargeables, conditions d'utilisation du site) | référence d'arabe standard pour filtrer les candidats du lexique (EXP-A2-013) ; corpus de presse maghrébine écartés volontairement (citations possibles en dialecte) |

**Ce qui n'est pas utilisé.** TSAC et Tunizi sont à l'origine des corpus d'analyse de sentiment : leurs
étiquettes positif / négatif ne sont **jamais** utilisées. Seuls leurs textes servent, comme source de
vrai tunisien de réseaux sociaux ; les étiquettes de langue sont posées par l'équipe (section 2).

## 2. Jeux construits par le Lot A2

| Jeu | Construction | Taille | Statut et empreinte |
| --- | --- | --- | --- |
| Échantillon TSAC en lettres arabes | tirage graine 13, 3 mots ou plus, sans doublon (`annotation sample arabic`) | 100 | annoté (`t` / `a` / `x`) par deux personnes, kappa 0,65 (accord 0,87, EXP-A2-007) |
| Échantillon TSAC en lettres latines | même tirage, sans chiffre d'arabizi (`annotation sample latin`) | 100 | annoté (`t` / `f` / `x`) par deux personnes, kappa 0,84 (accord 0,92, EXP-A2-007) |
| Références adjugées (dev) | 21 désaccords tranchés à deux (EXP-A2-009) | lettres arabes : 100 (77 `t`, 23 `a`) ; lettres latines : 86 décidés (70 `t`, 16 `f`) | gelées le 2026-10-26 ; SHA-256 `a59f3d27621a4f4d4297f7d73b80301418767197316fb785cb7f0f32bb4ad92f` (arabe) et `1703f003cc0132c148ca46bf92b86ea05270d8851eb3d447109e366985877a46` (latin) |
| Moitiés fixes du dev arabe (Silver) | coupe par empreinte SHA-256 de chaque texte (`silver_tuning.half`), sans graine | « reglage » 47 ; « mesure » 53 | « reglage » pour choisir (EXP-A2-012, 013) ; « mesure » utilisée une seule fois (EXP-A2-013) |
| Données du modèle arabizi | extraits français et commentaires arabizi (EXP-A2-006), graine 13 | 35 194 extraits français ; 66 241 textes arabizi | modèle régénérable à l'identique (poids en JSON) |
| Données de la perplexité | TSAC + Tunizi préparés, 3 mots ou plus, sans doublon ; graine 13 ; 80 / 10 / 10 | lettres arabes 4 556 / 569 / 569 ; lettres latines 53 804 / 6 725 / 6 725 | seuil au 95e centile du dev (EXP-A2-010) |
| Modèle appris : test gelé (nouveau) | réserve de 5 735 commentaires TSAC en lettres arabes jamais annotés ; graine 20261107 (`model_tn_data draw`) | 300 | à annoter par deux personnes ; liste ordonnée SHA-256 `a579a57da9611c1218bcb24c3e78df6979c381e284ac25f8ccf9c9af37fdd252` ; jamais utilisé avant la mesure finale |
| Modèle appris : entraînement | même tirage, disjoint du test | 800 (dont 160 annotés deux fois) | SHA-256 `5b4f40b94c7ac38ecae82afdf9ab76ea7cc1c478069db4dfdc0191bcd716b061` |

Guide : `docs/lot-a2_guide_annotation.md`. Protocole du modèle appris, pré-inscrit avant le tirage :
`docs/lot-a2_modele_tn_protocole.md`. Tirages vérifiables :
`python -m normalization.annotation sample arabic --check`.

## 3. Jeu partagé

`tests/fixtures/linguistic_analysis/eval_30.jsonl` (Lot B) : 34 phrases rédigées depuis sa création
(commit `3c0c382` ; 10 FR, 10 arabe standard, 14 tunisien : 5 en lettres arabes, 5 en arabizi,
4 mixtes), étiquettes `lang` et `script`. Le nom « eval_30 » est historique ; un renommage en
`eval_frozen_34.jsonl` a été proposé au Lot B.

- **Pour le Lot A2** : test gelé le 2026-10-20 au commit `85fb77d`, SHA-256
  `1d0bcfaa4b2a01fbd428fb18240174e309ac9877dc474a4dc1399e15e9dd34ce`. Consulté pour mesurer pendant le
  Bronze (EXP-A2-001, 002), il n'a jamais servi à écrire une règle ni à régler un seuil (EXP-A2-011) ;
  au Silver, il ne sert qu'à vérifier l'absence de régression.
- **Pour le Lot B** : jeu de mise au point des règles (EXP-B-007) ; ses scores B sont donc optimistes.
- Il ne contient que 5 phrases en tunisien en lettres arabes : il ne peut pas juger seul le rappel de
  cette classe (d'où le nouveau test gelé de 300 textes).

## 4. Provenance et reproductibilité

- Archive Leipzig : `ara_news_2022_300K.tar.gz`, téléchargée le 2026-11-06, SHA-256
  `63b50fc6756002b2896055aafc3773cf2169a41a3947bac6ec39eb0febe5215d`, lue sans extraction.
- Commandes : `normalization.review` (revue Bronze), `normalization.silver_tuning tune` et
  `tune --leipzig` (EXP-A2-012, 013), `normalization.model_tn_data draw` puis `kappa`.
- Les sorties contenant des textes (erreurs, tirages) restent dans `data/interim/` ; seuls des comptes,
  des scores et des empreintes sont versionnés.
- Outil pour les autres lots : `normalization.tag_lang` ajoute la langue et l'écriture de chaque texte
  d'un fichier local, sans afficher de texte (tâche S8).

## 5. Limites et précautions

- **Bruit d'étiquette** : Tunizi contient des commentaires en français ; UD French-GSD dev contient au
  moins une phrase anglaise ; en lettres arabes, l'accord entre annotateurs reste modéré (kappa 0,65),
  car la frontière entre tunisien et arabe standard est floue.
- **Contenu** : commentaires publics, parfois injurieux ; ils peuvent citer des personnes. Ils ne sont
  ni redistribués ni versionnés, et le journal ne cite pas d'insultes. Une liste de mots extraite
  automatiquement de ces commentaires contient des noms propres et des injures : elle doit être relue
  par un humain avant tout usage (EXP-A2-013).
- **Représentativité** : commentaires de réseaux sociaux (TSAC, Tunizi) et presse (PADT, GSD,
  Leipzig) ; les affirmations du projet (Lot A1) n'ont pas encore été mesurées par langue.
- **Recouvrement** : le nouveau test gelé et les marques du lexique viennent tous deux de TSAC ; la
  baseline à lexique peut en être légèrement avantagée.
- **Licences** : PADT est sous licence non commerciale (NC) ; tout usage hors du cadre académique
  doit être revu.

## 6. Citations

- D. Goldhahn, T. Eckart et U. Quasthoff, « Building Large Monolingual Dictionaries at the Leipzig
  Corpora Collection: From 100 to 200 Languages », LREC 2012.
- Universal Dependencies : UD French-GSD et UD Arabic-PADT (citer les versions utilisées, comme
  l'indique chaque dépôt).
- TSAC et Tunizi : citer les articles de référence indiqués dans leurs dépôts respectifs.
