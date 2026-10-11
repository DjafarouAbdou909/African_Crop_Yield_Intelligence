# Dictionnaire des données — GROW-Africa

Ce document présente les variables des quatre fichiers Excel utilisés dans le projet **African Crop Yield Intelligence**. Les définitions sont établies à partir des noms des colonnes et de la structure des fichiers.

## 1. GROW-Africa_LSMS_cropcut.xlsx

**Description :** données de récoltes expérimentales (*crop cuts*) issues d'enquêtes agricoles LSMS.

| Colonne | Définition |
|---|---|
| `Country` | Pays auquel appartient l'observation. |
| `Source` | Identifiant de la source ou de l'enquête d'origine. |
| `Year` | Année associée à l'observation agricole. |
| `GPS_lat` | Latitude géographique de l'observation. |
| `GPS_lon` | Longitude géographique de l'observation. |
| `L0_GID` | Identifiant géographique du niveau administratif 0, généralement le pays. |
| `L1_GID` | Identifiant géographique du niveau administratif 1. |
| `L2_GID` | Identifiant géographique du niveau administratif 2. |
| `L3_GID` | Identifiant géographique du niveau administratif 3. |
| `holder_id` | Identifiant du détenteur ou exploitant agricole. |
| `household_id` | Identifiant du ménage enquêté. |
| `parcel_id` | Identifiant de la parcelle agricole. |
| `field_id` | Identifiant du champ ou de la zone cultivée. |
| `Crop` | Nom harmonisé de la culture agricole. |
| `crop_origname` | Nom original de la culture dans la source d'origine. |
| `cropCutDay` | Jour associé à la mesure de récolte expérimentale. |
| `cropCutMonth` | Mois associé à la mesure de récolte expérimentale. |
| `freshWeightKg` | Poids frais de la récolte, en kilogrammes d'après le nom de la variable. |
| `dryWeightKg` | Poids sec de la récolte, en kilogrammes d'après le nom de la variable. |
| `Yield_ton_ha_` | Rendement agricole, apparemment exprimé en tonnes par hectare. |

## 2. GROW-Africa_LSMS_survey.xlsx

**Description :** données de production et de rendement provenant d'enquêtes agricoles auprès des ménages.

| Colonne | Définition |
|---|---|
| `Country` | Pays auquel appartient l'observation. |
| `Source1` | Première composante de l'identification de la source. |
| `Source2` | Deuxième composante de l'identification de la source, souvent liée à une enquête ou à une année. |
| `Source` | Identifiant combiné de la source de données. |
| `GPS_lat` | Latitude géographique de l'observation. |
| `GPS_lon` | Longitude géographique de l'observation. |
| `L0_GID` | Identifiant géographique du niveau administratif 0. |
| `L1_GID` | Identifiant géographique du niveau administratif 1. |
| `L2_GID` | Identifiant géographique du niveau administratif 2. |
| `L3_GID` | Identifiant géographique du niveau administratif 3. |
| `Crop` | Nom harmonisé de la culture agricole. |
| `prcCrop` | Pourcentage ou proportion associé à la culture sur la parcelle. |
| `prcLeft` | Variable liée à un pourcentage ou à une proportion. |
| `Prod_kg_` | Production agricole, apparemment exprimée en kilogrammes. |
| `ProdEst2_kg_` | Estimation alternative de la production en kilogrammes. |
| `ReportedArea_ha_` | Surface déclarée, apparemment exprimée en hectares. |
| `GPSArea_ha_` | Surface estimée à partir de données GPS, apparemment en hectares. |
| `Yield_ton_ha_` | Rendement agricole, apparemment en tonnes par hectare. |
| `YieldUsingGPS_ton_ha_` | Rendement calculé en utilisant la surface GPS, d'après le nom de la variable. |
| `YieldEst2_ton_ha_` | Estimation alternative du rendement. |
| `YieldEst2UsingGPS_ton_ha_` | Estimation alternative du rendement utilisant la surface GPS, d'après le nom. |
| `AgYearStart` | Année de début de la période agricole. |
| `AgYearEnd` | Année de fin de la période agricole. |
| `hhid` | Identifiant du ménage enquêté (*household ID*). |
| `parcel_id` | Identifiant de la parcelle agricole. |
| `plotid` | Identifiant du champ ou de la portion de terre agricole. |
| `SpatialPrecision_km_` | Indicateur de précision spatiale, apparemment exprimé en kilomètres. |

## 3. GROW-Africa_Point.xlsx

**Description :** observations agricoles associées à des sites ou à des localisations ponctuelles.

| Colonne | Définition |
|---|---|
| `Source` | Source, étude ou référence à l'origine de l'observation. |
| `Crop` | Culture agricole observée. |
| `HarvestYear` | Année de récolte. |
| `Latitude` | Latitude géographique du site. |
| `Longitude` | Longitude géographique du site. |
| `SpatialPrecision_km_` | Indicateur de précision spatiale, apparemment exprimé en kilomètres. |
| `L0_GID` | Identifiant géographique du niveau administratif 0. |
| `L1_GID` | Identifiant géographique du niveau administratif 1. |
| `L2_GID` | Identifiant géographique du niveau administratif 2. |
| `L3_GID` | Identifiant géographique du niveau administratif 3. |
| `Country` | Pays associé à l'observation. |
| `SiteName` | Nom ou description du site d'observation. |
| `Area_ha_` | Surface associée à l'observation, apparemment en hectares. |
| `Yield_ton_ha_` | Rendement agricole, apparemment en tonnes par hectare. |
| `PlantDate` | Date de plantation ou de semis. |
| `HarvestDate` | Date de récolte. |
| `Notes` | Notes ou informations complémentaires relatives à l'observation. |

## 4. GROW-Africa_Regional.xlsx

**Description :** statistiques agricoles regroupées par pays ou par zone administrative.

### Identification et localisation

| Colonne | Définition |
|---|---|
| `GDAM_ID` | Identifiant géographique. |
| `country` | Nom du pays. |
| `country_code` | Code associé au pays. |
| `admin_1` | Nom de la division administrative de niveau 1. |
| `admin_2` | Nom de la division administrative de niveau 2. |
| `level` | Niveau géographique auquel correspond l'observation. |
| `L0_GID` | Identifiant géographique du niveau administratif 0. |
| `L1_GID` | Identifiant géographique du niveau administratif 1. |
| `L2_GID` | Identifiant géographique du niveau administratif 2. |
| `L3_GID` | Identifiant géographique du niveau administratif 3. |

### Culture et calendrier agricole

| Colonne | Définition |
|---|---|
| `crop` | Nom harmonisé de la culture agricole. |
| `season_name` | Nom ou catégorie de la saison agricole. |
| `planting_year` | Année de plantation ou de semis. |
| `planting_month` | Mois de plantation ou de semis. |
| `harvest_year` | Année de récolte. |
| `harvest_month` | Mois de récolte. |
| `crop_production_system` | Catégorie du système de production agricole. |

### Surface, production et rendement

| Colonne | Définition |
|---|---|
| `areaHa` | Surface agricole, apparemment exprimée en hectares. |
| `productionTon` | Production agricole, apparemment exprimée en tonnes. |
| `yieldTonHa` | Rendement agricole, apparemment exprimé en tonnes par hectare. |

### Contrôle qualité et provenance

| Colonne | Définition |
|---|---|
| `QC_flag_A` | Indicateur de contrôle qualité associé à la surface. |
| `QC_flag_P` | Indicateur de contrôle qualité associé à la production. |
| `QC_flag_Y` | Indicateur de contrôle qualité associé au rendement. |
| `Source` | Source des statistiques agricoles. |
| `originalname` | Nom original de la culture tel qu'il apparaît dans la source avant harmonisation. |