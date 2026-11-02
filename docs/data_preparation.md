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

## 5. Jeux produits

Les jeux sont écrits au format CSV compressé dans `data/processed`. Ce dossier est exclu du dépôt git, car son contenu se reproduit entièrement à partir des données brutes et du code.

| Jeu | Lignes | Contenu |
|---|---:|---|
| `regional_prepare` | 197 535 | Fichier corrigé avec l'ensemble de ses indicateurs |
| `regional_modelisation` | 146 151 | Niveaux 1 et 2, une ligne par cellule, rendement renseigné et plausible. 45 pays, 34 cultures, période 1960 à 2023 |
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

- **Couverture de la cible GPS.** `YieldUsingGPS_ton_ha_` est absente pour l'ensemble du Burkina Faso et quasi absente pour le Bénin, avec 69 lignes contre 3 834 pour la cible fondée sur la surface déclarée. Elle est réduite de moitié pour la Côte d'Ivoire. Le maintien de cette cible, ou le recours à `Yield_ton_ha_` lorsque la surface GPS manque avec un indicateur de méthode de mesure, doit être confirmé par le porteur du projet.
- **Hiérarchie du Ghana.** 488 lignes conservent un identifiant de niveau 2 rattaché à plusieurs régions. Leur correction nécessite les polygones GADM.
- **Lignes inexpliquées.** 1 710 lignes de `regional` ne vérifient aucune relation entre production, surface et rendement. Elles restent dans le jeu de modélisation lorsque leur rendement est plausible.
- **Saisons.** Seule l'équivalence entre Meher et Main est établie. Les autres libellés de saison sont conservés tels quels, faute de preuve de leur équivalence.
- **Identifiants de ménage.** L'identifiant est manquant pour la vague `ETH2018` de `cropcut` et pour 6 106 lignes du jeu de modélisation de `survey`. La grappe spatiale sert alors de groupe de repli.

## 8. Reproductibilité

- Les tests s'exécutent depuis la racine du projet avec la commande `python -m unittest discover -s tests -t .`.
- La préparation complète s'exécute avec la commande `python -m src.data.prepare`, ou par le notebook de référence.
- La première exécution lit les fichiers Excel en une dizaine de minutes et alimente le cache. Les exécutions suivantes durent environ deux minutes, l'essentiel étant consacré à l'écriture des fichiers compressés.

## 9. Suite du pipeline

La troisième condition de la décision issue du Data Understanding reste à remplir. Le protocole d'évaluation doit être défini avant l'entraînement du premier modèle, avec des partitions par ménage ou par grappe pour `survey`, par zone géographique et par période pour `regional`, et une évaluation ventilée par culture et par source.
