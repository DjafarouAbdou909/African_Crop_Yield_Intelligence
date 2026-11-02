# Rapport de Data Preparation — GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 3 Data Preparation |
| Code | `src/data/` et `tests/` |
| Notebook de référence | `notebooks/03_data_preparation.ipynb` |
| Documents associés | `docs/data_understanding.md` et `docs/data_dictionary.md` |
| Statut | Préparation terminée. Choix de la cible de `survey` à confirmer |

## 1. Objet du document

Ce rapport décrit les corrections appliquées aux données GROW-Africa à la suite du Data Understanding, l'organisation du code qui les implémente, les jeux de données produits et les points qui restent ouverts avant la modélisation.

## 2. Périmètre et décisions

| Décision | Contenu | Origine |
|---|---|---|
| Fichiers préparés | `regional`, `survey` et `cropcut`, traités séparément | Première condition de la décision issue du Data Understanding |
| Fichier exclu | `point`, qui ne porte aucune des cibles retenues | Décision du porteur du projet |
| Cible principale | `yieldTonHa` de `regional` aux niveaux administratifs 1 et 2 | Choix validé le 2 novembre 2026 |
| Cible à l'échelle de la parcelle | `YieldUsingGPS_ton_ha_` de `survey` | Choix validé le 2 novembre 2026, à reconfirmer au vu de la section 7 |
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

Chaque fonction travaille sur une copie de son entrée. La suite de 25 tests unitaires de `tests/` vérifie chaque correction sur des cas construits pour l'occasion.

## 4. Corrections appliquées

### 4.1 Corrections communes

| Correction | Effet |
|---|---|
| Suppression du caractère invisible BOM et des espaces superflus | 318 identifiants `L1_GID` du Lesotho redeviennent exploitables |
| Conversion des jetons `[]` et `none` en valeurs manquantes | Les valeurs manquantes déguisées sont comptées comme telles |
| Bornes de plausibilité par culture | Calculées sur `regional` selon le filtre des auteurs, puis appliquées aux trois fichiers |

### 4.2 Fichier `regional`

| Correction | Lignes concernées |
|---|---:|
| Codes -999 et -99 convertis en valeurs manquantes, rendements négatifs dérivés invalidés | 66 rendements |
| Surface et production permutées sur les lignes inversées | 33 740 |
| Lignes ne vérifiant aucune relation entre production, surface et rendement, signalées | 1 710 |
| Codes pays du Ghana ramenés à `L0GHA086` | 71 codes deviennent 47 |
| Libellés de pays unifiés | 49 libellés deviennent 47 |
| Saison Meher harmonisée en Main dans une colonne `saison` | Saison principale éthiopienne |
| Niveau administratif reconstruit à partir des identifiants GADM | 485 lignes, 6 restant ambiguës |
| Lignes écartées par la règle d'une ligne par cellule | 182, dont 105 `FAO_subnational`, 73 `HarvestStat` et 4 `RCeA` |
| Rendements hors des bornes de plausibilité | 4 657 |
| Hiérarchie GADM incohérente, non corrigeable sans les polygones | 488 lignes du Ghana |

### 4.3 Fichier `survey`

| Correction | Lignes concernées |
|---|---:|
| Suppression des copies exactes | 448 |
| Libellé `Cote dIvoire` aligné sur `Côte dIvoire` | Toutes les lignes ivoiriennes |
| Année de fin de campagne déduite de l'année de début | 218 |
| Part de culture supérieure à 100, signalée | 80 |
| Surface supérieure à 1 000 ha, signalée | 1 |
| Identifiant de ménage tronqué, signalé et remplacé par une valeur manquante | 3 416 |
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
