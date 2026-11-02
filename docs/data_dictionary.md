
# Dictionnaire des données — GROW-Africa

**Projet :** African Crop Yield Intelligence

**Étape :** Audit des données — Dictionnaire des données

**Statut :** Version mise à jour après la phase de Data Understanding

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
| Vérifié | Information confirmée par un calcul reproductible sur les fichiers, documenté dans `notebooks/02_data_understanding.ipynb`. |

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

### Traitements préalablement appliqués aux données par les auteurs

D'après la documentation de GROW-Africa, plusieurs traitements ont été appliqués aux données avant leur diffusion :

- **Harmonisation des noms de cultures :** uniformisation des noms afin de faciliter leur comparaison entre les différentes sources.
- **Suppression des doublons :** élimination des observations identifiées comme doublons.
- **Harmonisation des références géographiques :** harmonisation des références et attribution d'identifiants administratifs.
- **Filtrage de certains rendements aberrants dans les données ponctuelles :** exclusion de valeurs selon des seuils calculés à partir des distributions régionales propres aux cultures.
- **Conservation des rendements aberrants dans les données nationales et infranationales :** ces données n'ont pas fait l'objet du même filtrage des rendements aberrants.

### Limites de la documentation source

La documentation décrit ces traitements à l'échelle générale, mais ne fournit pas, à elle seule, un dictionnaire exhaustif précisant pour chaque colonne sa signification, son type, son unité et son rôle potentiel dans un projet de prédiction. Le présent dictionnaire complète cette documentation en distinguant les informations documentées, les interprétations déduites et les points restant à vérifier.

Le fait que certains traitements aient déjà été appliqués ne garantit pas que les fichiers utilisés soient exempts d'anomalies ou directement adaptés à l'objectif de prédiction. L'audit complémentaire devra donc vérifier les propriétés des fichiers effectivement téléchargés, documenter les constats observés et distinguer les traitements confirmés par les auteurs des contrôles réalisés dans le cadre du projet.

### Effectifs attendus

Ces effectifs serviront à vérifier la cohérence des fichiers téléchargés.

| Fichier | Effectif attendu | Remarque |
|---|---:|---|
| Regional | 197 535 | Vérifié. Somme exacte des 185 651 lignes régionales et des 11 884 lignes nationales. Les 11 884 lignes de `level` 0 coïncident avec les lignes `FAOSTAT`. |
| LSMS_survey | 195 152 | Vérifié. Effectif identique à celui de l'article. |
| Point | 131 812 | Vérifié. Les 143 157 autres données locales de l'article correspondent à la somme de `Point` et de `LSMS_cropcut`. |
| LSMS_cropcut | 11 345 | Vérifié. Éthiopie uniquement et 12 cultures. Ces observations sont comprises dans le total de 535 844, que les quatre fichiers atteignent exactement. |

---

## 2. GROW-Africa_LSMS_cropcut

Ce fichier contient des mesures directes de récolte (**crop cuts**) réalisées en parallèle des enquêtes LSMS. Selon l'article, les observations concernent l'Éthiopie.

Ces données peuvent servir de référence pour examiner la qualité des rendements, mais leur couverture géographique ne permet pas, à elle seule, d'évaluer la généralisation du modèle à plusieurs pays.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Country` | Pays de l'observation | Texte | Vérifié | Clé de regroupement | Valeur unique `Ethiopia` sur les 11 345 lignes. |
| `Source` | Vague de l'enquête éthiopienne | Texte | Vérifié | Exclue (métadonnée) | Quatre vagues `ETH2011`, `ETH2013b`, `ETH2015` et `ETH2018`. Les valeurs manquantes de plusieurs colonnes dépendent de la vague. |
| `Year` | Année de fin de campagne agricole | Entier | Vérifié | Candidate | Valeurs 2012, 2014, 2016 et 2019. Égale à `AgYearEnd` de la vague `survey` correspondante. La forme `2,012` relevée dans l'audit est un artefact d'affichage. |
| `GPS_lat` | Latitude | Décimal | Documenté pour les coordonnées | À investiguer | Vérifier si les coordonnées sont décalées selon le protocole LSMS. |
| `GPS_lon` | Longitude | Décimal | Documenté pour les coordonnées | À investiguer | Même vérification que pour la latitude. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Des valeurs manquantes sont possibles. |
| `holder_id` | Identifiant de l'exploitant | Entier stocké en décimal | Vérifié | Clé de regroupement | Identifiant du ménage suivi d'un rang à deux chiffres. Absent pour toute la vague `ETH2018`. Les 415 valeurs de 16 chiffres finissent toutes par 0, signe d'une troncature à 15 chiffres significatifs. |
| `household_id` | Identifiant du ménage | Entier stocké en décimal | Vérifié | Clé de regroupement | Égal à `holder_id // 100` pour 99,03 % des lignes. 82 lignes de `ETH2011` portent deux valeurs de substitution. 914 exploitants sont observés sur deux vagues et 527 sur trois. |
| `parcel_id` | Identifiant de la parcelle | Texte | Déduit | Clé de regroupement | Vérifier les répétitions éventuelles. |
| `field_id` | Identifiant du champ | Texte | Déduit | Clé de regroupement | Définition à confirmer. |
| `Crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | La base comprend 25 cultures. |
| `crop_origname` | Nom original de la culture | Texte | Déduit | Exclue (métadonnée) | Conservé pour la traçabilité. |
| `cropCutDay` | Jour de la mesure de récolte | Entier | Déduit | Exclue (fuite) | Aucun jour 31 sur 11 341 dates. Calendrier éthiopien probable, à confirmer dans la documentation ESS. |
| `cropCutMonth` | Mois de la mesure de récolte | Entier | Déduit | Exclue (fuite) | Absent pour toute la vague `ETH2013b`. 132 dates impossibles en lecture grégorienne, dont 116 au 30 février. Valeurs 0 et 20 à 83 invalides. |
| `freshWeightKg` | Poids frais de l'échantillon récolté | Décimal, kg | Vérifié | Exclue (fuite) | Mesure du même échantillon que la cible. 80 lignes ont un poids sec supérieur au poids frais et 4 un poids frais nul. |
| `dryWeightKg` | Poids sec de l'échantillon récolté sur 16 m² | Décimal, kg | Vérifié | Exclue (fuite) | Fuite certaine. La cible est égale à 0,625 fois cette valeur sur 100 % des lignes. |
| `Yield_ton_ha_` | Rendement agricole | Décimal, t/ha | Vérifié | Cible candidate | Égal à `0,625 × dryWeightKg`, soit 1 kg récolté sur un carré de 4 m sur 4 m converti en t/ha. |

---

## 3. GROW-Africa_LSMS_survey

Ce fichier regroupe des données issues d'enquêtes LSMS-ISA auprès de ménages agricoles. L'article décrit une couverture de 13 pays sur la période 2004-2022.

Les productions peuvent être déclarées par les agriculteurs et les surfaces peuvent être déclarées ou mesurées par GPS. Certaines enquêtes suivent les mêmes ménages sur plusieurs années. Les coordonnées peuvent également être décalées.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Country` | Pays de l'observation | Texte | Vérifié | Clé de regroupement | 13 pays. Le libellé `Cote dIvoire` diffère de `Côte dIvoire` utilisé dans `regional`. |
| `Source1` | Première partie de l'identifiant de source | Texte | Déduit | Exclue (métadonnée) | Signification exacte à confirmer. |
| `Source2` | Code pays et année de la vague | Texte | Vérifié | Exclue (métadonnée) | L'année du libellé vaut `AgYearStart` ou `AgYearStart` plus un selon la vague. Elle ne constitue pas une source fiable de l'année. |
| `Source` | Identifiant combiné de la source | Texte | Déduit | À investiguer | Peut renseigner sur la méthode de mesure et l'année. |
| `GPS_lat` | Latitude | Décimal | Documenté pour le décalage des coordonnées | À investiguer | Décalage possible de 0 à 5 km en zone rurale. |
| `GPS_lon` | Longitude | Décimal | Documenté pour le décalage des coordonnées | À investiguer | Même remarque que pour la latitude. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 1. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau administratif 2. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Le décalage GPS peut affecter le rattachement administratif. |
| `Crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `prcCrop` | Part de la parcelle occupée par la culture | Pourcentage | Vérifié | Exclue (fuite) | Entre dans le calcul de toutes les variantes de rendement. 80 valeurs supérieures à 100, toutes dans `LSMS_MWI2019`. |
| `prcLeft` | Signification non confirmée | Pourcentage supposé | Inconnu | Exclue provisoirement | Nul dans 99 % des cas. Ne pas utiliser avant documentation. |
| `Prod_kg_` | Production déclarée | Décimal, kg | Vérifié | Exclue (fuite) | Numérateur de `Yield_ton_ha_` et de `YieldUsingGPS_ton_ha_`. |
| `ProdEst2_kg_` | Estimation alternative de la production | Décimal, kg | Déduit | Exclue (fuite) | Numérateur de `YieldEst2UsingGPS_ton_ha_`. Renseignée sur 6 % des lignes seulement. |
| `ReportedArea_ha_` | Surface déclarée par l'agriculteur | Décimal, ha | Vérifié | Exclue (fuite) | Dénominateur de `Yield_ton_ha_`. 59,8 % des valeurs tombent sur un multiple d'un quart d'acre. Une valeur aberrante de 5,99 milliards d'hectares dans `LSMS_GNB2021`. |
| `GPSArea_ha_` | Surface mesurée par GPS | Décimal, ha | Vérifié | Exclue (fuite) | Dénominateur de `YieldUsingGPS_ton_ha_`. Le rapport entre surface déclarée et surface GPS varie de 1,67 sous 0,1 ha à 0,81 au-delà de 2 ha. |
| `Yield_ton_ha_` | Rendement fondé sur la surface déclarée | Décimal, t/ha | Vérifié | Cible candidate | Égal à `Prod_kg_` divisé par `ReportedArea_ha_` et par la part `prcCrop`, converti en tonnes, pour 99,10 % des lignes. Les valeurs manquantes correspondent pour l'essentiel au filtrage des valeurs aberrantes par les auteurs. |
| `YieldUsingGPS_ton_ha_` | Rendement fondé sur la surface GPS | Décimal, t/ha | Vérifié | Cible recommandée pour `survey` | Même construction avec `GPSArea_ha_` pour 99,37 % des lignes. Mesure de surface objective, au prix d'une couverture réduite à 152 205 lignes. |
| `YieldEst2_ton_ha_` | Estimation alternative du rendement | Décimal, t/ha | Déduit | Exclue (fuite) | Reproduite avec `ProdEst2_kg_` pour 99,72 % des lignes comparables, mais renseignée sans `ProdEst2_kg_` sur 24 066 lignes tanzaniennes. Définition non homogène. |
| `YieldEst2UsingGPS_ton_ha_` | Rendement alternatif fondé sur la surface GPS | Décimal, t/ha | Vérifié | Exclue (fuite) | Reproduit avec `ProdEst2_kg_` et `GPSArea_ha_` pour 99,66 % des lignes. |
| `AgYearStart` | Année de début de la campagne agricole | Entier | Vérifié | Candidate | Toujours inférieure d'un an à `AgYearEnd`. |
| `AgYearEnd` | Année de fin de la campagne agricole | Entier | Vérifié | Candidate | Année de référence retenue pour l'harmonisation avec `cropcut`. Absente pour les 218 lignes de `LSMS_BFA2021`, déductible de `AgYearStart`. |
| `hhid` | Identifiant du ménage | Texte | Vérifié | Clé de regroupement | Format variable selon les vagues. Tronqué en notation scientifique dans `LSMS_ETH2018`, avec 251 valeurs pour 3 417 lignes, et absent dans `LSMS_ETH2021`. |
| `parcel_id` | Identifiant de la parcelle | Texte | Déduit | Clé de regroupement | Vérifier les répétitions. |
| `plotid` | Identifiant du champ | Texte | Déduit | Clé de regroupement | Aucune combinaison d'identifiants n'est unique. La clé la plus complète conserve 14 434 doublons. |
| `SpatialPrecision_km_` | Précision spatiale | Décimal, km | Vérifié | Exclue (métadonnée) | Constante égale à 5 sur toutes les lignes, sans information. |

---

## 4. GROW-Africa_Point

Ce fichier regroupe des observations ponctuelles issues de sources variées : One Acre Fund, USAID, études de la littérature et enquête CEEPA. L'article couvre notamment des données publiées entre 1974 et 2017.

Les méthodes de collecte sont hétérogènes et certaines observations proviennent d'essais agronomiques. C'est le seul fichier pour lequel les auteurs indiquent avoir filtré les rendements aberrants.

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `Source` | Étude ou référence d'origine | Texte | Vérifié | À investiguer | Six sources. Fortement liée à la période et à la méthode de mesure. `OneAcre_survey` représente 59 % des lignes. |
| `Crop` | Nom de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `HarvestYear` | Année de récolte | Entier | Vérifié | Candidate | Absente pour les 20 933 lignes de `CEEPA_time_avg`, qui sont des moyennes temporelles. Couverture de 1974 à 2021. |
| `Latitude` | Latitude du site | Décimal | Vérifié | À investiguer | 215 coordonnées de `Niche_trial` inversées avec la longitude et 30 latitudes de signe erroné dans `Corbeels2020`. |
| `Longitude` | Longitude du site | Décimal | Vérifié | À investiguer | Une valeur de 76,1 hors d'Afrique dans `OneAcre_survey`. |
| `SpatialPrecision_km_` | Précision spatiale | Décimal, km | Déduit | À investiguer | Valeurs 0,03, 1,85 et 5. Absente exactement lorsque les deux coordonnées sont absentes. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Documenté, article p. 4 | Clé de regroupement | Niveau national. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Documenté, article p. 4 | Clé de regroupement | 108 valeurs manquantes déguisées sous la forme du texte `[]`. Une ligne associe un `L0_GID` burundais à un `L1_GID` rwandais. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Documenté, article p. 4 | Clé de regroupement | Mêmes 108 valeurs `[]` que `L1_GID`. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Documenté, article p. 4 | Clé de regroupement | Mêmes 108 valeurs `[]` que `L1_GID`. |
| `Country` | Pays de l'observation | Texte | Vérifié | Clé de regroupement | 21 pays. Rwanda, Kenya et Burundi représentent 66 % des lignes. |
| `SiteName` | Nom du site ou identifiant d'exploitation | Texte | Vérifié | Clé de regroupement | Identifiant numérique pour les sources CEEPA. `CEEPA_annual` et `CEEPA_time_avg` partagent 4 965 sites. |
| `Area_ha_` | Surface associée à l'observation | Décimal, ha | Déduit | À investiguer | Peut intervenir dans le calcul du rendement. |
| `Yield_ton_ha_` | Rendement agricole | Décimal, t/ha | Vérifié | Cible candidate | Aucune valeur manquante. 0,24 % des valeurs seulement sortent des bornes reconstruites du filtre des auteurs. Maximum de 150 t/ha. |
| `PlantDate` | Date de plantation | Numéro de série Excel | Vérifié | À investiguer | Origine 1899-12-30. 684 récoltes antérieures à la plantation sur 58 744 couples de dates. |
| `HarvestDate` | Date de récolte | Numéro de série Excel | Vérifié | Exclue (fuite) | Information postérieure à la prédiction. Son année diffère de `HarvestYear` sur 3 208 lignes, dont 3 054 avec un an d'écart. |
| `Notes` | Commentaires sur l'observation | Texte | Vérifié | Exclue (métadonnée) | Mode de travail du sol dans `Corbeels2020` et saison A ou B dans `Niche_trial`. |

---

## 5. GROW-Africa_Regional

Ce fichier rassemble des statistiques agricoles nationales et sous-nationales provenant notamment de la FAO, d'Agro-MAPS, de ReSAKSS, de HarvestStat et de l'USAID.

Les rendements aberrants ont été conservés dans ces données. L'article rapporte également des différences entre les rendements gouvernementaux, les enquêtes et les mesures directes de récolte. Ces différences doivent être prises en compte lors de la comparaison des sources.

### Identification et localisation

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `GDAM_ID` | Identifiant GADM le plus fin de la ligne | Texte | Vérifié | Clé de regroupement | Égal à l'identifiant GID le plus fin pour 99,91 % des lignes renseignées. Absent sur 491 lignes `HarvestStat`, les mêmes que `level`. |
| `country` | Pays | Texte | Vérifié | Exclue (métadonnée) | 49 libellés pour 47 pays. `DRC` et `Tanzania, United Republic of` doublonnent d'autres libellés. Utiliser `L0_GID` comme clé pays. |
| `country_code` | Code du pays | Texte | Vérifié | Exclue (métadonnée) | Mélange de codes ISO à deux et à trois lettres, soit 82 codes pour 49 libellés. |
| `admin_1` | Division administrative de niveau 1 | Texte | Vérifié | Exclue (métadonnée) | Texte `none` utilisé comme valeur manquante sur les 11 884 lignes nationales. |
| `admin_2` | Division administrative de niveau 2 | Texte | Vérifié | Exclue (métadonnée) | Texte `none` utilisé comme valeur manquante sur 75 389 lignes. Deux unités distinctes peuvent être rattachées au même `L2_GID`. |
| `level` | Niveau administratif de la ligne | Entier stocké en décimal | Vérifié | À investiguer | Valeurs 0 à 3, parfaitement cohérentes avec le dernier GID renseigné. Déductible des GID pour 485 des 491 valeurs manquantes. |
| `L0_GID` | Identifiant GADM de niveau 0 | Texte | Vérifié | Clé de regroupement | Le Ghana possède 25 codes distincts, de `L0GHA086` à `L0GHA110`, dont les suffixes entrent en collision avec d'autres pays. Les autres fichiers n'utilisent que `L0GHA086`. |
| `L1_GID` | Identifiant GADM de niveau 1 | Texte | Vérifié | Clé de regroupement | 318 valeurs du Lesotho débutent par un caractère invisible BOM. 13 identifiants ghanéens sont rattachés à plusieurs `L0_GID`. |
| `L2_GID` | Identifiant GADM de niveau 2 | Texte | Vérifié | Clé de regroupement | 36 valeurs manquantes déguisées sous la forme `[]` à Madagascar. 22 identifiants ghanéens sont rattachés à plusieurs `L1_GID`. |
| `L3_GID` | Identifiant GADM de niveau 3 | Texte | Vérifié | Clé de regroupement | Absent pour 98,47 % des lignes, de manière structurelle puisque seules les lignes de `level` 3 en disposent. |

### Culture et calendrier

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `crop` | Nom harmonisé de la culture | Texte | Documenté, article p. 4 | Candidate | |
| `season_name` | Nom de la saison agricole | Texte | Déduit | À investiguer | 34 modalités hétérogènes telles que `Main`, `Annual`, `Total`, `Meher` ou `Gu`. À harmoniser entre saison principale, saison secondaire et total annuel. |
| `planting_year` | Année de plantation | Entier | Déduit | À investiguer | Définition de l'année à harmoniser entre les fichiers. |
| `planting_month` | Mois de plantation | Entier | Déduit | À investiguer | |
| `harvest_year` | Année de récolte | Entier | Documenté dans l'article | Candidate | |
| `harvest_month` | Mois de récolte | Entier | Déduit | Exclue (fuite) | À exclure si la prédiction est réalisée avant la récolte. |
| `crop_production_system` | Système de production agricole | Texte | Déduit | À investiguer | 16 modalités, dont `none` sur 57 325 lignes et une modalité agrégeant tous les systèmes qui coexiste avec un système détaillé dans 118 cellules. |

### Surface, production et rendement

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `areaHa` | Surface récoltée | Décimal, ha | Vérifié | Exclue (fuite) | Permutée avec `productionTon` sur 33 740 lignes. Code -999 sur 112 lignes `AgroMAPS`. |
| `productionTon` | Production agricole | Décimal, t | Vérifié | Exclue (fuite) | Permutée avec `areaHa` sur 33 740 lignes. Code -999 sur 117 lignes `AgroMAPS` et code -99 sur 21 lignes `RCeA`. |
| `yieldTonHa` | Rendement agricole | Décimal, t/ha | Vérifié | Cible recommandée | Égal à la production divisée par la surface pour 126 696 lignes et au rapport inverse pour 33 740 lignes où les colonnes sont permutées. Le rendement reste plausible dans les deux cas. 30 valeurs négatives issues du code -999 et 36 valeurs -99. |

### Contrôle qualité et provenance

| Colonne | Définition | Type / unité | Statut | Rôle | Remarque |
|---|---|---|---|---|---|
| `QC_flag_A` | Indicateur de contrôle qualité associé à la surface | Code | Déduit | Exclue (métadonnée) | Codes `A`, `E`, `I`, `M` et `X` compatibles avec la nomenclature FAOSTAT. Absent pour toute la source `AgroMAPS`. |
| `QC_flag_P` | Indicateur de contrôle qualité associé à la production | Code | Déduit | Exclue (métadonnée) | Même nomenclature que `QC_flag_A`. |
| `QC_flag_Y` | Indicateur de contrôle qualité associé au rendement | Code | Vérifié | Exclue (métadonnée) | Informatif uniquement pour `FAOSTAT`. Toujours `A` pour les autres sources. 706 valeurs manquantes déguisées sous la forme `[]`. |
| `Source` | Source des statistiques | Texte | Vérifié | À investiguer | Six sources aux périodes distinctes. `FAO_subnational` et `HarvestStat` divergent de 17,5 % en médiane sur les cellules communes. |
| `originalname` | Nom original de la culture avant harmonisation | Texte | Déduit | Exclue (métadonnée) | Conservé pour la traçabilité. |

---

## 6. Synthèse des rôles

| Rôle | Colonnes concernées |
|---|---|
| Cibles candidates | `yieldTonHa` de `regional` aux niveaux 1 et 2 pour la généralisation spatiale et temporelle. `YieldUsingGPS_ton_ha_` de `survey` à l'échelle de la parcelle. `Yield_ton_ha_` de `cropcut` comme référence de validation en Éthiopie. Recommandation à valider par le porteur du projet. |
| Clés de regroupement | `L0_GID`, `L1_GID`, `L2_GID`, `L3_GID`, pays, `admin_1`, `admin_2`, identifiants de ménage, parcelle, champ, exploitant et site. |
| Variables explicatives possibles | Culture, année (`harvest_year`, `HarvestYear`, `AgYearStart`, `AgYearEnd`) et éventuellement système de production ou source, sous réserve des tests d'ablation. |
| Variables exclues pour risque de fuite | Production, surfaces et poids de récolte lorsqu'ils entrent dans le calcul de la cible ; dates et mois de récolte non disponibles au moment de la prédiction ; variantes de rendement non retenues. |
| Variables à documenter | `prcLeft`, `season_name` et `crop_production_system`. La définition de `YieldEst2_ton_ha_` en Tanzanie et la nomenclature des indicateurs `QC_flag` restent à confirmer. |

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
| Les rendements manquants de `survey` résultent surtout du filtrage des valeurs aberrantes par les auteurs. | Ne pas les imputer ni les recalculer et documenter la troncature de la distribution. |
| Surface et production sont permutées sur 33 740 lignes de `regional`. | Permuter les deux colonnes sur ces lignes avant toute pondération ou agrégation. |
| Les codes -999 et -99 se propagent jusqu'au rendement. | Convertir les codes en valeurs manquantes et invalider les rendements négatifs. |
| Des valeurs manquantes sont déguisées sous la forme `[]`, `none` ou d'un caractère BOM. | Normaliser les chaînes avant tout calcul, toute jointure et tout regroupement. |
| Certains identifiants sont tronqués par la limite de 15 chiffres d'Excel ou par la notation scientifique. | Reconstruire le ménage par `holder_id // 100` et prévoir un regroupement géographique de repli. |
| Les observations sont regroupées en grappes spatiales et en panels de ménages. | Construire les partitions par groupe spatial, par ménage et par période. |
| Les identifiants pays du Ghana et la hiérarchie GADM associée sont incohérents. | Corriger `L0_GID`, `L1_GID` et `L2_GID` du Ghana avant toute agrégation par pays. |
| Les dates de `cropcut` relèvent probablement du calendrier éthiopien. | Ne pas les convertir en dates grégoriennes sans conversion de calendrier. |
| Les sources mesurent le rendement avec des biais différents. | Ne pas fusionner les fichiers sans variable de type de source ni correction de biais. |
