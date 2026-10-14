# Dictionnaire des données — GROW-Africa

**Projet :** African Crop Yield Intelligence  
**Étape :** Audit des données — Dictionnaire des données  
**Statut :** Version de travail

---

## 0. Présentation du document

Ce document décrit les colonnes des quatre fichiers de la base GROW-Africa. Il présente leur signification, leur type, leur rôle potentiel dans le projet et les points qui restent à vérifier.

Les définitions s'appuient sur l'article scientifique associé à la base et sur sa documentation. Certaines informations restent à confirmer directement à partir des fichiers.

### Statut des définitions

| Statut | Signification |
|---|---|
| Documenté | Information confirmée par une source officielle. |
| Déduit | Interprétation basée sur le nom de la colonne ou le contexte. |
| Inconnu | Signification non confirmée. La colonne ne sera pas utilisée avant clarification. |
| À vérifier | Information qui nécessite une vérification complémentaire. |

### Rôle des colonnes

Les rôles proposés reposent sur l'hypothèse que la cible est le rendement agricole en tonnes par hectare (t/ha).

| Rôle | Signification |
|---|---|
| Cible | Variable que le modèle devra prédire. |
| Clé de regroupement | Identifiant utilisé pour organiser les données et construire les partitions d'entraînement et de test. |
| Candidate | Variable pouvant servir de variable explicative, sous réserve de sa disponibilité au moment de la prédiction. |
| Exclue (fuite) | Variable qui entre dans le calcul de la cible ou qui n'est pas disponible au moment de la prédiction. |
| Exclue (métadonnée) | Information de provenance ou texte libre qui ne sera pas utilisé directement comme variable explicative. |
| À investiguer | Rôle à déterminer après examen des données. |

### Statistiques à calculer

Les statistiques descriptives seront générées par un script dans `src/data/`. Elles comprendront le type pandas, le pourcentage de valeurs manquantes, le minimum, le maximum et le nombre de valeurs distinctes pour chaque colonne.

---

## 1. Informations générales sur la base

| Information | Valeur | Statut |
|---|---|---|
| Nombre total d'observations | 535 844, pour 25 cultures | Documenté dans l'article |
| Composition de la base | Données nationales FAO : 11 884 ; régionales : 185 651 ; enquêtes LSMS : 195 152 ; autres données ponctuelles : 143 157 | Article, figure 2 |
| Fichiers | `GROW-Africa_Regional`, `GROW-Africa_LSMS_survey`, `GROW-Africa_LSMS_cropcut`, `GROW-Africa_Point` | Article, p. 5 |
| Unité du rendement | Tonnes par hectare (t/ha) | Article, p. 5 |
| Identifiants géographiques | Limites administratives GADM, niveaux 0 à 3 | Article, p. 4 |
| Décalage des coordonnées LSMS | De 0 à 2 km en zone urbaine et de 0 à 5 km en zone rurale ; 1 % des grappes rurales peuvent atteindre 10 km | Article, p. 4 |
| Nettoyage effectué par les auteurs | Harmonisation des noms de cultures et des références géographiques, suppression des doublons et filtrage de certains rendements aberrants | Article, p. 4 |
| Filtrage des rendements aberrants | Dans les données ponctuelles, exclusion des rendements inférieurs à 10 % de la médiane ou supérieurs à 200 % du 98e percentile de la distribution régionale de la culture | Article, p. 4 |
| Données nationales et sous-nationales | Les rendements aberrants n'ont pas été filtrés dans ces données | Article, p. 4 |
| Version utilisée | À confirmer. Le README mentionne la v1.0 ; une v2.0 existe sur Zenodo. DOI : `10.5281/zenodo.14961637` | À vérifier |
| Licence des données | À vérifier sur la page Zenodo. La licence de l'article ne permet pas de déduire celle des données. | À vérifier |

### Effectifs attendus

Ces effectifs serviront à vérifier la cohérence des fichiers téléchargés.

| Fichier | Effectif attendu | Remarque |
|---|---:|---|
| Regional | Environ 197 535 | Somme des données régionales (185 651) et nationales FAO (11 884). Vérifier la répartition avec `level`. |
| LSMS_survey | Environ 195 152 | À comparer à l'effectif réel. |
| Point | Environ 143 157 | À comparer à l'effectif réel. |
| LSMS_cropcut | 11 345 | Données concernant l'Éthiopie et 12 cultures. Vérifier si ces observations sont comprises dans le total de 535 844. |

---

## 2. GROW-Africa_LSMS_cropcut

Ce fichier contient des mesures directes de récolte (*crop cuts*) réalisées en parallèle des enquêtes LSMS. Selon l'article, les observations concernent l'Éthiopie.

Ces données peuvent servir de référence pour examiner la qualité des rendements, mais leur couverture géographique ne permet pas, à elle seule, d'évaluer la généralisation du modèle à plusieurs pays.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Country` | Pays de l'observation | Texte | Déduit | Clé de regroupement | Éthiopie attendue ; à confirmer. |
| `Source` | Source de l'enquête | Texte | Déduit | Exclue (métadonnée) | Peut renseigner sur l'année ou la méthode de collecte. |
| `Year` | Année de l'observation | Entier | À vérifier | Candidate | Vérifier s'il s'agit de l'année de récolte. |
| `GPS_lat` | Latitude | Décimal | Documenté pour les coordonnées | À investiguer | Vérifier si les coordonnées sont décalées selon le protocole LSMS. |
| `GPS_lon` | Longitude | Décimal | Documenté pour les coordonnées | À investiguer | Même vérification que pour la latitude. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Des valeurs manquantes sont possibles. |
| `holder_id` | Identifiant de l'exploitant | Texte | Déduit | Clé de regroupement | Définition à confirmer. |
| `household_id` | Identifiant du ménage | Texte | Déduit | Clé de regroupement | Vérifier les ménages présents sur plusieurs années. |
| `parcel_id` | Identifiant de la parcelle | Texte | Déduit | Clé de regroupement | Vérifier les répétitions éventuelles. |
| `field_id` | Identifiant du champ | Texte | Déduit | Clé de regroupement | Définition à confirmer. |
| `Crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | La base comprend 25 cultures. |
| `crop_origname` | Nom original de la culture | Texte | Déduit | Exclue (métadonnée) | Conservé pour la traçabilité. |
| `cropCutDay` | Jour de la mesure de récolte | Entier | Déduit | Exclue (fuite) | Information liée à la mesure. |
| `cropCutMonth` | Mois de la mesure de récolte | Entier | Déduit | Exclue (fuite) | Information liée à la mesure. |
| `freshWeightKg` | Poids frais récolté | Décimal, kg | Déduit | Exclue (fuite) | Peut intervenir dans le calcul du rendement. |
| `dryWeightKg` | Poids sec récolté | Décimal, kg | Déduit | Exclue (fuite) | Peut intervenir dans le calcul du rendement. |
| `Yield_ton_ha_` | Rendement agricole | Décimal, t/ha | Unité documentée ; formule à vérifier | Cible candidate | Vérifier si le rendement repose sur le poids frais ou sec. |

---

## 3. GROW-Africa_LSMS_survey

Ce fichier regroupe des données issues d'enquêtes LSMS-ISA auprès de ménages agricoles. L'article décrit une couverture de 13 pays sur la période 2004-2022.

Les productions peuvent être déclarées par les agriculteurs et les surfaces peuvent être déclarées ou mesurées par GPS. Certaines enquêtes suivent les mêmes ménages sur plusieurs années. Les coordonnées peuvent également être décalées.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Country` | Pays de l'observation | Texte | Déduit | Clé de regroupement | |
| `Source1` | Première partie de l'identifiant de source | Texte | Déduit | Exclue (métadonnée) | Signification exacte à confirmer. |
| `Source2` | Seconde partie de l'identifiant de source | Texte | Déduit | Exclue (métadonnée) | Peut correspondre à une enquête ou une année. |
| `Source` | Identifiant combiné de la source | Texte | Déduit | À investiguer | Peut renseigner sur la méthode de mesure et l'année. |
| `GPS_lat` | Latitude | Décimal | Documenté pour le décalage des coordonnées | À investiguer | Décalage possible de 0 à 5 km en zone rurale. |
| `GPS_lon` | Longitude | Décimal | Documenté pour le décalage des coordonnées | À investiguer | Même remarque que pour la latitude. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Le décalage GPS peut affecter le rattachement administratif. |
| `Crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `prcCrop` | Part de la parcelle occupée par la culture | Proportion | Déduit, cohérent avec l'article p. 10 | À investiguer | Peut intervenir dans le calcul de la surface par culture. |
| `prcLeft` | Signification non confirmée | Proportion supposée | Inconnu | Exclue provisoirement | Ne pas utiliser avant documentation. |
| `Prod_kg_` | Production déclarée | Décimal, kg | Déduit ; méthode de rappel documentée, article p. 10 | Exclue (fuite) | Peut entrer dans le calcul du rendement. |
| `ProdEst2_kg_` | Estimation alternative de la production | Inconnu | Inconnu | Exclue provisoirement | Définition à confirmer. |
| `ReportedArea_ha_` | Surface déclarée par l'agriculteur | Décimal, ha | Déduit ; article p. 9 | Exclue (fuite) | Peut entrer dans le calcul du rendement. |
| `GPSArea_ha_` | Surface mesurée par GPS | Décimal, ha | Déduit ; article p. 9 | Exclue (fuite) | Peut entrer dans le calcul du rendement. |
| `Yield_ton_ha_` | Rendement agricole | Décimal, t/ha | Unité documentée ; formule à vérifier | Cible candidate | Tester le calcul à partir de `Prod_kg_` et `ReportedArea_ha_`. |
| `YieldUsingGPS_ton_ha_` | Rendement calculé avec la surface GPS | Décimal, t/ha | Déduit | Cible alternative | Choisir une seule définition de la cible et la justifier. |
| `YieldEst2_ton_ha_` | Estimation alternative du rendement | Inconnu | Inconnu | Exclue provisoirement | Définition à documenter. |
| `YieldEst2UsingGPS_ton_ha_` | Rendement alternatif calculé avec la surface GPS | Inconnu | Inconnu | Exclue provisoirement | Définition à documenter. |
| `AgYearStart` | Année de début de la campagne agricole | Entier | Déduit | Candidate | Définition à harmoniser entre les fichiers. |
| `AgYearEnd` | Année de fin de la campagne agricole | Entier | Déduit | Candidate | Définition à harmoniser entre les fichiers. |
| `hhid` | Identifiant du ménage | Texte | Déduit | Clé de regroupement | Les ménages peuvent être suivis sur plusieurs vagues. |
| `parcel_id` | Identifiant de la parcelle | Texte | Déduit | Clé de regroupement | Vérifier les répétitions. |
| `plotid` | Identifiant du champ | Texte | Déduit | Clé de regroupement | Définition à confirmer. |
| `SpatialPrecision_km_` | Précision spatiale | Décimal, km | Déduit | À investiguer | Définition exacte à confirmer. |

---

## 4. GROW-Africa_Point

Ce fichier regroupe des observations ponctuelles issues de sources variées : One Acre Fund, USAID, études de la littérature et enquête CEEPA. L'article couvre notamment des données publiées entre 1974 et 2017.

Les méthodes de collecte sont hétérogènes et certaines observations proviennent d'essais agronomiques. C'est le seul fichier pour lequel les auteurs indiquent avoir filtré les rendements aberrants.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Source` | Étude ou référence d'origine | Texte | Documenté, article, tableau 1 | À investiguer | Peut renseigner sur la méthode de mesure. |
| `Crop` | Nom de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `HarvestYear` | Année de récolte | Entier | Documenté dans l'article | Candidate | |
| `Latitude` | Latitude du site | Décimal | Documenté pour les coordonnées | À investiguer | |
| `Longitude` | Longitude du site | Décimal | Documenté pour les coordonnées | À investiguer | |
| `SpatialPrecision_km_` | Précision spatiale | Décimal, km | Déduit | À investiguer | Définition exacte à confirmer. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 3. |
| `Country` | Pays de l'observation | Texte | Déduit | Clé de regroupement | |
| `SiteName` | Nom du site | Texte | Déduit | Clé de regroupement | Texte libre ; vérifier les noms similaires. |
| `Area_ha_` | Surface associée à l'observation | Décimal, ha | Déduit | À investiguer | Peut intervenir dans le calcul du rendement. |
| `Yield_ton_ha_` | Rendement agricole | Décimal, t/ha | Unité documentée | Cible candidate | Filtrage des rendements aberrants effectué par les auteurs. |
| `PlantDate` | Date de plantation | Date | Déduit | À investiguer | Peut être utile si elle est connue au moment de la prédiction. |
| `HarvestDate` | Date de récolte | Date | Déduit | Exclue (fuite) | Information postérieure à la prédiction. |
| `Notes` | Commentaires sur l'observation | Texte | Déduit | Exclue (métadonnée) | À examiner pour repérer des cas particuliers. |

---

## 5. GROW-Africa_Regional

Ce fichier rassemble des statistiques agricoles nationales et sous-nationales provenant notamment de la FAO, d'Agro-MAPS, de ReSAKSS, de HarvestStat et de l'USAID.

Les rendements aberrants ont été conservés dans ces données. L'article rapporte également des différences entre les rendements gouvernementaux, les enquêtes et les mesures directes de récolte. Ces différences doivent être prises en compte lors de la comparaison des sources.

### Identification et localisation

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `GDAM_ID` | Identifiant géographique | Texte | Déduit | Clé de regroupement | Nom exact à vérifier ; faute possible dans l'intitulé. |
| `country` | Pays | Texte | Déduit | Clé de regroupement | |
| `country_code` | Code du pays | Texte | Déduit | Clé de regroupement | |
| `admin_1` | Division administrative de niveau 1 | Texte | Déduit | Clé de regroupement | |
| `admin_2` | Division administrative de niveau 2 | Texte | Déduit | Clé de regroupement | |
| `level` | Niveau d'agrégation de la ligne | Texte | Déduit | À investiguer | À examiner pour distinguer les lignes nationales et régionales. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 3. |

### Culture et calendrier

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `season_name` | Nom de la saison agricole | Inconnu | Inconnu | À investiguer | Définition à confirmer. |
| `planting_year` | Année de plantation | Entier | Déduit | À investiguer | Définition de l'année à harmoniser entre les fichiers. |
| `planting_month` | Mois de plantation | Entier | Déduit | À investiguer | |
| `harvest_year` | Année de récolte | Entier | Documenté dans l'article | Candidate | |
| `harvest_month` | Mois de récolte | Entier | Déduit | Exclue (fuite) | À exclure si la prédiction est réalisée avant la récolte. |
| `crop_production_system` | Système de production agricole | Inconnu | Inconnu | À investiguer | Vérifier si la variable distingue, par exemple, les systèmes irrigués et pluviaux. |

### Surface, production et rendement

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `areaHa` | Surface agricole | Décimal, ha | Déduit | Exclue (fuite) | Entre dans le calcul du rendement. |
| `productionTon` | Production agricole | Décimal, t | Déduit | Exclue (fuite) | Entre dans le calcul du rendement. |
| `yieldTonHa` | Rendement agricole | Décimal, t/ha | Unité documentée | Cible candidate | Vérifier le calcul à partir de la production et de la surface. |

### Contrôle qualité et provenance

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `QC_flag_A` | Indicateur de contrôle qualité associé à la surface | Code | Inconnu | À investiguer | Peut dépendre de l'examen de la valeur ; risque de fuite à vérifier. |
| `QC_flag_P` | Indicateur de contrôle qualité associé à la production | Code | Inconnu | À investiguer | Signification et mode de calcul à documenter. |
| `QC_flag_Y` | Indicateur de contrôle qualité associé au rendement | Code | Inconnu | À investiguer | Peut être lié à la valeur cible ; ne pas utiliser sans documentation. |
| `Source` | Source des statistiques | Texte | Documenté, article, tableau 1 | À investiguer | Peut renseigner sur la méthode de collecte. |
| `originalname` | Nom original de la culture avant harmonisation | Texte | Déduit | Exclue (métadonnée) | Conservé pour la traçabilité. |

---

## 6. Synthèse des rôles

| Rôle | Colonnes concernées |
|---|---|
| Cibles candidates | `Yield_ton_ha_` dans les fichiers cropcut, survey et point ; `yieldTonHa` dans le fichier regional ; variantes `YieldUsingGPS_ton_ha_` et autres estimations de rendement à examiner. |
| Clés de regroupement | `L0_GID`, `L1_GID`, `L2_GID`, `L3_GID`, pays, `admin_1`, `admin_2`, identifiants de ménage, parcelle, champ, exploitant et site. |
| Variables explicatives possibles | Culture, année (`harvest_year`, `HarvestYear`, `AgYearStart`, `AgYearEnd`) et éventuellement système de production ou source, sous réserve des tests d'ablation. |
| Variables exclues pour risque de fuite | Production, surfaces et poids de récolte lorsqu'ils entrent dans le calcul de la cible ; dates et mois de récolte non disponibles au moment de la prédiction ; variantes de rendement non retenues. |
| Variables à documenter | `prcLeft`, `ProdEst2_kg_`, `YieldEst2_ton_ha_`, `YieldEst2UsingGPS_ton_ha_`, `season_name`, `crop_production_system` et les indicateurs `QC_flag`. |

Les quatre fichiers recensés ne contiennent pas directement de variables climatiques, pédologiques ou agronomiques détaillées dans les colonnes présentées ici. Les variables explicatives disponibles semblent principalement concerner la culture, la localisation, le calendrier agricole et la source des données.

---

## 7. Risques identifiés et actions prévues

| Risque | Action prévue |
|---|---|
| La cible est calculée à partir de la production, de la surface ou du poids de récolte. | Exclure ces variables des entrées du modèle et vérifier leur absence automatiquement. |
| Certaines variables ne sont connues qu'après la récolte. | Les exclure selon le moment choisi pour la prédiction. |
| Un même ménage ou une même parcelle apparaît plusieurs fois. | Vérifier les répétitions et éviter de répartir les observations liées entre entraînement et test. |
| Les coordonnées LSMS sont décalées. | Examiner la fiabilité des identifiants administratifs et éviter de supposer que les coordonnées sont exactes. |
| Plusieurs sources peuvent couvrir les mêmes lieux. | Identifier les observations potentiellement liées avant de fusionner les fichiers. |
| Les méthodes de mesure diffèrent selon les sources. | Comparer les distributions et documenter les différences de mesure. |
| Le filtrage des rendements aberrants concerne uniquement les données ponctuelles. | Consigner ce traitement et tenir compte des différences entre les fichiers. |
| Le fichier Regional contient des niveaux d'agrégation différents. | Examiner `level` et traiter séparément les observations nationales si nécessaire. |
| La source peut servir de proxy pour l'année, le pays ou la méthode de collecte. | Tester son apport par ablation et vérifier qu'elle ne crée pas de fuite. |
| Les indicateurs `QC_flag` peuvent dépendre de la cible. | Ne pas les utiliser avant d'avoir documenté leur définition. |

