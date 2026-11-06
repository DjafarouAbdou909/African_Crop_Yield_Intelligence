# Déploiement et fiche des modèles

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 6 Deployment |
| Code | `src/models/prediction.py` et `app/` |
| Documents associés | `docs/modeling.md` et `docs/evaluation.md` |
| Statut | Modèles livrés avec leurs prédictions et leurs intervalles |

## 1. Objet du document

Ce document décrit les livrables du projet, l'usage prévu des modèles, leurs performances mesurées, leurs limites et la procédure de mise à jour. Il tient lieu de fiche des modèles.

## 2. Livrables

| Livrable | Emplacement | Contenu |
|---|---|---|
| Modèles | `data/interim/modeles/regional_modele.txt` et `survey_modele.txt` | Modèles LightGBM entraînés sur tout le développement |
| Descriptions | `data/interim/modeles/regional_modele.json` et `survey_modele.json` | Variables, modalités, paramètres et nombre d'arbres |
| Intervalles | `data/interim/modeles/regional_intervalles.csv` et `survey_intervalles.csv` | Demi-largeurs sur le logarithme, par culture, à 80 et 90 % |
| Prédictions | `data/processed/predictions_regional.csv.gz`, `predictions_survey.csv.gz` et `predictions_cropcut.csv.gz` | Rendement observé, rendement prédit et bornes des intervalles, avec la partition de chaque ligne |
| Fonction de prédiction | `predire_avec_intervalles` dans `src/models/prediction.py` | Prédiction et intervalles pour toute table portant les variables du modèle |

Les fichiers de `data` sont exclus du dépôt git et se reproduisent par les commandes de la section 7. Les lignes du développement sont prédites par un modèle qui les a vues à l'entraînement, et leur erreur n'est pas une mesure de performance.

## 3. Usage prévu

| Modèle | Prédit | Usage prévu |
|---|---|---|
| `regional` | Rendement d'une culture et d'une saison dans une région de niveau 1 ou 2, en fin de saison | Estimer un rendement régional manquant ou récent, comparer des régions, explorer l'effet du climat de la saison |
| `survey` | Rendement déclaré d'une parcelle d'enquête, en fin de saison | Situer une parcelle par rapport aux parcelles comparables, étudier les facteurs de lieu |

Conformément à `01_business_understanding.ipynb`, ces modèles servent l'analyse et la recherche. Ils ne constituent pas un outil de décision opérationnelle. Le modèle de `survey` prédit un rendement déclaré, supérieur d'environ 40 % aux mesures par coupe, et ne remplace pas une mesure directe.

## 4. Entrées

| Modèle | Variables |
|---|---|
| `regional` | Culture, saison, pays, source, niveau administratif, système de production, année de récolte, latitude, longitude et surface de la zone, calendrier, douze indicateurs climatiques de la saison, neuf variables de sol, altitude et pente |
| `survey` | Culture, pays, année de récolte, position de la grappe, calendrier, neuf variables de sol, altitude et pente |

Les variables sont construites par `src/features` à partir des contours GADM, de NASA POWER, d'IMERG, de SoilGrids et de Copernicus DEM, selon `docs/explanatory_variables.md`. Le modèle accepte des variables manquantes, mais une modalité de culture ou de pays absente de l'entraînement est traitée comme manquante.

## 5. Performances mesurées

| Ensemble de test | `regional` | Compétence | Couverture à 80 % | `survey` | Compétence | Couverture à 80 % |
|---|---:|---:|---:|---:|---:|---:|
| Années futures, lieux connus | 0,310 | 22,3 % | 85,2 % | 0,765 | 7,6 % | 77,2 % |
| Lieux nouveaux, années passées | 0,321 | 17,4 % | 84,8 % | 0,716 | 5,3 % | 81,5 % |
| Lieux nouveaux, années futures | 0,334 | 17,2 % | 84,5 % | 0,767 | 6,8 % | 76,9 % |

Les erreurs sont exprimées en `mae_log`. Une erreur de 0,31 correspond à une erreur relative typique de 36 %. La compétence est la part de l'erreur de la référence hiérarchique supprimée par le modèle.

## 6. Limites d'usage

- Les séries climatiques s'arrêtent en 2023. Une saison postérieure exige leur extension, décrite à la section 7.
- Le modèle ne prolonge pas la tendance des rendements au-delà de 2016, dernière année du développement de `regional`. Il peut sous-estimer les années récentes.
- Le climat n'explique qu'une faible part de la variation annuelle des rendements infranationaux. Le modèle anticipe mal une année exceptionnelle.
- Les rendements de `regional` contiennent quinze erreurs d'unité de tabac et d'autres valeurs suspectes, selon `docs/evaluation.md`.
- Les intervalles de `survey` couvrent moins que leur niveau nominal dans quelques pays, dont le Nigeria.
- Le modèle de `regional` n'a appris que sur les 45 pays de GROW-Africa et celui de `survey` sur ses 12 pays. Un pays absent de l'entraînement est prédit sans son effet propre.

## 7. Application de démonstration

**Contenu**

L'application Streamlit de `app/app.py` présente le modèle de `regional` en quatre pages.

| Page | Contenu |
|---|---|
| Prédiction | Rendement prédit d'une région, d'une culture, d'une saison et d'une année, intervalles à 80 et 90 %, rendement observé, contributions de Shapley et conditions de la saison |
| Série d'une région | Rendements observés et prédits année par année, avec l'intervalle à 80 % et la distinction entre années d'entraînement et années de test |
| Performance | Scores de test des deux modèles, couverture des intervalles et limites |
| À propos | Données, méthode et usage prévu |

**Ressources**

L'application ne relit que `app/ressources`, soit 17,6 Mo produits par `python -m app.preparer`. Ces ressources réunissent le modèle de `regional`, sa description, les demi-largeurs de ses intervalles, la table des variables des 142 247 lignes retenues et les scores de test. Les prédictions de l'application coïncident avec `predictions_regional.csv.gz` à 10 puissance -15 près.

**Lancement local**

La commande `streamlit run app/app.py --server.address localhost` ouvre l'application à l'adresse `http://localhost:8501`, sans l'exposer au réseau local. La collecte de statistiques d'usage de Streamlit est désactivée par `.streamlit/config.toml`.

**Hébergement**

Streamlit Community Cloud peut héberger l'application depuis le dépôt GitHub, avec `app/app.py` comme fichier principal et Python 3.12. Il lit les dépendances minimales de `app/requirements.txt`, sans la chaîne géospatiale. Les ressources doivent alors être versionnées.

## 8. Reproduction et mise à jour

Les commandes suivantes s'exécutent depuis la racine du projet, dans l'ordre.

| Étape | Commande | Durée indicative |
|---|---|---|
| Préparation | `python -m src.data.prepare` | 11 minutes au premier chargement des fichiers bruts, une minute ensuite |
| Climat | `python -m src.features.climat` puis `python -m src.features.climat imerg` | Plusieurs heures, avec reprise après interruption |
| Magasin climatique | Fonctions `construire_magasin` de `src/features/climat.py` et `calculer_et0` de `src/features/agregation.py` | Non mesurée précisément |
| Variables climatiques | `python -m src.features.variables` | Non mesurée précisément |
| Sols | `python -m src.features.sols extraire` puis `construire` | Une heure environ |
| Relief | `python -m src.features.relief extraire` puis `construire` | Quarante minutes environ |
| Variables de `cropcut` | `python -m src.features.variables_cropcut` | Une minute |
| Expériences | `python -m src.models.experiences regional` puis `survey` | Deux heures environ |
| Évaluation | `python -m src.models.evaluation_finale` | Deux minutes |
| Prédictions | `python -m src.models.prediction regional`, `survey` et `cropcut` | Quelques minutes |
| Application | `python -m app.preparer` puis `streamlit run app/app.py --server.address localhost` | Une minute |

Pour une saison nouvelle, la fin des séries `FIN_POWER` de `src/features/climat.py` est repoussée, les séries sont téléchargées à nouveau, puis les étapes suivantes sont relancées. Un réentraînement intégrant les années récentes doit suivre le protocole d'évaluation, en redéfinissant la période future.
