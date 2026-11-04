# Proposition de variables explicatives pour GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, retour en Data Understanding et Data Preparation pour l'acquisition de données externes |
| Code | `src/features/` et `tests/test_geographie.py` |
| Notebook de référence | `notebooks/05_explanatory_variables.ipynb` |
| Documents associés | `docs/evaluation_protocol.md` et `docs/data_preparation.md` |
| Statut | Décisions arrêtées, géographie acquise, variables de NASA POWER acquises et contrôlées, précipitations IMERG en cours d'acquisition |

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

Les fenêtres de saison s'appuient sur ces mois lorsqu'ils existent. Pour les autres lignes et pour `survey`, un calendrier cultural externe par culture et par lieu est nécessaire.

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
- Par rapport à sa moyenne de 2001 à 2019, `GWETROOT` présente sur 800 mailles tirées au hasard des écarts de +0,031, +0,026 et +0,027 en 2020, 2021 et 2022, les plus élevés depuis 1995. Les autres variables ne présentent pas de rupture comparable.

**Analyse**

- Les cumuls de plusieurs milliers de millimètres en un jour sont physiquement impossibles, et IMERG n'enregistre aucun épisode notable aux mêmes dates dans les trois mailles examinées. Il s'agit d'artefacts du produit.
- Au-delà de ces pics, l'intensité de `PRECTOTCORR` n'est pas homogène dans le temps par rapport à IMERG, alors que la chronologie des épisodes pluvieux reste aussi bien restituée d'une année à l'autre. L'excès de 11 à 20 % de 2020 à 2022 tombe dans les périodes futures du protocole, qui commencent en 2017 pour `regional` et comprennent les vagues 2021 et 2022 de `survey`, soit 24 423 parcelles. Un modèle entraîné sur les années antérieures y verrait des saisons artificiellement humides et en tirerait des prédictions biaisées.
- La documentation de NASA POWER ne signale aucun changement de source en 2020, et la cause de la rupture n'est pas identifiée. La comparaison établit l'incohérence de `PRECTOTCORR`, sans démontrer l'exactitude d'IMERG, dont la stabilité sur l'échantillon reste toutefois cohérente avec un produit homogène.
- `GWETROOT` est calculé par le modèle de surface de MERRA-2 à partir des précipitations corrigées. L'excès de 2020 à 2022 se retrouve dans son humidité record, alors qu'IMERG décrit 2021 et 2022 comme des années plutôt sèches sur l'échantillon.

**Décisions**

- Les précipitations proviennent d'IMERG, diffusé par NASA POWER sous le nom `IMERG_PRECTOT`, interrogé au centre de chacune des mailles déjà retenues. La source NASA POWER arrêtée par le porteur du projet est conservée et seul le produit change.
- `PRECTOTCORR` et `GWETROOT` restent dans les fichiers téléchargés mais ne servent à aucune variable explicative. Le stress hydrique sera estimé par un bilan entre les précipitations d'IMERG et l'évapotranspiration de référence calculée à partir des températures, du rayonnement et du vent.
- Les saisons antérieures à juin 2000 n'ont pas d'indicateur de précipitations. Elles concernent 44 654 lignes de `regional_modelisation` récoltées avant 2001, contre 101 223 à partir de 2001. Le choix entre restreindre les modèles climatiques aux récoltes postérieures à 2000 et conserver les années antérieures avec des précipitations manquantes sera tranché par validation croisée lors de la modélisation.

**Limites**

- IMERG est diffusé en temps universel et les autres variables en temps solaire local. L'écart n'excède pas 3 h 30 sur les longitudes couvertes. Il est sans effet sur les cumuls saisonniers mais peut déplacer un épisode pluvieux sur le jour voisin dans le calcul des séquences sèches.
- La valeur interrogée au centre d'une maille est celle d'un pixel IMERG de 0,1°, et non la moyenne de la maille. La moyenne d'une zone constitue donc un échantillonnage de la zone, d'autant plus bruité que la zone recoupe peu de mailles.

## 11. Reproductibilité

- Les fichiers externes sont téléchargés dans `data/external`, exclu du dépôt git, et consignés dans `data/external/registre.csv` avec leur adresse, leur date, leur taille et leur empreinte SHA-256.
- La table de correspondance est vérifiée par l'empreinte MD5 publiée par Zenodo.
- Le notebook de référence télécharge les fichiers manquants, construit les contours et les descripteurs, et s'exécute en moins d'une minute lorsque les fichiers sont présents.
- Les séries de NASA POWER se téléchargent avec la commande `python -m src.features.climat`. Chaque maille est compressée dans `data/external/power` et consignée dans le registre, avec l'adresse exacte de la requête.
- Les précipitations IMERG se téléchargent avec la commande `python -m src.features.climat imerg` dans `data/external/imerg`, selon les mêmes règles. Les coordonnées nulles étant désormais ignorées, cette commande interroge 7 362 mailles.
