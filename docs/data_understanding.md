# Rapport de Data Understanding des données GROW-Africa

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

## 5. Qualité des données

| Domaine | Anomalie | Ampleur | Traitement prévu |
|---|---|---|---|
| Identifiants | `holder_id` de 16 chiffres tronqués par la limite de 15 chiffres significatifs d'Excel | 415 lignes de `LSMS_cropcut` | Reconstruire le ménage par `holder_id // 100` |
| Identifiants | `household_id` remplacé par deux valeurs de substitution | 82 lignes de `ETH2011` | Ignorer `household_id` au profit de la reconstruction |
| Identifiants | `hhid` stocké en notation scientifique et tronqué | 3 417 lignes de `LSMS_ETH2018`, 251 valeurs distinctes | Regroupement géographique de repli |
| Identifiants | Aucune clé unique dans `LSMS_survey` | 14 434 doublons sur la clé la plus complète | Créer un identifiant technique de ligne |
| Valeurs manquantes déguisées | Texte `[]` dans les identifiants GADM et `QC_flag_Y` | 142 lignes de `LSMS_survey`, 108 de `Point`, 36 et 706 de `Regional` | Convertir en valeurs manquantes |
| Valeurs manquantes déguisées | Texte `none` dans `admin_1`, `admin_2` et `crop_production_system` | 11 884, 75 389 et 57 325 lignes de `Regional` | Convertir en valeurs manquantes |
| Encodage | Caractère invisible BOM en tête de `L1_GID` | 318 lignes du Lesotho | Nettoyer avant toute jointure |
| Référentiel géographique | 25 `L0_GID` pour le Ghana et hiérarchie L1 et L2 incohérente | 3 890 et 488 lignes concernées | Reconstruire les identifiants du Ghana depuis GADM |
| Référentiel géographique | `country_code` mêlant ISO2 et ISO3, libellés de pays doublonnés | 82 codes pour 49 libellés et 47 pays | Utiliser `L0_GID` corrigé comme clé pays |
| Coordonnées | Latitude et longitude inversées | 215 lignes de `Niche_trial` | Permuter les deux valeurs |
| Coordonnées | Latitude de signe erroné | 30 lignes de `Corbeels2020` | Corriger le signe |
| Coordonnées | Point situé hors d'Afrique | 1 ligne de `OneAcre_survey` | Invalider la coordonnée |
| Dates | Calendrier éthiopien probable, aucun jour 31 et 116 dates au 30 février | 11 341 dates de `LSMS_cropcut` | Aucune conversion grégorienne directe |
| Dates | Récolte antérieure à la plantation | 684 couples sur 58 744 dans `Point` | Signaler ces lignes |
| Mesures | Poids sec supérieur au poids frais, dont 4 poids frais nuls | 80 lignes de `LSMS_cropcut` | Signaler et tester l'exclusion |
| Mesures | Surface déclarée de 5,99 milliards d'hectares | 1 ligne de `LSMS_GNB2021` | Invalider la valeur |
| Mesures | `prcCrop` supérieur à 100 | 80 lignes de `LSMS_MWI2019` | Invalider la valeur |
| Doublons | Copies exactes | 448 lignes de `LSMS_survey` et 1 282 de `Point`, dont 19,3 % de `Corbeels2020` | Supprimer ou regrouper selon une règle documentée |
| Doublons | Deux unités `admin_2` rattachées au même `L2_GID` | 65 lignes de `HarvestStat` | Retenir une ligne par cellule |
| Valeurs impossibles | Rendements atteignant 6 996 t/ha | 3 475 rendements supérieurs à 20 t/ha dans `Regional` | Bornes de plausibilité par culture |

## 6. Distribution des rendements

| Fichier | Rendements positifs | Médiane t/ha | Moyenne t/ha | 99e percentile | Maximum | Asymétrie | Asymétrie du logarithme |
|---|---:|---:|---:|---:|---:|---:|---:|
| `LSMS_cropcut` | 11 345 | 0,86 | 1,13 | 4,47 | 10,75 | 2,14 | -0,27 |
| `LSMS_survey` | 158 478 | 0,74 | 1,50 | 11,50 | 155,68 | 9,97 | 0,20 |
| `Point` | 131 812 | 1,73 | 2,55 | 11,46 | 150,00 | 13,83 | -0,27 |
| `Regional` | 162 439 | 1,00 | 3,29 | 28,28 | 6 996,21 | 192,23 | 0,29 |

- Les distributions sont fortement asymétriques à droite et deviennent approximativement log-normales après transformation logarithmique.
- L'échelle dépend fortement de la culture. Les tubercules et la banane présentent des rendements médians de 2 à 9 t/ha selon le fichier, contre 0,2 à 2,9 t/ha pour les céréales et les légumineuses.
- Les comparaisons globales entre fichiers sont trompeuses. `LSMS_survey` est globalement inférieur à `LSMS_cropcut`, alors qu'il lui est supérieur à zone, culture et année identiques en Éthiopie. La composition en pays, en cultures et en périodes explique cette inversion.

## 7. Structure temporelle et spatiale

### 7.1 Définition de l'année

| Fichier | Colonne de référence | Signification vérifiée |
|---|---|---|
| `LSMS_cropcut` | `Year` | Année de fin de campagne, égale à `AgYearEnd` de la vague `LSMS_survey` correspondante |
| `LSMS_survey` | `AgYearStart` et `AgYearEnd` | Début et fin de campagne, toujours séparés d'un an |
| `Point` | `HarvestYear` | Année de récolte, absente pour toute la source `CEEPA_time_avg` |
| `Regional` | `harvest_year` | Année de récolte |

Une variable unique `annee_recolte` sera construite à partir de `AgYearEnd` pour `LSMS_survey` et de `Year` pour `LSMS_cropcut`. Le libellé des vagues d'enquête ne constitue pas une source fiable de l'année.

### 7.2 Liens entre année et source

Dans `Point` et `Regional`, les sources se succèdent dans le temps. `AgroMAPS` s'arrête en 2002, `RCeA` couvre 2001 à 2019, `Corbeels2020` couvre 1974 à 2017 et `OneAcre_survey` 2015 à 2020. Un effet temporel appris par un modèle pourrait donc refléter un changement de source et de méthode de mesure.

### 7.3 Dépendances entre observations

- Les observations sont regroupées en grappes spatiales. La médiane est de 19 lignes par coordonnée dans `LSMS_cropcut` et de 11 dans `LSMS_survey`, avec un maximum de 519.
- `LSMS_cropcut` est un panel. 914 exploitants sont observés sur deux vagues et 527 sur trois.
- Dans `LSMS_survey`, une part importante des identifiants de ménage réapparaît d'une vague à l'autre en Éthiopie, en Ouganda, au Niger, au Togo et au Bénin.
- Les coordonnées LSMS sont volontairement déplacées de 0 à 5 km en zone rurale selon l'article.

## 8. Biais de mesure et représentativité

### 8.1 Surface déclarée et surface mesurée par GPS

59,8 % des surfaces déclarées tombent sur un multiple d'un quart d'acre, contre 4,3 % des surfaces GPS. L'écart entre les deux mesures dépend de la taille de la parcelle.

| Surface GPS | Parcelles | Rapport médian entre surface déclarée et surface GPS | Rendement médian fondé sur la surface GPS |
|---|---:|---:|---:|
| Jusqu'à 0,1 ha | 21 009 | 1,67 | 1,73 t/ha |
| De 0,1 à 0,4 ha | 53 769 | 1,16 | 0,92 t/ha |
| De 0,4 à 2 ha | 49 310 | 0,93 | 0,56 t/ha |
| Au-delà de 2 ha | 8 985 | 0,81 | 0,34 t/ha |

Les agriculteurs surestiment les petites parcelles et sous-estiment les grandes, ce qui concorde avec l'article. La relation inverse entre surface et rendement combine un effet agronomique possible et une erreur de mesure placée au dénominateur. Les données ne permettent pas de séparer ces deux effets.

### 8.2 Écart entre sources en Éthiopie

À zone `L2_GID`, culture et année identiques, avec au moins 10 observations de part et d'autre, les rendements de `LSMS_survey` dépassent ceux de `LSMS_cropcut` dans 69,8 % des cellules, pour un rapport médian de 1,46. Les statistiques officielles de `Regional` les dépassent dans 88,7 à 90,1 % des cellules, pour un rapport médian de 1,78 à 1,88.

Le sens de l'écart concorde avec l'article. Son ampleur est supérieure aux biais publiés de 20 % et de 32 %, car la comparaison ne pondère pas les cellules et mélange saisons et sources. Ces chiffres établissent le sens de l'écart sans en constituer une estimation.

### 8.3 Désaccord entre sources officielles

Sur les 105 cellules communes à `FAO_subnational` et `HarvestStat`, l'écart relatif médian atteint 17,5 %. Cet ordre de grandeur représente le bruit irréductible de la cible `Regional`. Un modèle dont l'erreur relative serait nettement inférieure devrait faire l'objet d'une recherche de fuite.

### 8.4 Représentativité

- Le Malawi représente 26,9 % de `LSMS_survey`. Le Rwanda, le Kenya et le Burundi représentent ensemble 66 % de `Point`.
- `OneAcre_survey` représente 59 % de `Point` et `HarvestStat` 67 % de `Regional`.
- Le maïs représente 51,7 % de `Point` et 33 % de `LSMS_survey`.
- `LSMS_cropcut`, seule source de mesures directes, ne couvre que l'Éthiopie.

## 9. Implications pour les phases suivantes

### 9.1 Data Preparation

1. Normaliser les chaînes de caractères en convertissant `[]`, `none` et le BOM avant tout calcul.
2. Remplacer les codes -999 et -99 par des valeurs manquantes et invalider les rendements négatifs.
3. Permuter `areaHa` et `productionTon` sur les 33 740 lignes identifiées dans `Regional`.
4. Corriger les identifiants du Ghana, utiliser `L0_GID` comme clé pays et reconstruire `level` lorsque les GID le permettent.
5. Corriger les coordonnées inversées ou de signe erroné et invalider le point hors d'Afrique.
6. Reconstruire l'identifiant de ménage de `LSMS_cropcut` par `holder_id // 100` et créer un identifiant technique de ligne pour `LSMS_survey`.
7. Harmoniser l'année de référence entre les fichiers.
8. Appliquer des bornes de plausibilité par culture fondées sur le filtre des auteurs.
9. Traiter les doublons exacts et retenir une ligne par cellule dans `Regional` selon une règle de priorité documentée.
10. Signaler les lignes incohérentes plutôt que de les corriger par imputation.

Ces traitements seront implémentés sous forme de fonctions testées dans `src/` et appliqués à une copie des données brutes.

### 9.2 Feature Engineering

- Exclure toutes les variables qui entrent dans le calcul de la cible, à savoir les poids, productions, surfaces et `prcCrop`, ainsi que les variantes de rendement non retenues.
- Exclure les dates de récolte, connues seulement après la récolte.
- Ne pas utiliser les indicateurs `QC_flag_*` comme prédicteurs.
- Les fichiers ne contiennent aucune variable climatique, pédologique ou relative aux pratiques culturales. Les prédicteurs admissibles se limitent à la culture, au lieu, à l'année et à la source. Des covariables externes, climatiques et issues de la télédétection, seront nécessaires pour obtenir une performance utile.

### 9.3 Modélisation

- Modéliser le logarithme du rendement ou utiliser une fonction de perte robuste.
- Intégrer la culture comme prédicteur indispensable et regrouper les cultures de moins de 100 lignes.
- Ne pas fusionner les fichiers sans variable de type de source ni correction de biais.

### 9.4 Évaluation

- Construire les partitions par ménage, par grappe ou région et par période, jamais par tirage aléatoire des lignes.
- Vérifier que les sources du jeu de test sont représentées dans le jeu d'entraînement.
- Ventiler les métriques par culture, par type de source et par classe de surface.
- Utiliser l'écart de 17,5 % entre sources officielles comme repère de l'erreur atteignable sur `Regional`.

## 10. Limites de l'analyse

- **Bornes du filtre des auteurs.** Les seuils exacts ne sont pas publiés et ont été reconstruits. La correspondance de 96,48 % constitue une forte présomption et non une preuve formelle.
- **Absence des polygones GADM.** La cohérence spatiale a été évaluée au moyen de signatures d'erreur et d'un cadre géographique approximatif. Une jointure spatiale reste nécessaire pour valider chaque point.
- **Calendrier éthiopien.** L'hypothèse repose sur des régularités statistiques et sur une connaissance externe du calendrier agricole. Elle doit être confirmée dans la documentation de l'enquête ESS.
- **Comparaisons entre sources.** Les rapports présentés reposent sur des cellules d'au moins 10 observations, sans pondération. Ils établissent le sens des écarts sans en estimer l'ampleur.
- **Variables non documentées.** `prcLeft`, `season_name` et `crop_production_system` ne disposent d'aucune définition officielle.

## 11. Décision

**Go pour la phase de Data Preparation**, sous trois conditions.

1. Les fichiers sont traités séparément. Aucune fusion n'intervient tant que la question des biais entre sources n'est pas tranchée.
2. Les traitements de la section 9.1 sont implémentés sous forme de fonctions testées et appliqués à une copie des données brutes.
3. Le protocole d'évaluation de la section 9.4 est arrêté avant l'entraînement du premier modèle.

**Choix de la cible, validé par le porteur du projet le 2 novembre 2026**

| Usage | Cible retenue | Justification |
|---|---|---|
| Généralisation spatiale et temporelle | `yieldTonHa` de `Regional`, niveaux 1 et 2 | Couverture de 47 pays sur la période 1960 à 2023 |
| Prédiction à l'échelle de la parcelle | `YieldUsingGPS_ton_ha_` de `LSMS_survey` | Surface mesurée de manière objective |
| Validation | `Yield_ton_ha_` de `LSMS_cropcut` | Mesure directe de référence, limitée à l'Éthiopie |

## 12. Reproductibilité

- Environnement d'exécution Python 3.12.13, pandas 3.0.6, numpy 2.5.3 et matplotlib 3.11.2.
- Le notebook s'exécute de bout en bout à partir des fichiers bruts de `data/raw/`, sans état préalable, avec la commande `jupyter nbconvert --to notebook --execute notebooks/02_data_understanding.ipynb`.
- La lecture des quatre fichiers Excel dure environ onze minutes. Les analyses suivantes s'exécutent en quelques secondes.
- Les empreintes SHA-256 de la section 3.1 permettent de vérifier que les fichiers utilisés sont identiques à ceux de l'analyse.

## 13. Questions ouvertes

| Question | Source de vérification envisagée |
|---|---|
| Définition de `prcLeft`, `season_name` et `crop_production_system` | Documentation GROW-Africa et sources primaires |
| Nomenclature des indicateurs `QC_flag_*` | Documentation FAOSTAT |
| Calendrier utilisé pour `cropCutDay` et `cropCutMonth` | Questionnaires de l'enquête éthiopienne ESS |
| Conversions d'unités des vagues LSMS 2021 non conformes à la formule du rendement | Documentation LSMS-ISA |
| Définition de `YieldEst2_ton_ha_` en Tanzanie | Documentation LSMS-ISA |
| Relation entre `CEEPA_time_avg` et `CEEPA_annual` | Documentation CEEPA |
| Origine des 1 710 lignes de `Regional` qui ne vérifient aucune relation entre production, surface et rendement | Sources `RCeA` et `FAOSTAT` |
| Version de GADM utilisée pour les identifiants géographiques | Auteurs de GROW-Africa |
