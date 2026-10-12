# Dictionnaire des données — GROW-Africa

**Projet :** African Crop Yield Intelligence  
**Étape :** Audit des données — Dictionnaire des données

## 1. Présentation

Ce document décrit les colonnes des quatre fichiers de la base GROW-Africa. Pour chaque colonne, il présente sa signification, son type, son rôle potentiel dans le projet et les éventuels points à vérifier.

Les définitions s'appuient sur l'article scientifique associé à la base et sur sa documentation. Lorsque la signification d'une colonne n'est pas confirmée, cela est précisé. Les statistiques descriptives seront ajoutées après l'analyse des fichiers avec pandas.

### Statut des définitions

| Statut | Signification |
|---|---|
| Documenté | Information confirmée par une source. |
| Déduit | Interprétation basée sur le nom de la colonne ou le contexte. |
| À vérifier | Information qui nécessite une analyse complémentaire. |

### Rôle des colonnes

| Rôle | Signification |
|---|---|
| Cible | Variable que le modèle devra prédire. |
| Clé de regroupement | Identifiant utilisé pour organiser les données et éviter certaines fuites entre les ensembles d'entraînement et de test. |
| Candidate | Variable pouvant servir de variable explicative. |
| Exclue | Variable qui ne sera pas utilisée comme entrée du modèle, notamment en cas de fuite de données ou de métadonnée. |
| À investiguer | Rôle à déterminer après analyse. |

Les rôles proposés reposent sur l'hypothèse que la cible est le rendement agricole en tonnes par hectare (t/ha). Ils seront confirmés au cours de l'audit.

## 2. Présentation générale de la base

| Information | Description |
|---|---|
| Nombre d'observations | 535 844 selon l'article scientifique |
| Nombre de cultures | 25 |
| Fichiers | `GROW-Africa_Regional`, `GROW-Africa_LSMS_survey`, `GROW-Africa_LSMS_cropcut` et `GROW-Africa_Point` |
| Unité du rendement | Tonnes par hectare (t/ha) |
| Références géographiques | Identifiants administratifs GADM, niveaux 0 à 3 |
| Principales opérations de nettoyage | Harmonisation des noms de cultures et des références géographiques, suppression des doublons |
| Traitement des rendements aberrants | Filtrage appliqué aux données ponctuelles selon les critères décrits dans l'article |
| Version utilisée | À confirmer |
| Licence des données | À vérifier sur Zenodo |

Les effectifs de chaque fichier devront être comparés aux chiffres de l'article afin de vérifier la version téléchargée et la cohérence des données.

## 3. GROW-Africa_LSMS_cropcut

Ce fichier contient des mesures de récolte (*crop cuts*) associées aux enquêtes LSMS. Selon l'article, les observations concernent l'Éthiopie.

| Colonne | Définition | Type | Rôle | Remarque |
|---|---|---|---|---|
| `Country` | Pays de l'observation | Texte | Regroupement | Pays à confirmer dans les données |
| `Source` | Source de l'enquête | Texte | Métadonnée | Peut renseigner sur la méthode de collecte |
| `Year` | Année de l'observation | Entier | Candidate | Vérifier la définition exacte |
| `GPS_lat` | Latitude | Décimal | À investiguer | Coordonnée géographique |
| `GPS_lon` | Longitude | Décimal | À investiguer | Coordonnée géographique |
| `L0_GID` | Identifiant administratif de niveau 0 | Texte | Regroupement | Niveau national |
| `L1_GID` | Identifiant administratif de niveau 1 | Texte | Regroupement | Division administrative |
| `L2_GID` | Identifiant administratif de niveau 2 | Texte | Regroupement | Division administrative |
| `L3_GID` | Identifiant administratif de niveau 3 | Texte | Regroupement | Peut contenir des valeurs manquantes |
| `holder_id` | Identifiant de l'exploitant | Texte | Regroupement | Définition à confirmer |
| `household_id` | Identifiant du ménage | Texte | Regroupement | Vérifier les répétitions entre années |
| `parcel_id` | Identifiant de la parcelle | Texte | Regroupement | |
| `field_id` | Identifiant du champ | Texte | Regroupement | |
| `Crop` | Nom harmonisé de la culture | Texte | Candidate | |
| `crop_origname` | Nom original de la culture | Texte | Métadonnée | |
| `cropCutDay` | Jour de la mesure de récolte | Entier | Excl