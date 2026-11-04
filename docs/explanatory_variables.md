# Proposition de variables explicatives pour GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, retour en Data Understanding et Data Preparation pour l'acquisition de données externes |
| Code | `src/features/` et les tests correspondants dans `tests/` |
| Notebooks de référence | `notebooks/05_explanatory_variables.ipynb`, `06_climate_variables.ipynb`, `07_soil_variables.ipynb` et `08_terrain_variables.ipynb` |
| Documents associés | `docs/evaluation_protocol.md` et `docs/data_preparation.md` |
| Statut | Premier lot acquis et contrôlé, avec la géographie, les variables climatiques de saison, les sols et le relief |

## 1. Objet du document

Les jeux préparés ne contiennent que la cible, la culture, le lieu, la saison et l'année. Ce document examine les contraintes que les données imposent au choix des variables explicatives, compare les sources candidates et propose un premier lot à acquérir. Les caractéristiques des sources externes proviennent de leur documentation publique et devront être confirmées lors de l'acquisition.

## 2. Contraintes établies sur les données

### 2.1 Raccordement géographique

**Constat**

- Les identifiants `L1_GID` et `L2_GID` sont des codes propres à GROW-Africa, comme `L2BEN02140`, et non des identifiants GADM.
- La version 2.0 de l'archive Zenodo, publiée le 12 août 2025, fournit une table de correspondance entre ces codes et les identifiants GADM officiels. Son archive de données porte la même empreinte MD5 que celle de la version 1.0. Les rendements sont donc identiques d'une version à l'autre.
- La version 2.0 ne fournit plus les contours, qui doivent être téléchargés depuis le site de GADM sous sa licence propre.
- Toutes les zones de niveau 1 et de niveau 2 de `regional_modelisation` trouvent une correspondance, à l'exception de 5 zones du Lesotho, soit 22 lignes, dépourvues d'identifiant GADM de niveau 2.
- Les coordonnées de `survey` sont déplacées de 0 à 5 km pour protéger l'anonymat des ménages, selon la documentation de la base. 13 558 lignes du jeu de modélisation n'ont pas de coordonnées, dont 135 dont la position était codée par une latitude et une longitude nulles.

**Conséquences pour la suite**

- Les contours GADM et la table de correspondance de la version 2.0 doivent être acquis en premier. La section 8 établit que la table vise GADM 4.1.
- Les variables de `regional` sont agrégées sur le contour de la zone. Les 22 lignes du Lesotho utilisent le contour de leur région de niveau 1.
- Les variables de `survey` sont agrégées dans un rayon de 5 km autour de la grappe, ce qui couvre l'incertitude du déplacement. Sans coordonnées, le contour de niveau 2 sert de repli.

### 2.2 Couverture temporelle

**Constat**

| Jeu | Période | Lignes antérieures à 1981 | Lignes antérieures à 2001 |
|---|---|---:|---:|
| `regional_modelisation` | 1960 à 2023 | 3 542, soit 2,4 % | 44 654, soit 30,6 % |
| `survey_modelisation` | 2005 à 2022 | Aucune | Aucune |
| `cropcut_validation` | 2012 à 2019 | Aucune | Aucune |

**Analyse**

Les précipitations satellitaires de référence pour l'Afrique commencent en 1981 et les indices de végétation à 250 m en 2000. Une variable issue de ces sources serait absente pour une part de `regional` qui dépend de sa date de début.

### 2.3 Calendrier cultural

**Constat**

Les mois de semis et de récolte sont renseignés pour toutes les lignes `HarvestStat` de `regional_modelisation`, soit 81,1 % du jeu, et pour aucune ligne des autres sources.

**Conséquences pour la suite**

Les fenêtres de saison s'appuient sur ces mois lorsqu'ils existent. Pour les autres lignes et pour `survey`, un calendrier cultural externe par culture et par lieu est nécessaire. La section 11 établit que l'année de semis publiée n'est pas fiable et qu'un calendrier `HarvestStat` voisin est préférable au calendrier externe.

## 3. Décision préalable sur l'horizon de prédiction

Le Business Understanding impose de distinguer les informations disponibles au moment de la prédiction, sans fixer ce moment. Deux scénarios sont possibles.

| Scénario | Variables admissibles | Usage |
|---|---|---|
| Estimation en fin de saison | Toutes les conditions observées jusqu'à la récolte | Estimer un rendement avant la publication des statistiques officielles |
| Prévision en cours de saison | Conditions observées jusqu'à une date fixée avant la récolte | Alerte précoce |

L'estimation en fin de saison est recommandée comme scénario principal. Elle constitue la borne supérieure de la performance atteignable et sert de point de comparaison à toute prévision ultérieure. Le scénario de prévision peut être ajouté ensuite en tronquant les mêmes séries.

## 4. Sources candidates

### 4.1 Climat

| Source | Résolution | Période | Pas de temps | Intérêt | Limite |
|---|---|---|---|---|---|
| CHIRPS | 0,05° | Depuis 1981 | Journalier | Précipitations validées sur l'Afrique, combinant satellite et stations | Aucune donnée avant 1981 |
| AgERA5 | 0,1° | Depuis 1979 | Journalier | Températures extrêmes, rayonnement, humidité et vent prêts pour l'agronomie | Réanalyse, moins précise pour les précipitations |
| ERA5-Land | 0,1° | Depuis 1950 | Horaire | Humidité du sol et évapotranspiration, couverture des années 1960 et 1970 | Volume important, précipitations de réanalyse |
| TerraClimate | Environ 4 km | Depuis 1958 | Mensuel | Bilan hydrique et indice de sécheresse sur toute la période | Pas de temps mensuel, insuffisant pour les épisodes secs |

### 4.2 Sols et relief

| Source | Résolution | Intérêt | Limite |
|---|---|---|---|
| SoilGrids 2.0 | 250 m | Texture, carbone organique, pH, capacité d'échange, cohérence mondiale | Incertitude élevée en Afrique |
| iSDAsoil | 30 m | Produit propre à l'Afrique, avec phosphore et potassium | Couverture limitée au continent, ce qui suffit ici |
| Copernicus DEM | 30 m | Altitude et pente | Effet indirect sur le rendement |

### 4.3 Végétation observée par satellite

| Source | Résolution | Période | Intérêt | Limite |
|---|---|---|---|---|
| MODIS NDVI et EVI | 250 m | Depuis 2000 | Réponse directe de la culture, résolution adaptée aux régions | Absent pour 30,6 % de `regional` |
| GIMMS NDVI | Environ 8 km | Depuis 1982 | Couverture longue | Résolution grossière |
| GOSIF | 0,05° | Depuis 2000 | Fluorescence liée à la photosynthèse, utilisée par les auteurs de GROW-Africa | Produit dérivé, mêmes limites de période que MODIS |

### 4.4 Masques et calendriers

| Source | Rôle |
|---|---|
| Digital Earth Africa cropland extent, à 10 m | Pondérer les pixels par la présence de cultures, comme le font les auteurs de GROW-Africa |
| ESA WorldCover, à 10 m | Alternative au masque précédent |
| MapSPAM | Superficie par culture, pour une pondération propre à chaque culture |
| Calendrier GGCMI phase 3, à 0,5° | Dates de semis et de récolte par culture pour les lignes sans calendrier |

## 5. Proposition

### 5.1 Premier lot

| Famille | Source | Variables construites sur la fenêtre de saison |
|---|---|---|
| Géographie | GADM et table de correspondance de la version 2.0 | Contours, surface, latitude et longitude du centroïde |
| Précipitations | CHIRPS | Cumul, nombre de jours de pluie, plus longue séquence sèche, anomalie par rapport à la normale |
| Température et rayonnement | AgERA5 | Moyennes des minimales et des maximales, degrés-jours de croissance, degrés-jours au-delà de 30 et de 35 °C, rayonnement cumulé, déficit de pression de vapeur |
| Sols | iSDAsoil, ou SoilGrids pour la cohérence mondiale | Texture, carbone organique, pH, azote total, capacité d'échange cationique |
| Relief | Copernicus DEM | Altitude et pente moyennes |
| Pondération | Digital Earth Africa cropland extent | Moyenne pondérée par la fraction cultivée de chaque pixel |
| Calendrier | Mois de `HarvestStat`, puis GGCMI phase 3 | Début et fin de la fenêtre de saison |

### 5.2 Conséquences sur le périmètre

- La modélisation de `regional` est restreinte aux années de récolte postérieures ou égales à 1981. Cette restriction écarte 3 542 lignes, soit 2,4 % du jeu, et évite de mélanger des lignes avec et sans précipitations satellitaires.
- La végétation MODIS est réservée à un second lot, évalué comme variante du modèle sur les années postérieures ou égales à 2001.

### 5.3 Règles de construction

- Les normales climatiques servant aux anomalies sont calculées sur la période fixe 1981 à 2010, antérieure à la période future du protocole d'évaluation.
- Aucune variable n'utilise d'information postérieure à la récolte.
- Les variables de sol et de relief sont statiques et ne posent pas de risque de fuite temporelle.
- Chaque fichier acquis est enregistré avec sa source, sa version, sa date de téléchargement et son empreinte SHA-256.

## 6. Infrastructure

Deux organisations sont possibles.

| Option | Principe | Avantage | Inconvénient |
|---|---|---|---|
| Google Earth Engine | Agrégation côté serveur, seuls les résultats tabulaires sont téléchargés | Aucun volume local, catalogue comprenant CHIRPS, ERA5-Land et MODIS | Compte requis, contours GADM à importer, AgERA5 et iSDAsoil à vérifier dans le catalogue |
| Traitement local | Téléchargement des rasters, puis agrégation avec des bibliothèques Python spécialisées | Indépendance totale et reproductibilité complète | Plusieurs dizaines de gigaoctets et nouvelles dépendances à installer |

## 7. Décisions

Les décisions suivantes ont été arrêtées le 3 novembre 2026 sur délégation du porteur du projet, en retenant les options recommandées.

1. Le scénario principal est l'estimation en fin de saison.
2. La modélisation de `regional` est restreinte aux années de récolte postérieures ou égales à 1981.
3. Le premier lot est celui de la section 5.1, et la végétation est reportée au second lot. Les sols proviennent de SoilGrids 2.0 dans sa version agrégée à 1 km, plutôt que d'iSDAsoil à 30 m. Cette version se lit à distance par fenêtres, sans téléchargement complet, et son serveur publie les empreintes de ses fichiers.
4. L'extraction est réalisée localement, aucun compte Google Earth Engine n'étant configuré sur le poste. Les bibliothèques geopandas, pyogrio, shapely, pyproj, rasterio et requests ont été ajoutées à `requiremnts.txt` avec leur version exacte.

## 8. Géographie

**Constat**

- La table de correspondance, dont l'empreinte MD5 coïncide avec celle publiée par Zenodo, et les contours GADM 4.1 des 45 pays de `regional_modelisation` ont été acquis, soit 46 fichiers et 622,9 Mo.
- Dans ces 45 pays, les 741 codes GADM de niveau 1 et les 6 377 codes GADM de niveau 2 de la table existent dans GADM 4.1 et y portent le même nom. Les 80 codes sans unité GADM appartiennent tous au Lesotho, pour lequel GADM 4.1 ne fournit aucun niveau 2.
- Les 1 682 zones de `regional_modelisation` reçoivent un contour. 22 lignes du Lesotho reçoivent celui de leur région de niveau 1. 8 zones ghanéennes de `RCeA`, soit 130 lignes, réunissent les deux districts GADM issus de la division d'un même district, et leur contour est l'union des deux.
- 88 lignes de `regional_modelisation` déclarent une surface récoltée supérieure à la surface de leur zone. À Kigali, d'une superficie de 729 km², `RCeA` attribue à la banane et au manioc des surfaces de 543 000 à 617 000 ha. Au Sénégal, `FAO_subnational` attribue 2,4 millions d'hectares de mil à la région de Kaolack.
- Les grappes de `survey` tombent toutes à l'intérieur du contour de leur zone, alors qu'une zone tirée au hasard n'en contient que 0,4 %. 1 085 lignes de `survey` n'ont ni identifiant géographique ni coordonnées.

**Analyse**

- La table vise GADM 4.1, ce qui clôt la question ouverte depuis le Data Understanding.
- Un dépassement de la surface de la zone est physiquement impossible au cours d'une saison. Les surfaces attribuées à Kigali sont de l'ordre de celles du pays entier et suggèrent des valeurs nationales rattachées à une seule zone. Le filtre de plausibilité ne pouvait pas les détecter, car leur rendement reste plausible.
- L'accord parfait entre grappes et zones indique que les identifiants de `survey` ont été déduits des coordonnées déjà déplacées. Il confirme la cohérence interne de la base sans garantir l'exactitude des coordonnées.

**Décisions**

- Les 88 lignes sont signalées par la fonction `signaler_surface_superieure_zone` et seront exclues de l'entraînement comme de l'évaluation. Elles restent dans `regional_modelisation`, car le contrôle dépend des contours, acquis après la préparation.
- La surface de la zone et les coordonnées de son centroïde, calculées dans une projection à surfaces équivalentes, forment les premières variables explicatives statiques. Elles sont écrites dans `data/processed/geographie_regional.csv.gz`, et les contours dans `zones_regional.gpkg` et `zones_survey.gpkg`.

## 9. Obstacles à l'acquisition du climat

**Constat**

| Source | Constat du 3 novembre 2026 | Conséquence |
|---|---|---|
| CHIRTS-daily | Les températures journalières couvrent 1983 à 2016 seulement | Inutilisable, car la période future du protocole commence en 2017 |
| AgERA5 | Le téléchargement exige un compte Copernicus Climate Data Store, absent du poste | Bloqué sans action du porteur du projet |
| CHIRPS | Le serveur du Climate Hazards Center n'a délivré que 110 ko en quinze minutes depuis ce poste. L'archive journalière de l'Afrique à 0,05° représente environ 13 Go | Téléchargement local impossible à ce débit |
| CHIRPS par l'IRI Data Library | L'extraction côté serveur fonctionne, mais avec un débit de 26 ko par seconde, soit plus de 50 heures pour l'Afrique à 0,25° | Impraticable |
| NASA POWER | La série journalière 1981 à 2023 de sept variables d'une maille s'obtient en 4 secondes, sans compte | Faisable localement |
| SoilGrids 2.0 | Une fenêtre de 512 par 512 pixels se lit à distance en environ une seconde | Faisable localement |

**Analyse**

Le traitement local reste adapté aux données statiques, comme la géographie et les sols. Il ne l'est pas pour les séries climatiques journalières, dont le volume est incompatible avec le débit observé. L'agrégation côté serveur de Google Earth Engine supprime ce volume, puisque seules les moyennes par zone sont téléchargées. Son catalogue contient CHIRPS journalier et ERA5-Land journalier, qui fournit les températures sur toute la période.

**Décision**

Le 3 novembre 2026, sur délégation du porteur du projet, le climat est acquis auprès de NASA POWER, seule source sans compte dont le débit permet l'acquisition depuis ce poste. Les séries proviennent de la réanalyse MERRA-2, sur une grille de 0,5 degré de latitude par 0,625 degré de longitude, et du produit CERES pour le rayonnement.

| Variable POWER | Contenu | Usage prévu |
|---|---|---|
| `T2M_MAX` et `T2M_MIN` | Températures maximale et minimale à 2 m | Degrés-jours de croissance et degrés-jours au-delà de 30 et de 35 °C |
| `T2MDEW` | Point de rosée à 2 m | Déficit de pression de vapeur |
| `PRECTOTCORR` | Précipitations corrigées par les pluviomètres | Abandonné au profit d'IMERG, voir la section 10 |
| `ALLSKY_SFC_SW_DWN` | Rayonnement solaire incident | Rayonnement cumulé |
| `WS2M` | Vent à 2 m | Évapotranspiration de référence |
| `GWETROOT` | Humidité du sol dans la zone racinaire | Abandonné, voir la section 10 |

7 363 mailles recoupent une zone de `regional`, une zone de `survey` ou le voisinage de 5 km d'une grappe. La valeur d'une zone sera la moyenne de ses mailles pondérée par la surface de leur intersection avec la zone.

**Limites**

- La résolution de 0,5 degré convient à la température, dont le champ varie lentement, mais lisse les précipitations. Les précipitations de MERRA-2 sont moins fiables que celles de CHIRPS en Afrique, notamment pour les épisodes secs localisés.
- Le rayonnement CERES n'est disponible qu'à partir de 1984. Les variables qui en dépendent seront manquantes pour les saisons antérieures.
- Les séries commencent le 1er janvier 1981. Une saison récoltée en 1981 mais semée en 1980 n'est couverte qu'en partie.

**Décision du porteur du projet**

Le 3 novembre 2026, le porteur du projet a renoncé à Google Earth Engine. Les précipitations de NASA POWER sont donc retenues comme source définitive, et CHIRPS est abandonné. Leur moindre précision constitue une limite du projet, qui devra être rappelée dans l'interprétation des modèles et de l'importance des variables de pluie. Le contrôle du 4 novembre 2026, décrit à la section 10, conduit à retenir le produit IMERG diffusé par NASA POWER plutôt que `PRECTOTCORR`.

## 10. Contrôle des séries de NASA POWER

**Constat**

- Le téléchargement s'est achevé le 4 novembre 2026, sans échec. Chacune des 7 363 mailles couvre les 15 705 jours du 1er janvier 1981 au 31 décembre 2023, et chaque fichier correspond à son entrée du registre par sa taille et son empreinte SHA-256.
- Températures, point de rosée, précipitations et vent sont complets. Le rayonnement manque avant 1984, comme prévu, et pour quelques jours isolés de 49 mailles entre 1985 et 1996, soit au plus 0,089 % des jours d'une maille. `GWETROOT` manque entièrement pour 11 mailles situées en mer, sur une côte ou sur le lac Victoria, car cette variable n'est définie que sur les terres émergées.
- L'une de ces 11 mailles est centrée sur le point de latitude et de longitude nulles, en mer. Elle n'a été téléchargée qu'à cause des 135 parcelles de `survey` dont la position absente était codée par ce point, et elle n'est plus utilisée depuis l'invalidation de ces coordonnées.
- Les températures extrêmes restent plausibles, avec un minimum de -17,7 °C sur les hauts plateaux du Lesotho et un maximum de 51,7 °C dans le Sahara algérien.
- `PRECTOTCORR` contient des cumuls journaliers impossibles. 205 mailles comptent au moins un jour au-delà de 500 mm et 542 au-delà de 300 mm. Le maximum atteint 2 581 mm le 21 mars 2022 dans le sud-ouest de l'Angola, et 2 533 mm le 12 octobre 2020 dans le nord de la Mauritanie, dans une maille dont le cumul annuel moyen est de 137 mm.
- Ces anomalies se concentrent à partir de 2020. Le nombre de jours au-delà de 200 mm, toutes mailles réunies, ne dépasse pas 91 par an de 1981 à 2019, puis atteint 610 en 2020, 427 en 2021, 382 en 2022 et 281 en 2023. Le cumul annuel médian des mailles passe de 594 mm en 2019 à 776 mm en 2020.
- NASA POWER ne diffuse pas de précipitations non corrigées, car l'API rejette `PRECTOT` comme un doublon de `PRECTOTCORR`. Elle diffuse en revanche le produit satellitaire IMERG à 0,1°, en temps universel, à partir du 1er juin 2000.
- Sur 43 mailles, soit 40 tirées au hasard et les 3 mailles les plus extrêmes, la comparaison des deux produits de 2001 à 2023 donne les résultats suivants.

| Mesure | 2001 à 2006 | 2007 | 2008 à 2019 | 2020 à 2022 | 2023 |
|---|---|---|---|---|---|
| Rapport des précipitations moyennes de `PRECTOTCORR` et d'IMERG, jours au-delà de 200 mm exclus | 0,80 à 0,92 | 1,19 | 0,92 à 1,04 | 1,11 à 1,20 | 0,97 |
| Corrélation des rangs des cumuls journaliers | 0,65 à 0,67 | 0,67 | 0,65 à 0,69 | 0,67 à 0,68 | 0,68 |

- En temps universel, les journées de 2 532, 2 501 et 1 817 mm relevées dans `PRECTOTCORR` aux centres des trois mailles les plus extrêmes correspondent à 3,3, 1,3 et 0 mm dans IMERG.
- Sur l'ensemble des mailles, pics compris, le rapport des cumuls annuels moyens de `PRECTOTCORR` et d'IMERG vaut 0,83 à 0,88 de 2001 à 2006, 0,95 à 1,07 de 2007 à 2019, 1,28 à 1,33 de 2020 à 2022 et 1,14 en 2023. IMERG compte entre 2 et 34 jours au-delà de 200 mm par an, sans tendance.
- Par rapport à sa moyenne de 2001 à 2019, `GWETROOT` présente sur 800 mailles tirées au hasard des écarts de +0,031, +0,026 et +0,027 en 2020, 2021 et 2022, les plus élevés depuis 1995. Les autres variables ne présentent pas de rupture comparable.

**Analyse**

- Les cumuls de plusieurs milliers de millimètres en un jour sont physiquement impossibles, et IMERG n'enregistre aucun épisode notable aux mêmes dates dans les trois mailles examinées. Il s'agit d'artefacts du produit.
- Au-delà de ces pics, l'intensité de `PRECTOTCORR` n'est pas homogène dans le temps par rapport à IMERG, alors que la chronologie des épisodes pluvieux reste aussi bien restituée d'une année à l'autre. L'excès de 11 à 20 % de 2020 à 2022 tombe dans les périodes futures du protocole, qui commencent en 2017 pour `regional` et comprennent les vagues 2021 et 2022 de `survey`, soit 24 423 parcelles. Un modèle entraîné sur les années antérieures y verrait des saisons artificiellement humides et en tirerait des prédictions biaisées.
- La documentation de NASA POWER ne signale aucun changement de source en 2020, et la cause de la rupture n'est pas identifiée. La comparaison établit l'incohérence de `PRECTOTCORR`, sans démontrer l'exactitude d'IMERG, dont la stabilité sur l'échantillon reste toutefois cohérente avec un produit homogène.
- `GWETROOT` est calculé par le modèle de surface de MERRA-2 à partir des précipitations corrigées. L'excès de 2020 à 2022 se retrouve dans son humidité record, alors qu'IMERG décrit 2021 et 2022 comme des années plutôt sèches sur l'échantillon.

**Décisions**

- Les précipitations proviennent d'IMERG, diffusé par NASA POWER sous le nom `IMERG_PRECTOT`, interrogé au centre de chacune des mailles déjà retenues. La source NASA POWER arrêtée par le porteur du projet est conservée et seul le produit change.
- `PRECTOTCORR` et `GWETROOT` restent dans les fichiers téléchargés mais ne servent à aucune variable explicative. Le stress hydrique est mesuré par un bilan entre les précipitations d'IMERG et l'évapotranspiration de référence FAO-56, calculée dans chaque maille à partir des températures, du point de rosée, du rayonnement, du vent et de l'altitude.
- Les saisons antérieures à juin 2000 n'ont pas d'indicateur de précipitations. Elles concernent 44 654 lignes de `regional_modelisation` récoltées avant 2001, contre 101 223 à partir de 2001. Le choix entre restreindre les modèles climatiques aux récoltes postérieures à 2000 et conserver les années antérieures avec des précipitations manquantes sera tranché par validation croisée lors de la modélisation.

**Limites**

- IMERG est diffusé en temps universel et les autres variables en temps solaire local. L'écart n'excède pas 3 h 30 sur les longitudes couvertes. Il est sans effet sur les cumuls saisonniers mais peut déplacer un épisode pluvieux sur le jour voisin dans le calcul des séquences sèches.
- La valeur interrogée au centre d'une maille est celle d'un pixel IMERG de 0,1°, et non la moyenne de la maille. La moyenne d'une zone constitue donc un échantillonnage de la zone, d'autant plus bruité que la zone recoupe peu de mailles.

## 11. Fenêtres de saison et indicateurs climatiques

**Constat**

- L'année de semis publiée par `HarvestStat` contredit les mois de semis et de récolte pour 17 045 des 118 333 lignes qui en disposent, dont 8 499 au Malawi, 3 574 à Madagascar, 1 959 au Soudan, 1 382 au Niger à partir de 2011 et 1 301 en Afrique du Sud. Les erreurs sont de sens opposés selon les pays.
- L'année de récolte retrouve les sécheresses connues. Le rendement du maïs s'écarte de -1,11 en logarithme de la moyenne de sa zone pour la récolte de 1992 au Malawi et de -0,88 en Afrique du Sud, et la saison 1984 se lit en 1984 au Soudan et au Niger.
- Les différences annuelles du logarithme du rendement ont été corrélées avec celles du climat de la fenêtre de saison, pour l'année de récolte et pour les années voisines. La fenêtre de l'année de récolte donne la corrélation la plus négative avec la température maximale dans 18 des 24 pays testés, la plus positive avec la pluie dans 17 pays, et les deux à la fois dans 15 pays. Au Lesotho, les deux variables désignent l'année suivante, avec -0,119 pour la température et 0,191 pour la pluie.
- Dans `survey`, la même démarche appliquée à la pluie, après retrait des effets fixes de zone et de vague, confirme la fin de campagne au Malawi et le début de campagne en Ouganda, au Togo, au Mali et au Sénégal. Elle désigne le début de campagne en Tanzanie, alors que le calendrier annuel `HarvestStat` de septembre à juillet y conduirait à la fin de campagne. Elle désigne aussi le début de campagne en Éthiopie, avec 0,111 contre -0,016, et la fin de campagne au Niger sur 184 cellules seulement. Une analyse exploratoire fondée sur la température, non reprise dans le notebook, ne distinguait aucune hypothèse dans `survey`.
- Une comparaison exploratoire des écarts de rendement de `survey` et de `regional` dans les mêmes régions, non reprise dans le notebook, désignait déjà le début de campagne en Éthiopie, avec une corrélation de 0,67 contre 0,41, et en Tanzanie.
- Sur les lignes `HarvestStat`, le calendrier dominant d'une autre culture de la même région retrouve 96 % des mois de semis et de récolte à un mois près, contre 55 % pour le calendrier GGCMI de phase 3 de la même culture. GGCMI place par exemple le semis de l'arachide du Zimbabwe en juin, en saison sèche.

**Analyse**

- L'année de récolte de `HarvestStat` est fiable et son année de semis ne l'est pas. Le Lesotho fait exception, son année de récolte désignant l'année de semis selon deux variables indépendantes.
- En Éthiopie, le résultat de `survey` signifierait que la vague de 2015 mesure la saison principale de 2014, ce qui contredit le déroulement de l'enquête, dont le passage après récolte a lieu au début de l'année de fin de campagne. Au Niger, l'hypothèse de fin de campagne placerait la saison mesurée après l'enquête elle-même, ce qui est impossible.
- Les calendriers `HarvestStat` décrivent avant tout la saison des pluies d'une région, commune à la plupart des cultures, ce qui explique la fiabilité du calendrier dominant.

**Décisions**

- La fenêtre de saison va du premier jour du mois de semis au dernier jour du mois de récolte. Elle s'achève l'année de récolte et commence l'année précédente lorsque le mois de semis suit le mois de récolte. Les fenêtres des lignes `HarvestStat` du Lesotho sont décalées d'un an.
- Dans `survey`, la saison commence par le semis de l'année de début de campagne et s'achève à la récolte qui suit, sauf en Tanzanie, où elle s'achève l'année de début de campagne. `annee_recolte` n'est pas modifiée, car le décalage est constant au sein d'un pays.
- Le conflit éthiopien est consigné comme anomalie non résolue et fera l'objet d'une analyse de sensibilité lors de la modélisation.
- Une ligne sans mois reçoit, par ordre de priorité, le calendrier `HarvestStat` principal de sa zone, de sa région ou de son pays pour la même culture, puis le calendrier dominant de sa région ou de son pays toutes cultures confondues, et enfin le calendrier GGCMI au centroïde de son lieu. Le niveau retenu est conservé dans `source_calendrier`.
- Le lieu d'une ligne de `regional` est sa zone. Celui d'une parcelle de `survey` est le voisinage de 5 km de sa grappe lorsque ses coordonnées sont connues, sinon sa zone de repli. La série d'un lieu est la moyenne de ses mailles pondérée par la surface de leur intersection avec le lieu, une maille sans valeur un jour donné étant ignorée ce jour-là.
- Les indicateurs de chaque fenêtre sont le cumul de pluie, le nombre de jours d'au moins 1 mm, la plus longue séquence sans pluie, le bilan entre la pluie et l'évapotranspiration de référence FAO-56, les degrés-jours au-delà de 10 °C avec une température moyenne plafonnée à 30 °C, les degrés-jours de température maximale au-delà de 30 et de 35 °C, les températures maximale et minimale moyennes, le déficit moyen de pression de vapeur, le rayonnement moyen et l'évapotranspiration cumulée. Un indicateur est manquant dès qu'un jour de sa fenêtre manque.

**Résultats**

| Élément | `regional` | `survey` |
|---|---:|---:|
| Lignes | 145 877 | 151 138 |
| Mois propres à la ligne | 118 333 | 0 |
| Calendrier de la même culture | 20 324 | 145 426 |
| Calendrier dominant toutes cultures | 2 127 | 4 056 |
| Calendrier GGCMI | 4 680 | 1 571 |
| Sans calendrier | 413 | 85 |
| Lignes sans aucun indicateur | 413 et les saisons antérieures à 1981 | 1 170, dont 1 085 sans localisation |

Pour les récoltes postérieures à 2000, la pluie couvre 99,3 % des lignes de `regional` et la température 99,6 %. Pour les récoltes de 1982 à 2000, la température couvre 99,9 % des lignes et la pluie 3,3 %. Dans `survey`, 99,2 % des parcelles reçoivent tous les indicateurs. Les 1 450 saisons de `regional` à moins de 100 mm de pluie relèvent surtout de cultures irriguées, de décrue ou riveraines.

**Limites**

- GGCMI reste le seul calendrier disponible au Ghana, en Guinée, en Afrique du Nord et en Gambie, soit 4 680 lignes de `regional`, avec une fiabilité mesurée de 55 % à un mois près.
- Les tests d'alignement de `survey` reposent sur deux à huit vagues par pays, et l'alignement de l'Éthiopie n'est pas établi.
- Les années de récolte choisies pour le Lesotho et la Tanzanie l'ont été au vu de corrélations calculées sur toutes les années, périodes futures comprises. Ce choix porte sur un seul paramètre par pays et ne concerne pas les modèles, mais il constitue un usage limité des périodes de test.

## 12. Sols

**Constat**

- La version à 1 km de SoilGrids 2.0 ne contient pas le pH. Pour les huit autres propriétés retenues, elle est identique pixel à pixel au premier aperçu de la mosaïque à 250 m, fichier que SoilGrids publie aussi pour le pH, avec son empreinte.
- L'empreinte SHA-256 publiée par ISRIC porte sur le fichier complet et ne peut pas vérifier une lecture à distance par fenêtres. Le serveur limite chaque connexion à 0,4 Mo par seconde environ, mais plusieurs connexions simultanées en multiplient le débit.
- Les 27 couches, neuf propriétés à trois profondeurs de 0 à 30 cm, ont été téléchargées en entier, soit 4,68 Go, et toutes ont l'empreinte publiée. Les découpages conservés occupent 787 Mo.
- La version à 1 km n'est pas exactement la moyenne des 16 pixels à 250 m qu'elle recouvre. Le meilleur accord est obtenu en décalant les blocs de 500 à 1 000 m vers l'ouest et de 750 m vers le nord, sans annuler l'écart. À l'échelle de carrés de 5 km, la corrélation avec la moyenne exacte à 250 m est comprise entre 0,94 et 0,99 sur trois sites et trois propriétés.
- Quatre zones urbaines de `regional`, Accra, Ledzokuku et Tema au Ghana et Dakar au Sénégal, n'ont aucun pixel valide, car SoilGrids exclut les villes et les plans d'eau. Elles portent 68 lignes. Dans `survey`, trois grappes de Dar es Salaam sont dans le même cas.
- Le pH des zones décroît avec leur pluie de saison, avec une corrélation de rang de -0,61. Le carbone organique et l'azote ont une corrélation de rang de 0,94.

**Analyse**

- Lire le pH dans l'aperçu de sa mosaïque donne exactement la valeur qu'ISRIC aurait publiée à 1 km, ce qui garde les neuf propriétés homogènes.
- Le téléchargement complet s'écarte de la lecture par fenêtres prévue par la décision 3 de la section 7. Il est justifié par la vérification des empreintes, que la lecture par fenêtres ne permet pas, pour une durée d'une heure environ et sans encombrement durable du disque, puisque les fichiers sources sont supprimés après découpage.
- L'écart entre les versions à 1 km et à 250 m, et l'incertitude de position de l'ordre de 1 km, restent faibles devant le rayon de 5 km des voisinages, devant la taille des zones et devant l'incertitude propre de SoilGrids en Afrique.
- Les relations entre propriétés et avec la pluie sont celles qu'attend la science du sol. Elles signalent aussi qu'une part de l'information des sols est déjà portée par le climat.

**Décisions**

- La valeur d'un lieu est la moyenne des pixels dont le centre tombe dans son contour, ou des pixels qu'il touche lorsqu'il est trop petit pour contenir un centre. La projection de SoilGrids conservant les surfaces, cette moyenne est pondérée par la surface.
- Les lieux sont ceux des variables climatiques. Comme pour le climat, aucun masque des terres cultivées n'est appliqué.
- Les variables manquantes restent manquantes, et `pixels_sol` et `part_sol_valide` accompagnent chaque lieu.
- Le limon, que la fermeture de la texture rend redondant, et l'azote, très lié au carbone organique, sont conservés dans les fichiers. Leur usage sera décidé lors de la modélisation.

**Résultats**

| Variable | Contenu | Unité | Médiane des zones de `regional` |
|---|---|---|---:|
| `argile_0_30` | Part d'argile | % | 26,7 |
| `limon_0_30` | Part de limon | % | 23,1 |
| `sable_0_30` | Part de sable | % | 49,1 |
| `carbone_organique_0_30` | Carbone organique | g/kg | 14,7 |
| `azote_0_30` | Azote total | g/kg | 1,17 |
| `ph_0_30` | pH dans l'eau | Sans unité | 6,08 |
| `cec_0_30` | Capacité d'échange cationique | cmolc/kg | 13,8 |
| `densite_apparente_0_30` | Densité apparente | g/cm³ | 1,41 |
| `elements_grossiers_0_30` | Part volumique des éléments grossiers | % | 11,8 |

`sols_regional.csv.gz` contient les 1 682 zones, avec la clé `GDAM_ID`. `sols_survey.csv.gz` contient les 151 138 lignes, avec la clé `id_ligne`, et 99,28 % d'entre elles reçoivent des variables de sol, les autres étant les 1 085 lignes sans localisation et les trois grappes urbaines. Dans `regional`, 99,95 % des lignes en reçoivent.

**Limites**

- SoilGrids est une prédiction statistique, dont l'incertitude est élevée en Afrique faute de profils mesurés. Ses valeurs sont statiques et ne suivent pas l'évolution des sols de 1981 à 2023.
- ISRIC ne documente pas le calcul de sa version à 1 km, dont les contrôles montrent qu'elle approche la moyenne des pixels fins sans l'égaler.
- Les variables de `cropcut` restent à construire pour la validation externe, pour les sols comme pour le climat.

## 13. Relief

**Constat**

- Copernicus DEM GLO-90 se télécharge sans compte, en tuiles d'un degré accompagnées d'un masque des eaux, et l'empreinte MD5 de chaque fichier est publiée. Les 2 408 tuiles qui recoupent un lieu du projet et leurs masques, soit 4 816 fichiers et 10,86 Go, ont tous l'empreinte publiée.
- L'altitude moyenne de la mosaïque à 1 km s'écarte de 2 à 32 m de celle de sept villes de contrôle. Sur les 1 682 zones de `regional`, sa corrélation avec l'altitude des mailles de MERRA-2 atteint 0,992, avec un écart absolu médian de 14 m. Les plus grands écarts, jusqu'à 719 m en Érythrée, concernent des hauts plateaux que MERRA-2 abaisse en les lissant.
- Dans la cuvette congolaise, quasi plane, la pente médiane atteint 1,4 degré, contre 0,5 degré dans la plaine sahélienne du Niger.
- La pente médiane des zones dépasse 8 degrés au Lesotho, au Rwanda, au Burundi et à Madagascar, et reste inférieure à 0,5 degré au Soudan du Sud et en Namibie. La corrélation de rang entre altitude et pente des zones vaut 0,55.

**Analyse**

- La version à 90 m a été préférée à la version à 30 m mentionnée à la section 4.2. Elle est neuf fois plus légère et suffit à l'échelle des lieux du projet, dont le plus petit est un voisinage de 5 km.
- Copernicus DEM est un modèle numérique de surface. Sous la forêt dense, la hauteur variable de la canopée crée une pente apparente d'environ un degré.
- L'altitude et la pente portent des informations distinctes, ce que confirme leur corrélation modérée.

**Décisions**

- La pente est calculée à 90 m par la méthode de Horn, avec un pas est-ouest corrigé de la latitude, après exclusion de la mer, des lacs et des rivières. L'altitude et la pente sont moyennées sur la grille à 1 km des sols, chaque pixel de 90 m étant pondéré par sa surface, puis sur chaque lieu selon les règles des sols.
- Les tuiles sont supprimées après traitement. Un résumé par tuile est conservé, ce qui permet de reprendre une extraction et de reconstruire la mosaïque sans nouveau téléchargement.
- L'altitude de Copernicus DEM sert de variable explicative. Celle de MERRA-2 reste utilisée pour le calcul de l'évapotranspiration, qui doit rester cohérent avec les variables météorologiques de la même maille.

**Résultats**

| Variable | Contenu | Médiane des zones de `regional` | Médiane des grappes de `survey` |
|---|---|---:|---:|
| `altitude_moyenne` | Altitude moyenne en mètres | 387 | 610 |
| `pente_moyenne` | Pente moyenne en degrés | 2,3 | 2,0 |

`relief_regional.csv.gz` contient les 1 682 zones, toutes renseignées, avec la clé `GDAM_ID`. `relief_survey.csv.gz` contient les 151 138 lignes, avec la clé `id_ligne`, et 99,28 % d'entre elles sont renseignées, les autres étant les 1 085 lignes sans localisation.

**Limites**

- La pente des zones de forêt dense est surestimée d'un degré environ, ce qui concerne surtout le bassin du Congo et la côte guinéenne.
- La pente des pixels de 90 m situés au bord d'une tuile est calculée en prolongeant la tuile, ce qui touche 0,3 % des pixels.
- La pente moyenne ne distingue pas une zone uniformément inclinée d'une zone mêlant plaines et reliefs escarpés.

## 14. Reproductibilité

- Les fichiers externes sont téléchargés dans `data/external`, exclu du dépôt git, et consignés dans `data/external/registre.csv` avec leur adresse, leur date, leur taille et leur empreinte SHA-256.
- La table de correspondance est vérifiée par l'empreinte MD5 publiée par Zenodo.
- Le notebook de référence télécharge les fichiers manquants, construit les contours et les descripteurs, et s'exécute en moins d'une minute lorsque les fichiers sont présents.
- Les séries de NASA POWER se téléchargent avec la commande `python -m src.features.climat`. Chaque maille est compressée dans `data/external/power` et consignée dans le registre, avec l'adresse exacte de la requête.
- Les précipitations IMERG se téléchargent avec la commande `python -m src.features.climat imerg` dans `data/external/imerg`, selon les mêmes règles. Les coordonnées nulles étant désormais ignorées, cette commande interroge 7 362 mailles.
- Le calendrier GGCMI de phase 3 est téléchargé depuis Zenodo et vérifié par les empreintes MD5 publiées.
- Les séries retenues sont réunies dans `data/interim/climat`, un tableau par variable indexé par maille et par jour, par la fonction `construire_magasin` de `src/features/climat.py`. L'évapotranspiration de référence y est ajoutée par la fonction `calculer_et0` de `src/features/agregation.py`.
- La commande `python -m src.features.variables` recalcule les poids des mailles de chaque lieu et écrit `climat_regional.csv.gz` et `climat_survey.csv.gz` dans `data/processed`. La clé de `regional` est le quadruplet `GDAM_ID`, `crop`, `saison` et `harvest_year`, et celle de `survey` est `id_ligne`.
- Le notebook `06_climate_variables.ipynb` établit tous les contrôles de cette phase et s'exécute en cinq minutes environ lorsque le magasin est construit.
- Les couches de SoilGrids s'obtiennent avec la commande `python -m src.features.sols extraire`. Chaque fichier source est téléchargé en entier, comparé à l'empreinte SHA-256 publiée par ISRIC, découpé sur la fenêtre fixe `FENETRE_AFRIQUE` puis supprimé. Les découpages sont écrits dans `data/external/soilgrids` et consignés dans le registre, et les empreintes vérifiées des sources dans `data/external/soilgrids/sources.csv`.
- La commande `python -m src.features.sols construire` écrit `sols_regional.csv.gz` et `sols_survey.csv.gz` dans `data/processed` en une minute environ.
- Le notebook `07_soil_variables.ipynb` établit les contrôles des sols et s'exécute en six minutes environ, dont l'essentiel est consacré aux lectures à distance de la version à 250 m.
- Le relief s'obtient avec la commande `python -m src.features.relief extraire`, qui télécharge chaque tuile de Copernicus DEM et son masque des eaux, les compare à l'empreinte MD5 publiée, écrit un résumé dans `data/interim/relief/tuiles` puis les supprime. Les empreintes vérifiées sont consignées dans `data/external/copernicus/sources.csv`. L'extraction dure quarante minutes environ et reprend après une interruption.
- La commande `python -m src.features.relief construire` écrit la mosaïque `altitude_1km.tif` et `pente_1km.tif` dans `data/interim/relief`, puis `relief_regional.csv.gz` et `relief_survey.csv.gz` dans `data/processed`, en une minute environ.
- Le notebook `08_terrain_variables.ipynb` établit les contrôles du relief et s'exécute en moins d'une minute.
