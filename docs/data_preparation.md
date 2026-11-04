# Rapport de Data Preparation des données GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 3 Data Preparation |
| Code | `src/data/` et `tests/` |
| Notebook de référence | `notebooks/03_data_preparation.ipynb` |
| Documents associés | `docs/data_understanding.md` et `docs/data_dictionary.md` |
| Statut | Préparation terminée |

## 1. Objet du document

Ce rapport décrit les corrections appliquées aux données GROW-Africa à la suite du Data Understanding, l'organisation du code qui les implémente, les jeux de données produits et les points qui restent ouverts avant la modélisation.

## 2. Périmètre et décisions

| Décision | Contenu | Origine |
|---|---|---|
| Fichiers préparés | `regional`, `survey` et `cropcut`, traités séparément | Première condition de la décision issue du Data Understanding |
| Fichier exclu | `point`, qui ne porte aucune des cibles retenues | Décision du porteur du projet |
| Cible principale | `yieldTonHa` de `regional` aux niveaux administratifs 1 et 2 | Choix validé le 2 novembre 2026 |
| Cible à l'échelle de la parcelle | `YieldUsingGPS_ton_ha_` de `survey`, sans remplacement par le rendement fondé sur la surface déclarée | Choix validé le 2 novembre 2026, maintenu le 3 novembre 2026 au vu de la section 7.1 |
| Référence de validation | `Yield_ton_ha_` de `cropcut` pour l'Éthiopie | Choix validé le 2 novembre 2026 |
| Une ligne par cellule dans `regional` | Priorité au système de production global, puis à la source `HarvestStat` | Décision du porteur du projet |
| Traçabilité | Aucune ligne n'est supprimée des tableaux préparés, sauf les copies exactes de `survey`. Les lignes corrigées ou écartées portent un indicateur préfixé par `flag_` | Principe de la phase |

## 3. Organisation du code

| Module | Rôle |
|---|---|
| `src/data/load.py` | Chargement des fichiers bruts avec un cache dans `data/interim`, indexé par l'empreinte SHA-256 du fichier source |
| `src/data/common.py` | Normalisation des textes, bornes de plausibilité des auteurs, identifiant de grappe et contrôle de la hiérarchie GADM |
| `src/data/regional.py` | Corrections propres au fichier `regional` et extraction du jeu de modélisation |
| `src/data/survey.py` | Corrections propres au fichier `survey` et extraction du jeu de modélisation |
| `src/data/cropcut.py` | Corrections propres au fichier `cropcut` et extraction du jeu de validation |
| `src/data/prepare.py` | Orchestration de l'ensemble et export dans `data/processed` |

Chaque fonction travaille sur une copie de son entrée. La suite de 29 tests unitaires de `tests/` consacrés à la préparation vérifie chaque correction sur des cas construits pour l'occasion.

## 4. Corrections appliquées

### 4.1 Corrections communes

| Correction | Effet |
|---|---|
| Suppression du caractère invisible BOM et des espaces superflus | 318 identifiants `L1_GID` du Lesotho redeviennent exploitables |
| Conversion des jetons `[]` et `none` en valeurs manquantes | Les valeurs manquantes déguisées sont comptées comme telles |
| Bornes de plausibilité par culture | Calculées sur `regional` selon le filtre des auteurs, puis appliquées aux trois fichiers. Un rendement nul ou négatif est toujours jugé hors bornes, ce qui couvre la culture `Legumes`, dépourvue de bornes faute de rendement positif |

### 4.2 Fichier `regional`

| Correction | Lignes concernées |
|---|---:|
| Codes -999 et -99 convertis en valeurs manquantes, rendements négatifs dérivés invalidés | 66 rendements |
| Surface et production permutées sur les lignes inversées | 33 740 |
| Lignes ne vérifiant aucune relation entre production, surface et rendement, signalées | 1 710 |
| Codes pays du Ghana ramenés à `L0GHA086` | 71 codes deviennent 47 |
| Libellés de pays unifiés | 49 libellés deviennent 47 |
| Saison Meher harmonisée en Main dans une colonne `saison` | Saison principale éthiopienne |
| Niveau administratif reconstruit à partir des identifiants GADM et du nom de niveau 2 | 485 lignes, toutes de niveau 2, 6 restant ambiguës |
| Unités de niveau 2 absentes de GADM, signalées et tenues à l'écart de la sélection par cellule | 491 lignes `HarvestStat` |
| Lignes écartées par la règle d'une ligne par cellule | Aucune |
| Rendements hors des bornes de plausibilité, rendements nuls compris | 4 658 |
| Hiérarchie GADM incohérente, non corrigeable sans les polygones | 488 lignes du Ghana |

### 4.3 Fichier `survey`

| Correction | Lignes concernées |
|---|---:|
| Suppression des copies exactes | 448 |
| Libellé `Cote dIvoire` aligné sur `Côte dIvoire` | Toutes les lignes ivoiriennes |
| Année de fin de campagne déduite de l'année de début | 218 |
| Part de culture supérieure à 100, signalée | 80 |
| Surface supérieure à 1 000 ha, signalée | 1 |
| Surface GPS strictement égale à la surface déclarée, signalée | 7 403 |
| Identifiant de ménage tronqué, signalé et remplacé par une valeur manquante | 3 416 |
| Latitude et longitude nulles, signalées et remplacées par des valeurs manquantes | 518 |
| Hiérarchie GADM incohérente | 10 |
| Cible hors des bornes de plausibilité | 737 |

Des identifiants de ligne, de ménage et de grappe spatiale sont créés pour permettre les partitions par groupe.

### 4.4 Fichier `cropcut`

| Correction | Lignes concernées |
|---|---:|
| Ménage reconstruit par division entière de `holder_id` par 100 | 8 440, soit 2 338 ménages |
| Poids sec supérieur au poids frais, signalé | 80 |
| Date de mesure impossible dans le calendrier éthiopien, signalée | 19 |
| Cible hors des bornes de plausibilité | 2 |

Un identifiant de mesure `id_mesure` est formé de la source et de la position dans le fichier brut, selon la convention d'`id_ligne` dans `survey`. Aucune combinaison des colonnes d'origine n'identifie une mesure, et la vague de 2018 n'a pas d'identifiant d'exploitant. Cet identifiant a été ajouté le 4 novembre 2026, sans modifier les autres jeux.

## 5. Jeux produits

Les jeux sont écrits au format CSV compressé dans `data/processed`. Ce dossier est exclu du dépôt git, car son contenu se reproduit entièrement à partir des données brutes et du code.

| Jeu | Lignes | Contenu |
|---|---:|---|
| `regional_prepare` | 197 535 | Fichier corrigé avec l'ensemble de ses indicateurs |
| `regional_modelisation` | 145 877 | Niveaux 1 et 2, une ligne par cellule, rendement renseigné et plausible. 45 pays, 33 cultures, période 1960 à 2023 |
| `survey_prepare` | 194 704 | Fichier corrigé avec l'ensemble de ses indicateurs |
| `survey_modelisation` | 151 138 | Cible GPS renseignée et plausible. 12 pays, 25 cultures, période 2005 à 2022 |
| `cropcut_prepare` | 11 345 | Fichier corrigé avec l'ensemble de ses indicateurs |
| `cropcut_validation` | 11 263 | Mesures cohérentes et plausibles |
| `bornes_plausibilite` | 34 | Bornes basse et haute par culture |

`HarvestStat` représente 81 % de `regional_modelisation`. Djibouti et la Guinée équatoriale en sont absents, car ils ne disposent que de données nationales.

## 6. Contrôles

Le notebook de référence vérifie les propriétés suivantes et s'interrompt si l'une d'elles n'est pas satisfaite.

- Aucun rendement négatif ne subsiste dans `regional`.
- Chaque code pays ne porte qu'un seul nom.
- Le jeu de modélisation de `regional` ne contient qu'une ligne par cellule.
- L'identifiant de ligne de `survey` est unique et aucune copie exacte ne subsiste.
- Les cibles sont renseignées dans les trois jeux finaux.
- Les tableaux bruts ne sont pas modifiés par la préparation.

## 7. Limites et points ouverts

### 7.1 Choix de la cible de `survey`

**Constat**

`YieldUsingGPS_ton_ha_` est absente pour l'ensemble du Burkina Faso et quasi absente pour le Bénin, avec 69 lignes contre 3 834 pour la cible fondée sur la surface déclarée. Elle est réduite de moitié pour la Côte d'Ivoire. Sur les 117 719 parcelles qui disposent des deux rendements, le rapport médian entre le rendement fondé sur la surface déclarée et le rendement GPS vaut 0,994, mais les deux valeurs diffèrent de plus de 50 % pour 43,8 % des parcelles. Cette part varie de 22,9 % au Togo à 69,1 % en Guinée-Bissau.

**Analyse**

Recourir à `Yield_ton_ha_` lorsque la surface GPS manque introduirait un bruit de mesure considérable dans la cible. Ce bruit serait entièrement confondu avec le pays dans le cas du Burkina Faso, qui ne dispose que de la surface déclarée, si bien qu'un indicateur de méthode ne permettrait pas de séparer l'effet de la méthode de celui du pays. Le Burkina Faso et le Bénin restent par ailleurs couverts par `regional_modelisation`, avec respectivement 15 327 et 19 751 lignes.

**Décision**

La cible `YieldUsingGPS_ton_ha_` est maintenue sans remplacement. Ce choix a été arrêté le 3 novembre 2026 sur délégation du porteur du projet. `Yield_ton_ha_` reste disponible dans `survey_prepare` pour des analyses de sensibilité. Le modèle à l'échelle de la parcelle couvre 12 pays, et son application au Burkina Faso relèverait d'une extrapolation hors du domaine d'entraînement.

### 7.2 Autres limites

- **Surfaces GPS recopiées.** 7 403 surfaces GPS sont strictement égales à la surface déclarée, dont 43,6 % des parcelles de `LSMS_TGO2021` dans le jeu de modélisation. Une telle égalité est improbable entre deux mesures indépendantes et suggère une reprise de la surface déclarée en l'absence de mesure GPS. Ces lignes sont signalées sans être écartées, et leur effet devra être mesuré lors de l'évaluation.
- **Unités hors GADM.** 491 lignes `HarvestStat` décrivent 18 unités de niveau 2 créées après la carte GADM, comme les départements nigériens de 2011, les zones éthiopiennes Buno Bedele et Southeast Tigray ou trois districts ougandais. Elles portent l'identifiant de l'unité qui les contenait, et les départements de Tibiri, Falmey et Dioudiou, situés dans la région de Dosso, portent celui de la région de Diffa. Ces lignes sont exclues du jeu de modélisation, car elles ne peuvent recevoir ni zone propre ni contour.
- **Correction du 3 novembre 2026.** Avant l'introduction de `flag_unite_hors_gadm`, ces unités partageaient la zone de leur unité mère et la règle d'une ligne par cellule écartait 182 lignes, dont 105 rendements régionaux `FAO_subnational` d'Oromia et du Tigray remplacés par le rendement d'une seule zone. Leur exclusion retire 383 lignes du jeu de modélisation et y restaure 110 rendements. Aucune autre ligne n'est concernée par la règle d'une ligne par cellule.
- **Hiérarchie du Ghana.** 488 lignes conservent un identifiant de niveau 2 rattaché à plusieurs régions. Leur correction nécessite les polygones GADM.
- **Lignes inexpliquées.** 1 710 lignes de `regional` ne vérifient aucune relation entre production, surface et rendement. Elles restent dans le jeu de modélisation lorsque leur rendement est plausible.
- **Saisons.** Seule l'équivalence entre Meher et Main est établie. Les autres libellés de saison sont conservés tels quels, faute de preuve de leur équivalence.
- **Coordonnées nulles.** 518 lignes de `survey`, dont 135 du jeu de modélisation, sont placées au point de latitude et de longitude nulles, situé en mer dans le golfe de Guinée. Elles proviennent des sources `LSMS_TZA2008`, `LSMS_UGA2011`, `LSMS_MWI2019`, `LSMS_MLI2018`, `LSMS_TZA2012` et `LSMS_ETH2011` et n'ont aucun identifiant administratif. Ce point code une position absente. Avant sa correction du 4 novembre 2026, il formait dans chaque pays une grappe fictive qui reliait des ménages sans lien entre eux, et le plus grand groupe de la partition comptait 456 parcelles au lieu de 253. La correction déplace 332 lignes d'une partition à une autre.
- **Identifiants de ménage.** L'identifiant est manquant pour la vague `ETH2018` de `cropcut` et pour 6 106 lignes du jeu de modélisation de `survey`. La grappe spatiale sert alors de groupe de repli.

## 8. Reproductibilité

- Les tests s'exécutent depuis la racine du projet avec la commande `python -m unittest discover -s tests -t .`.
- La préparation complète s'exécute avec la commande `python -m src.data.prepare`, ou par le notebook de référence.
- La première exécution lit les fichiers Excel en une dizaine de minutes et alimente le cache. Les exécutions suivantes durent environ deux minutes, l'essentiel étant consacré à l'écriture des fichiers compressés.

## 9. Suite du pipeline

La troisième condition de la décision issue du Data Understanding est remplie par le protocole d'évaluation décrit dans `docs/evaluation_protocol.md`. Ce protocole fixe des partitions par groupe et par période, une validation externe sur `cropcut` et des scores de référence que tout modèle devra dépasser.
