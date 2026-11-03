# Proposition de variables explicatives pour GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, retour en Data Understanding et Data Preparation pour l'acquisition de données externes |
| Documents associés | `docs/evaluation_protocol.md` et `docs/data_preparation.md` |
| Statut | Proposition soumise au porteur du projet |

## 1. Objet du document

Les jeux préparés ne contiennent que la cible, la culture, le lieu, la saison et l'année. Ce document examine les contraintes que les données imposent au choix des variables explicatives, compare les sources candidates et propose un premier lot à acquérir. Les caractéristiques des sources externes proviennent de leur documentation publique et devront être confirmées lors de l'acquisition.

## 2. Contraintes établies sur les données

### 2.1 Raccordement géographique

**Constat**

- Les identifiants `L1_GID` et `L2_GID` sont des codes propres à GROW-Africa, comme `L2BEN02140`, et non des identifiants GADM.
- La version 2.0 de l'archive Zenodo, publiée le 12 août 2025, fournit une table de correspondance entre ces codes et les identifiants GADM officiels. Son archive de données porte la même empreinte MD5 que celle de la version 1.0. Les rendements sont donc identiques d'une version à l'autre.
- La version 2.0 ne fournit plus les contours, qui doivent être téléchargés depuis le site de GADM sous sa licence propre.
- Toutes les zones de niveau 1 et de niveau 2 de `regional_modelisation` trouvent une correspondance, à l'exception de 5 zones du Lesotho, soit 22 lignes, dépourvues d'identifiant GADM de niveau 2.
- Les coordonnées de `survey` sont déplacées de 0 à 5 km pour protéger l'anonymat des ménages, selon la documentation de la base. 13 423 lignes du jeu de modélisation n'ont pas de coordonnées.

**Conséquences pour la suite**

- Les contours GADM et la table de correspondance de la version 2.0 doivent être acquis en premier. La version de GADM visée par la table reste à confirmer en comparant les identifiants et les noms.
- Les variables de `regional` sont agrégées sur le contour de la zone. Les 22 lignes du Lesotho utilisent le contour de leur région de niveau 1.
- Les variables de `survey` sont agrégées dans un rayon de 5 km autour de la grappe, ce qui couvre l'incertitude du déplacement. Sans coordonnées, le contour de niveau 2 sert de repli.

### 2.2 Couverture temporelle

**Constat**

| Jeu | Période | Lignes antérieures à 1981 | Lignes antérieures à 2001 |
|---|---|---:|---:|
| `regional_modelisation` | 1960 à 2023 | 3 545, soit 2,4 % | 44 734, soit 30,6 % |
| `survey_modelisation` | 2005 à 2022 | Aucune | Aucune |
| `cropcut_validation` | 2012 à 2019 | Aucune | Aucune |

**Analyse**

Les précipitations satellitaires de référence pour l'Afrique commencent en 1981 et les indices de végétation à 250 m en 2000. Une variable issue de ces sources serait absente pour une part de `regional` qui dépend de sa date de début.

### 2.3 Calendrier cultural

**Constat**

Les mois de semis et de récolte sont renseignés pour toutes les lignes `HarvestStat` de `regional_modelisation`, soit 81,2 % du jeu, et pour aucune ligne des autres sources.

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

- La modélisation de `regional` est restreinte aux années de récolte postérieures ou égales à 1981. Cette restriction écarte 3 545 lignes, soit 2,4 % du jeu, et évite de mélanger des lignes avec et sans précipitations satellitaires.
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

## 7. Décisions attendues du porteur du projet

1. Scénario principal d'estimation en fin de saison, recommandé, ou de prévision en cours de saison.
2. Restriction de `regional` aux années postérieures ou égales à 1981, recommandée.
3. Composition du premier lot, et report de la végétation au second lot.
4. Infrastructure d'extraction, Google Earth Engine ou traitement local.
