## Audit des données — Data Understanding

### Objectif

Cette étape vise à comprendre la structure, la signification, la provenance et la qualité des données du projet **African Crop Yield Intelligence**, conformément à la phase *Data Understanding* de la méthodologie CRISP-DM.

L’objectif est d’évaluer si les données sont suffisamment documentées, cohérentes et adaptées à l’objectif de prédiction du rendement agricole avant d’engager leur préparation pour la modélisation.

### Datasets étudiés

L’étude porte sur les quatre fichiers suivants issus de GROW-Africa :

- `GROW-Africa_LSMS_cropcut.csv`
- `GROW-Africa_LSMS_survey.csv`
- `GROW-Africa_Point.xlsx`
- `GROW-Africa_Regional.xlsx`

Source principale : [GROW-Africa — Zenodo](https://zenodo.org/records/14961637).

Article scientifique de référence : [GROW-Africa — Scientific Data](https://www.nature.com/articles/s41597-025-05257-5).

### Méthodologie commune d'audit

Chaque dataset est étudié selon une structure commune afin de faciliter la comparaison des résultats et de garantir la cohérence de la démarche.

#### 1. Inventaire et provenance

- Identifier le fichier, son format, son nombre de lignes et de colonnes.
- Examiner les sources de données, les pays, les cultures et les périodes représentés, selon les informations disponibles.
- Vérifier la version du fichier analysé et conserver les références nécessaires à sa traçabilité.

#### 2. Compréhension des colonnes

- Documenter la signification de chaque colonne.
- Identifier son type, son unité, ses modalités et son rôle potentiel.
- Distinguer les variables explicatives candidates, la variable cible, les identifiants, les métadonnées et les variables dont le rôle reste incertain.
- Consigner les définitions inconnues ou insuffisamment documentées dans le dictionnaire des données.

Les définitions ne sont pas considérées comme confirmées lorsqu'elles reposent uniquement sur le nom d'une colonne ou sur une interprétation plausible.

#### 3. Qualité et intégrité des données

Les contrôles portent notamment sur :

- les valeurs manquantes ;
- les doublons exacts et les doublons potentiels ;
- les types de données et les formats incohérents ;
- les valeurs négatives, nulles ou extrêmes ;
- la cohérence des dates, des unités et des identifiants ;
- la cohérence des relations entre les variables.

Les anomalies détectées sont documentées avant toute décision de correction ou de suppression.

#### 4. Analyse descriptive et structurelle

Lorsque les colonnes le permettent, l'étude examine la répartition des observations par source, pays, culture, année et niveau géographique.

Cette analyse permet de comprendre la composition du dataset, d'identifier les déséquilibres éventuels et de repérer les différences de couverture entre les sources.

#### 5. Relations entre variables et risques méthodologiques

Une attention particulière est accordée aux relations entre les variables de production agricole, notamment :

- la superficie cultivée ;
- la production récoltée ;
- le rendement agricole ;
- les variables pouvant être calculées à partir de la cible ;
- les identifiants et indicateurs susceptibles d'introduire une fuite de données ou une information indirecte sur la cible.

Le rôle de chaque variable doit être évalué en fonction de sa définition et du scénario de prédiction envisagé. Une variable liée mathématiquement au rendement n'est pas automatiquement retenue comme variable explicative.

#### 6. Traitements préalablement appliqués

La documentation de GROW-Africa mentionne notamment l'harmonisation des noms de cultures et des références géographiques, la suppression de doublons et le filtrage de certains rendements aberrants dans les données ponctuelles.

Ces traitements sont considérés comme des informations documentées par les auteurs. Leur effet sur les fichiers étudiés n'est considéré comme confirmé que lorsque les éléments disponibles permettent de le vérifier.

Le nettoyage préalable effectué par les auteurs ne dispense donc pas d'un audit complémentaire.

#### 7. Actions de suivi

Pour chaque dataset, les vérifications restantes sont consignées et priorisées.

Elles peuvent concerner :

- la recherche de documentation complémentaire ;
- la confirmation de la signification des colonnes ;
- l'investigation des valeurs suspectes ;
- l'analyse des valeurs manquantes selon leur source et leur contexte ;
- la vérification des relations entre les variables ;
- la définition de règles de validation reproductibles.

Les contrôles automatisés et les transformations définitives sont définis après clarification des règles applicables.

#### 8. Conclusion et décision provisoire

Chaque audit se termine par une synthèse des constats, des risques, des incertitudes et des actions nécessaires.

La décision provisoire est exprimée selon trois niveaux :

- **Go :** les éléments nécessaires à la poursuite de l'étape considérée sont suffisamment établis.
- **Go restreint :** l'étude peut continuer, mais certaines incertitudes ou certains risques doivent être résolus avant les étapes suivantes.
- **No-go :** un problème bloquant empêche de poursuivre l'étape concernée dans les conditions actuelles.

Ces décisions sont justifiées par les résultats de l'audit et ne signifient pas qu'un dataset est automatiquement prêt pour la modélisation.

### Principes de rigueur

L'audit repose sur les principes suivants :

- **Traçabilité :** conserver la provenance des données et la justification des décisions.
- **Reproductibilité :** privilégier des contrôles dont les résultats peuvent être vérifiés et reproduits.
- **Prudence :** ne pas supprimer, corriger ou imputer une valeur sans justification.
- **Documentation explicite :** distinguer les faits documentés, les constats observés, les hypothèses et les informations inconnues.
- **Prévention de la fuite de données :** ne pas sélectionner de variables explicatives avant d'avoir compris leur relation avec la cible et leur disponibilité au moment de la prédiction.
- **Séparation des responsabilités :** utiliser l'audit pour évaluer les données, le dictionnaire pour documenter les colonnes et l'étape de préparation pour appliquer les transformations justifiées.

### Synthèse globale

Les quatre datasets sont examinés selon le même cadre méthodologique, mais leurs résultats ne sont pas nécessairement comparables directement. Ils peuvent différer par leur source, leur niveau géographique, leur période, leurs méthodes de collecte et leurs variables disponibles.

Une synthèse globale sera établie après l'examen des quatre fichiers. Elle servira à évaluer leur compatibilité, les éventuelles redondances, les différences de couverture et les conditions nécessaires avant une éventuelle fusion.

**Décision générale :** aucune préparation définitive destinée à la modélisation ne sera engagée tant que les risques importants, les définitions essentielles et les conditions de validation n'auront pas été suffisamment clarifiés.


# Rapport d’audit des données — GROW-Africa

**Projet :** African Crop Yield Intelligence  
**Méthodologie :** CRISP-DM — Data Understanding  
**Statut :** Audit préliminaire des quatre datasets

## 1. Objectif de l’audit

L’objectif est de comprendre la structure, la provenance, la qualité et les limites des données GROW-Africa avant toute préparation destinée à la modélisation.

L’audit cherche notamment à :

- comprendre la signification des colonnes et leur rôle potentiel ;
- examiner les valeurs manquantes, les doublons et les incohérences ;
- vérifier les relations entre les variables ;
- identifier les risques de fuite de données (*data leakage*) ;
- distinguer les traitements documentés par les auteurs des constats observés dans les fichiers ;
- déterminer les vérifications nécessaires avant la préparation des données.

**Sources de référence :**

- Dataset : https://zenodo.org/records/14961637
- Article scientifique : https://www.nature.com/articles/s41597-025-05257-5

## 2. Traitements préalablement appliqués aux données

D’après la documentation de GROW-Africa, plusieurs traitements ont été appliqués avant la diffusion des données :

- harmonisation des noms de cultures ;
- suppression des doublons identifiés ;
- harmonisation des références géographiques et attribution d’identifiants administratifs ;
- filtrage de certains rendements aberrants dans les données ponctuelles, selon des seuils propres aux distributions régionales des cultures ;
- conservation des rendements aberrants dans les données nationales et infranationales.

Ces informations décrivent les traitements rapportés par les auteurs. Leur effet sur chaque fichier doit être distingué des contrôles réalisés dans le cadre de notre propre audit.

## 3. Dataset 1 — LSMS Crop Cut

**Fichier :** `GROW-Africa_LSMS_cropcut.csv`

### 3.1. Présentation

Ce fichier contient des observations de mesures directes de récolte (*crop cuts*) associées aux enquêtes LSMS. La documentation indique une couverture concernant l’Éthiopie et 12 cultures.

L’effectif de référence mentionné dans notre dictionnaire est de 11 345 observations. Cet effectif doit être confirmé sur la version exacte du fichier utilisée.

### 3.2. Constats préliminaires

| Observation | Risque ou question | Action prévue | Statut |
|---|---|---|---|
| `Yield_ton_ha_` semble dépendre de `dryWeightKg`. | Fuite de données potentielle si le poids sec intervient dans le calcul de la cible. | Vérifier la relation mathématique, son coefficient et ses exceptions. | À confirmer |
| L’année 2012 apparaît sous la forme `2,012`. | Incohérence de représentation et risque de conversion incorrecte. | Vérifier la valeur d’origine et documenter la normalisation sur une copie de travail. | À vérifier |
| Plusieurs colonnes contiennent des identifiants ou des codes. | Risque de redondance, de fuite indirecte ou de perte d’informations utiles au regroupement. | Examiner leur rôle avant toute exclusion du modèle. | À investiguer |

### 3.3. Risque de fuite de données

Une relation approximative a été relevée entre le rendement et le poids sec :

`Yield_ton_ha_ ≈ dryWeightKg × 0,6267`

Cette relation est un constat préliminaire et non une formule officiellement confirmée. Il reste à établir l’origine du coefficient, les observations concernées et les éventuelles exceptions.

Si `dryWeightKg` intervient directement dans le calcul de la cible, son utilisation comme variable explicative pourrait rendre l’évaluation artificiellement favorable lorsque cette mesure n’est pas disponible au moment de la prédiction.

Les identifiants doivent également être étudiés pour déterminer s’ils sont utiles à la traçabilité ou à la constitution des groupes d’entraînement et de test.

### 3.4. Actions de suivi

1. Confirmer les dimensions réelles du fichier et sa version.
2. Vérifier la relation entre le poids sec et le rendement.
3. Examiner les types, valeurs manquantes, doublons et plages de valeurs.
4. Clarifier les identifiants et les codes.
5. Vérifier les dates et les années agricoles.

**Décision provisoire :** poursuivre le Data Understanding. Aucune suppression définitive de colonne ni transformation irréversible n’est justifiée à ce stade.

## 4. Dataset 2 — LSMS Survey

**Fichier :** `GROW-Africa_LSMS_survey.csv`

### 4.1. Présentation

Les notes de travail indiquent un effectif de référence d’environ 195 152 observations, 27 colonnes, 13 pays et 25 cultures. Ces dimensions doivent être comparées à celles de la version effectivement utilisée.

Le fichier contient notamment des informations sur les cultures, la production, les superficies, les rendements, les coordonnées géographiques, les campagnes agricoles et les identifiants d’enquête.

### 4.2. Variables importantes à examiner

| Groupe | Colonnes concernées | Vérification nécessaire |
|---|---|---|
| Localisation | `GPS_lat`, `GPS_lon`, `L0_GID` à `L3_GID` | Qualité des coordonnées, identifiants géographiques et valeurs manquantes |
| Culture | `Crop` | Modalités et cohérence des noms de cultures |
| Production | `Prod_kg_`, `ProdEst2_kg_` | Définitions, unités et relation entre les deux mesures |
| Superficie | `ReportedArea_ha_`, `GPSArea_ha_` | Méthodes de mesure et différences éventuelles |
| Rendement | `Yield_ton_ha_`, `YieldUsingGPS_ton_ha_`, `YieldEst2_ton_ha_`, `YieldEst2UsingGPS_ton_ha_` | Origine des différentes estimations et choix de la cible |
| Calendrier agricole | `AgYearStart`, `AgYearEnd` | Signification des années et cohérence des campagnes |
| Provenance | `Source`, `Source1`, `Source2` | Définition des sources et relation entre les champs |
| Identifiants | `hhid`, `parcel_id`, `plotid` | Traçabilité, répétitions et regroupement des observations |
| Précision spatiale | `SpatialPrecision_km_` | Interprétation et prise en compte de l’incertitude géographique |
| Autres variables | `prcCrop`, `prcLeft` | Définition et modalités à confirmer |

### 4.3. Risque de fuite de données

Le fichier contient plusieurs variantes de production, de superficie et de rendement. Il est nécessaire d’établir comment chacune est calculée et dans quelles conditions elle est disponible.

Si une variable de production ou de superficie entre directement dans le calcul du rendement choisi comme cible, son utilisation comme prédicteur peut entraîner une fuite de données.

Les quatre colonnes de rendement ne doivent pas être considérées comme interchangeables sans justification. Le choix de la cible dépendra de leur définition, de leur qualité et du scénario de prédiction.

Les identifiants de ménage, de parcelle et de terrain doivent rester disponibles pour l’audit et les contrôles de partition, même s’ils sont finalement exclus des variables explicatives.

### 4.4. Actions de suivi

1. Confirmer les dimensions et les statistiques descriptives du fichier.
2. Documenter les variantes de production, de superficie et de rendement.
3. Vérifier les valeurs manquantes, les doublons et les incohérences.
4. Clarifier les champs de provenance et les variables encore inconnues.
5. Examiner les répétitions de ménages, de parcelles et de terrains.
6. Définir la cible et le scénario de prédiction avant de sélectionner les variables explicatives.

**Décision provisoire :** poursuivre le Data Understanding. La sélection de la cible et des prédicteurs reste conditionnée à la clarification des relations entre variables.

## 5. Dataset 3 — Point

**Fichier :** `GROW-Africa_Point.xlsx`

### 5.1. Inventaire du fichier examiné

| Contrôle | Résultat observé |
|---|---:|
| Nombre de lignes | 131 812 |
| Nombre de colonnes | 17 |
| Pays distincts | 21 |
| Cultures distinctes | 24 |
| Sources distinctes | 6 |
| Doublons exacts de lignes | 1 282 |

L’effectif observé de 131 812 lignes diffère de l’effectif de référence de 143 157 observations indiqué dans le dictionnaire. La version du fichier, la feuille examinée et les éventuels filtres doivent être vérifiés avant d’expliquer cet écart.

### 5.2. Répartition des observations par source

| Source | Nombre de lignes |
|---|---:|
| `OneAcre_survey` | 77 474 |
| `CEEPA_time_avg` | 20 933 |
| `Niche_trial` | 14 354 |
| `CEEPA_annual` | 14 104 |
| `USAID_Zimbabwe` | 2 852 |
| `Corbeels2020` | 2 095 |

La source `OneAcre_survey` représente la majorité des observations du fichier examiné. Les distributions globales peuvent donc être fortement influencées par cette source.

Les périodes couvertes, les méthodes de collecte et les règles de calcul doivent être documentées séparément avant de comparer les observations entre sources.

### 5.3. Constats de qualité

| Observation | Résultat observé | Action prévue |
|---|---:|---|
| Coordonnées manquantes | Environ 41 % | Examiner leur répartition par source et vérifier leur nécessité pour le scénario retenu. |
| `L3_GID` manquant | Environ 36,7 % | Vérifier la disponibilité des niveaux administratifs selon la source. |
| `Area_ha_` manquant | Environ 28,4 % | Examiner la couverture et la définition de la superficie. |
| `HarvestYear` manquant | 20 933 | Vérifier la relation avec `CEEPA_time_avg`. |
| Doublons exacts | 1 282 | Identifier les répétitions avant de décider de leur traitement. |
| Rendement maximal | 150 t/ha | Vérifier les unités, les sources et la plausibilité des valeurs extrêmes. |
| Superficies égales à zéro | Présentes | Vérifier leur signification et leur cohérence avec les autres variables. |
| Dates agricoles | Formats numériques observés | Vérifier le format, l’interprétation et la plausibilité des dates. |

Les contrôles préliminaires n’ont pas relevé de rendements manquants ni de rendements nuls ou négatifs dans le fichier examiné. Cette observation devra être conservée avec la référence à la version et à la méthode de contrôle utilisées.

### 5.4. Risques méthodologiques

Les différences de provenance et de méthodes de collecte peuvent limiter la comparabilité des observations. Les valeurs manquantes en localisation peuvent aussi affecter les analyses géographiques.

Les colonnes `Area_ha_` et `Yield_ton_ha_` doivent être étudiées pour comprendre leurs relations avec les autres mesures. Une superficie ne doit pas être automatiquement utilisée comme prédicteur sans vérifier sa disponibilité et son rôle dans le calcul de la cible.

### 5.5. Actions de suivi

1. Confirmer la version du fichier et expliquer l’écart avec l’effectif de référence.
2. Documenter les six sources, leurs périodes et leurs méthodes.
3. Examiner les doublons exacts et les doublons potentiels.
4. Étudier les valeurs manquantes par source, pays et culture.
5. Vérifier les dates agricoles, les superficies et les rendements extrêmes.
6. Clarifier la signification des colonnes encore inconnues.

**Décision provisoire :** poursuivre le Data Understanding. Les doublons, les différences entre sources et les incohérences potentielles doivent être étudiés avant toute préparation définitive.

## 6. Dataset 4 — Regional

**Fichier :** `GROW-Africa_Regional.xlsx`

### 6.1. Inventaire du fichier examiné

| Contrôle | Résultat observé |
|---|---:|
| Feuille examinée | `Sheet1` |
| Nombre de lignes | 197 535 |
| Nombre de colonnes | 25 |
| Pays distincts | 49 |
| Cultures distinctes | 34 |
| Sources distinctes | 6 |
| Doublons exacts de lignes | 0 |

L’effectif observé correspond à l’effectif de travail attendu pour le fichier Regional. Cela ne suffit toutefois pas à confirmer la version exacte du fichier.

### 6.2. Répartition par source

| Source | Nombre de lignes | Part approximative |
|---|---:|---:|
| `HarvestStat` | 132 675 | 67,2 % |
| `AgroMAPS` | 27 710 | 14,0 % |
| `RCeA` | 17 931 | 9,1 % |
| `FAOSTAT` | 11 884 | 6,0 % |
| `FAO_subnational` | 7 261 | 3,7 % |
| `USAID_KadunaState` | 74 | 0,04 % |
| **Total** | **197 535** | **100 %** |

`HarvestStat` représente environ deux tiers des observations. Les résultats globaux peuvent donc être fortement influencés par cette source.

Les périodes, méthodes de collecte, niveaux géographiques et méthodes de calcul doivent être vérifiés séparément.

### 6.3. Valeurs manquantes

| Colonne | Valeurs manquantes | Part du fichier |
|---|---:|---:|
| `L3_GID` | 194 512 | 98,47 % |
| `L2_GID` | 85 477 | 43,27 % |
| `planting_year` | 64 860 | 32,83 % |
| `planting_month` | 64 860 | 32,83 % |
| `harvest_month` | 64 860 | 32,83 % |
| `yieldTonHa` | 34 584 | 17,51 % |
| `QC_flag_A` | 27 710 | 14,03 % |
| `QC_flag_P` | 27 710 | 14,03 % |
| `QC_flag_Y` | 27 710 | 14,03 % |
| `productionTon` | 22 036 | 11,16 % |
| `areaHa` | 20 417 | 10,34 % |
| `L1_GID` | 11 890 | 6,02 % |
| `GDAM_ID` | 491 | 0,25 % |
| `level` | 491 | 0,25 % |
| `admin_1` | 318 | 0,16 % |

L’absence fréquente de `L3_GID` peut être liée au niveau d’agrégation des observations plutôt qu’à une erreur. Cette hypothèse doit être vérifiée selon la source et le niveau géographique.

Les valeurs manquantes ne doivent pas être supprimées ou imputées avant d’avoir compris leur répartition et leur origine.

### 6.4. Contrôles numériques préliminaires

| Variable | Valeurs négatives | Valeurs égales à zéro | Minimum observé | Maximum observé |
|---|---:|---:|---:|---:|
| `yieldTonHa` | 66 | 446 | -99 | 6 996,21 |
| `areaHa` | 112 | 8 761 | -999 | 1 751 414 298 |
| `productionTon` | 138 | 4 149 | -999 | 17 014 272 |

Ces résultats signalent des valeurs à investiguer, sans permettre de conclure automatiquement qu’elles sont toutes incorrectes.

Les valeurs `-99` et `-999` peuvent correspondre à des codes spéciaux ou à des anomalies. Leur signification doit être confirmée. Les rendements très élevés, les superficies et les productions extrêmes doivent également être examinés en tenant compte des unités et des sources.

Aucune suppression automatique n’est décidée à ce stade.

### 6.5. Répartition par niveau géographique

| Valeur de `level` | Nombre de lignes |
|---:|---:|
| 0 | 11 884 |
| 1 | 73 170 |
| 2 | 108 967 |
| 3 | 3 023 |
| Valeur manquante | 491 |

Cette répartition est compatible avec la présence de données nationales et infranationales. La signification officielle de chaque valeur de `level` doit néanmoins être confirmée.

### 6.6. Colonnes à documenter

| Colonnes | Vérification nécessaire |
|---|---|
| `GDAM_ID` | Définition et relation avec les identifiants géographiques |
| `level` | Signification de chaque valeur |
| `season_name` | Définition et catégories |
| `crop_production_system` | Signification des catégories |
| `QC_flag_A`, `QC_flag_P`, `QC_flag_Y` | Codes, règles d’attribution et relation éventuelle avec la cible |
| `Source` | Référence, période et méthode de collecte |
| `areaHa`, `productionTon`, `yieldTonHa` | Relation entre surface, production et rendement |
| `planting_year`, `planting_month`, `harvest_year`, `harvest_month` | Construction des dates et gestion des campagnes agricoles |

### 6.7. Risque de fuite de données

Si le rendement est calculé à partir de la production et de la superficie, utiliser `areaHa` et `productionTon` pour prédire `yieldTonHa` peut entraîner une fuite de données lorsque ces informations ne sont pas disponibles au moment de la prédiction.

Ces variables doivent être conservées pour l’audit et les contrôles de cohérence. Leur utilisation comme prédicteurs est suspendue jusqu’à clarification de leur relation avec la cible et du scénario de prédiction.

Les indicateurs `QC_flag_*` ne doivent pas non plus être utilisés comme prédicteurs avant que leur signification et leur mode de calcul soient documentés.

### 6.8. Actions de suivi

1. Documenter les six sources et leurs périodes.
2. Examiner les valeurs manquantes par source, niveau géographique, pays et culture.
3. Investiguer les valeurs négatives et extrêmes.
4. Vérifier les relations entre surface, production et rendement.
5. Documenter les indicateurs de contrôle qualité.
6. Confirmer les définitions des niveaux et identifiants géographiques.
7. Mettre à jour le dictionnaire des données.
8. Définir les contrôles automatisés après établissement des règles de validation.

**Décision provisoire : Go restreint pour poursuivre le Data Understanding.** Le fichier n’est pas encore prêt pour une préparation définitive destinée à la modélisation.

## 7. Synthèse transversale des quatre datasets

| Dataset | Principaux points à résoudre | Décision provisoire |
|---|---|---|
| LSMS Crop Cut | Relation poids sec–rendement, année mal représentée, rôle des identifiants | Poursuivre l’audit |
| LSMS Survey | Définitions des variantes de production, superficie et rendement ; risque de fuite | Poursuivre l’audit |
| Point | Écart d’effectif à expliquer, doublons exacts, valeurs manquantes et différences entre sources | Poursuivre l’audit |
| Regional | Valeurs manquantes, codes numériques suspects, niveaux géographiques et relation production–surface–rendement | Go restreint pour le Data Understanding |

### Risques communs

Les quatre fichiers nécessitent une attention particulière sur les points suivants :

- la comparabilité entre sources et méthodes de collecte ;
- la signification des colonnes insuffisamment documentées ;
- la disponibilité des variables au moment de la prédiction ;
- les relations mathématiques entre la cible et les variables candidates ;
- la présence d’observations liées entre les jeux d’entraînement et de test ;
- les différences de couverture géographique et temporelle.

Les identifiants et les métadonnées doivent être conservés pendant l’audit. Leur exclusion éventuelle du modèle ne signifie pas qu’ils doivent être supprimés des données brutes ou des éléments de traçabilité.

## 8. Conclusion générale

L’examen des quatre datasets permet d’identifier les principales questions de qualité, de documentation et de cohérence à résoudre avant la préparation des données.

Les résultats disponibles restent préliminaires et leur niveau de détail varie selon le fichier. Les statistiques doivent être confirmées sur les versions exactes utilisées et les contrôles doivent devenir reproductibles avant toute décision définitive.

La prochaine étape consiste à harmoniser les quatre audits, compléter les contrôles manquants, mettre à jour le dictionnaire des données et établir une synthèse de compatibilité entre les fichiers.

**Décision générale : poursuivre le Data Understanding. Aucune préparation définitive pour la modélisation ni fusion des quatre datasets ne doit être engagée avant la clarification des risques importants, des définitions essentielles et des conditions de validation.**
