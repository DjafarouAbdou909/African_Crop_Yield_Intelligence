# Rapport de Data Understanding — GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 2 Data Understanding |
| Notebook de référence | `notebooks/02_data_understanding.ipynb` |
| Documents associés | `docs/data_dictionary.md` et `docs/data_audit_report.md` |
| Statut | Phase terminée. Go pour la Data Preparation sous conditions |

## 1. Objet du document

Ce rapport synthétise les résultats de la phase de Data Understanding menée sur la base GROW-Africa. Il présente la structure des données, la définition des cibles, les anomalies détectées, les biais identifiés et leurs conséquences pour les phases suivantes du pipeline.

Chaque résultat chiffré est reproduit par une cellule du notebook de référence. Le rapport distingue les faits mesurés dans les fichiers des interprétations proposées, et précise pour chaque interprétation son niveau de preuve.

## 2. Démarche suivie

### 2.1 Correspondance avec les tâches CRISP-DM

| Tâche CRISP-DM | Travaux réalisés | Sections du notebook |
|---|---|---|
| Collecte initiale des données | Chargement des quatre fichiers, empreintes SHA-256, réconciliation des effectifs avec l'article | Section 1 |
| Description des données | Dimensions, types, granularité, identifiants, couverture temporelle et géographique | Sections 2, 5 et 6 |
| Exploration des données | Dérivation des cibles, distributions, relations entre variables, comparaisons entre sources | Sections 3, 4 et 7 |
| Vérification de la qualité | Valeurs manquantes, doublons, codes spéciaux, incohérences, valeurs impossibles | Sections 2 à 7 |
| Synthèse et décision | Registre des constats, limites, décision et recommandation de cible | Section 8 |

### 2.2 Règles de preuve

- Chaque affirmation repose sur un calcul reproductible exécuté sur les fichiers bruts.
- Un constat désigne un fait mesuré. Une analyse désigne une explication proposée, accompagnée de son niveau de preuve.
- Les hypothèses qui reposent sur une connaissance externe aux données sont signalées comme telles et restent à confirmer.
- Les données brutes ne sont jamais modifiées. Les corrections identifiées sont décrites ici et seront implémentées lors de la Data Preparation.

## 3. Données analysées

### 3.1 Traçabilité des fichiers

Chaque fichier contient une feuille unique nommée `Sheet1`. Les empreintes suivantes identifient la version exacte analysée.

| Fichier | Lignes | Colonnes | Empreinte SHA-256 |
|---|---:|---:|---|
| `GROW-Africa_LSMS_cropcut.xlsx` | 11 345 | 20 | `ff7b8e1c4307b1b9eaa83937d8462465594f346a2984616911f95ccae8a376d4` |
| `GROW-Africa_LSMS_survey.xlsx` | 195 152 | 27 | `011a7439e5ce5bf0f10b150f2cacace2a96987b8c46206e65f1d4e40f12be75d` |
| `GROW-Africa_Point.xlsx` | 131 812 | 17 | `18e226b799fcfa732a11886c9e3b6fbe8cc993fed8dd80ee433466a92271a0c1` |
| `GROW-Africa_Regional.xlsx` | 197 535 | 25 | `15e92a193e113cf24e52c52dc4f512a55b575e3b75a1c1e134556256784f352f` |

### 3.2 Réconciliation avec l'article

- Le total des quatre fichiers atteint exactement les 535 844 observations publiées.
- `Regional` correspond exactement aux 11 884 lignes nationales et aux 185 651 lignes infranationales de l'article. Les 11 884 lignes de niveau 0 sont les lignes `FAOSTAT`.
- Les 143 157 autres données locales de l'article correspondent à la somme de `Point` et de `LSMS_cropcut`. L'effectif attendu de `Point` est donc de 131 812 lignes et non de 143 157.

### 3.3 Profil des fichiers

| Fichier | Nature des données | Granularité | Période | Pays | Cultures | Cible |
|---|---|---|---|---:|---:|---|
| `LSMS_cropcut` | Mesures directes de récolte sur 16 m² | Exploitant, parcelle, champ, année et culture | 2012 à 2019 | 1 | 12 | `Yield_ton_ha_` |
| `LSMS_survey` | Enquêtes LSMS-ISA auprès des ménages | Parcelle et culture, sans clé unique | 2005 à 2022 | 13 | 25 | `Yield_ton_ha_` et variantes |
| `Point` | Essais, enquêtes et méta-analyses | Site ou exploitation et culture | 1974 à 2021 | 21 | 24 | `Yield_ton_ha_` |
| `Regional` | Statistiques officielles nationales et infranationales | Unité administrative, culture, saison et année | 1960 à 2023 | 47 | 34 | `yieldTonHa` |

Les taux globaux de cellules manquantes sont de 3,98 % pour `LSMS_cropcut`, 16,65 % pour `LSMS_survey`, 23,45 % pour `Point` et 13,12 % pour `Regional`. Ces taux sont légèrement sous-estimés, car certaines valeurs manquantes sont déguisées en texte.

## 4. Cibles et risques de fuite

### 4.1 Construction des rendements

| Fichier | Cible | Relation vérifiée | Part des lignes conformes | Variables exclues pour fuite |
|---|---|---|---:|---|
| `LSMS_cropcut` | `Yield_ton_ha_` | 0,625 fois `dryWeightKg`, soit 1 kg récolté sur 16 m² converti en t/ha | 100 % | `dryWeightKg`, `freshWeightKg` |
| `LSMS_survey` | `Yield_ton_ha_` | `Prod_kg_` divisé par `ReportedArea_ha_` et par la part `prcCrop`, converti en tonnes | 99,10 % | `Prod_kg_`, `ReportedArea_ha_`, `prcCrop` |
| `LSMS_survey` | `YieldUsingGPS_ton_ha_` | Même construction avec `GPSArea_ha_` | 99,37 % | `GPSArea_ha_` |
| `LSMS_survey` | `YieldEst2_ton_ha_` et `YieldEst2UsingGPS_ton_ha_` | Même construction avec `ProdEst2_kg_` | 99,72 % et 99,66 % | `ProdEst2_kg_` |
| `Regional` | `yieldTonHa` | `productionTon` divisé par `areaHa`, ou rapport inverse sur les lignes permutées | 126 696 et 33 740 lignes | `areaHa`, `productionTon` |

Les quatre variantes de rendement de `LSMS_survey` mesurent la même grandeur. Une seule sera retenue comme cible et les autres seront exclues des prédicteurs. `YieldEst2_ton_ha_` est en outre renseigné sans `ProdEst2_kg_` sur 24 066 lignes tanzaniennes, ce qui rend sa définition hétérogène.

### 4.2 Cible manquante non aléatoire dans `LSMS_survey`

Parmi les 10 550 lignes dont le rendement est absent mais calculable, 96,48 % ont une valeur recalculée située hors des bornes du filtre décrit par les auteurs. Ce filtre écarte les rendements inférieurs à 10 % de la médiane ou supérieurs à 200 % du 98e percentile de la distribution régionale de chaque culture. Seuls 0,73 % des rendements publiés sortent de ces bornes.

Les valeurs manquantes de la cible résultent donc principalement de ce filtrage et relèvent d'un mécanisme MNAR. La distribution publiée est tronquée. Ces lignes ne seront ni imputées ni recalculées.

### 4.3 Colonnes permutées dans `Regional`

Pour 33 740 lignes, soit 17,1 % du fichier, `yieldTonHa` est égal à `areaHa` divisé par `productionTon`. Dans ce groupe, le rendement médian du manioc atteint 9,98 t/ha, comparable aux 8,41 t/ha du groupe conforme, alors que le rapport entre production et surface donnerait 0,10 t/ha. Le rendement est donc plausible et ce sont les colonnes `areaHa` et `productionTon` qui sont permutées.

| Source | Lignes permutées | Lignes conformes |
|---|---:|---:|
| `HarvestStat` | 25 631 | 96 792 |
| `RCeA` | 3 262 | 5 786 |
| `FAO_subnational` | 3 233 | 3 736 |
| `AgroMAPS` | 1 579 | 9 268 |
| `USAID_KadunaState` | 35 | 39 |
| `FAOSTAT` | 0 | 11 075 |

1 710 lignes ne vérifient aucune des deux relations, dont 1 623 issues de `RCeA` et 87 de `FAOSTAT`. Elles restent inexpliquées.

### 4.4 Codes spéciaux dans `Regional`

Le code -999 apparaît uniquement dans `AgroMAPS` et le code -99 uniquement dans `RCeA`. Ces codes ont été intégrés au calcul du rendement et ont produit 30 rendements négatifs, tels que -0,01001 qui correspond à -10 divisé par 999. La préparation devra convertir les codes en valeurs manquantes et invalider tout rendement négatif.
