# Évaluation des modèles de rendement GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 5 Evaluation |
| Code | `src/models/evaluation_finale.py`, `incertitude.py` et `interpretation.py` |
| Notebooks de référence | `notebooks/11_evaluation.ipynb` et `notebooks/12_uncertainty_interpretation.ipynb` |
| Documents associés | `docs/modeling.md` et `docs/evaluation_protocol.md` |
| Statut | Modèles évalués une seule fois sur les ensembles de test et retenus |

## 1. Objet du document

Ce document rapporte l'évaluation des modèles retenus dans `docs/modeling.md` sur les ensembles de test du protocole et sur la validation externe `cropcut`. La sélection a été figée et versionnée avant cette évaluation, qui n'a modifié aucun choix de modélisation.

## 2. Scores

**Constat**

| Ensemble | `regional`, modèle et référence | Compétence | `survey`, modèle et référence | Compétence |
|---|---|---:|---|---:|
| Test temporel | 0,310 et 0,398 | 22,3 % | 0,765 et 0,828 | 7,6 % |
| Test spatial | 0,321 et 0,389 | 17,4 % | 0,716 et 0,756 | 5,3 % |
| Test spatio-temporel | 0,334 et 0,404 | 17,2 % | 0,767 et 0,822 | 6,8 % |
| `cropcut`, grappes tenues à l'écart | | | 0,669 et 0,676 | 1,1 % |

- L'erreur relative typique du modèle de `regional` vaut 36 à 40 %, et celle du modèle de `survey` 105 à 115 %.
- Le biais logarithmique de la référence sur les années futures de `regional`, de -0,086 et -0,112, tombe à -0,013 et -0,028. Celui de la dernière vague de `survey` passe de -0,236 à 0,050.
- Les scores de `survey` sans les surfaces GPS recopiées sont pratiquement identiques, avec une compétence de 8,3 %, 5,2 % et 7,5 %.

**Analyse**

- Les deux modèles battent la référence en validation croisée et sur chaque ensemble de test, et satisfont la règle de retenue du protocole.
- Les scores de test de `survey` s'écartent de moins de 0,01 de la validation interne. Ceux de `regional` sont meilleurs que la validation interne, car le modèle final apprend sur toutes les années du développement et les années futures proviennent à 82 % de `HarvestStat`. La référence progresse dans la même proportion.

## 3. Ventilations

**Constat**

- Dans `regional`, le modèle bat la référence pour chaque source et chaque niveau administratif, avec une compétence de 13,3 à 28,5 %. Il la bat dans 90 à 100 % des pays d'au moins 200 lignes selon l'ensemble. Il fait moins bien à Madagascar et en Afrique du Sud sur le test spatial, et au Mozambique sur le test temporel, de 8,7 % avec un biais de -0,212.
- Dans `survey`, il fait moins bien en Guinée-Bissau et au Nigeria sur le test spatial, au Mali et au Nigeria sur le test temporel et au Togo sur le test spatio-temporel.

**Analyse**

Le gain est général. Les exceptions concernent des pays peu représentés dans le développement ou des évolutions récentes que ni la tendance ni le climat n'anticipent.

## 4. Validation externe

**Constat**

Sur les 2 297 mesures de `cropcut` des grappes tenues à l'écart, le modèle de `survey` atteint 0,669 contre 0,676 pour la référence, avec un biais logarithmique de 0,333. Sur les grappes déjà vues, il atteint 0,655 contre 0,698.

**Analyse**

Le modèle apprend le rendement déclaré par les enquêtes, qui dépasse la mesure par coupe d'environ 40 % pour ses prédictions. Il ne remplace pas une mesure directe, et son biais ne sera pas corrigé sans validation spécifique.

## 5. Rendements aberrants

**Constat**

- Quinze lignes de tabac du Malawi, issues de `RCeA` pour la récolte de 2016, ont des rendements de 610 à 1 471 t/ha, soit 600 à 1 400 fois la médiane du tabac. Six appartiennent au test spatial.
- La borne haute de plausibilité du tabac, calculée selon le filtre des auteurs à deux fois le 98e percentile, vaut 1 532 t/ha. Ce filtre ne protège qu'une culture dont moins de 2 % des valeurs sont corrompues.
- Sans ces six lignes, le coefficient de détermination en tonnes par hectare du test spatial passe de 0,063 à 0,814, et l'erreur `mae_log` de 0,321 à 0,319.
- D'autres rendements dépassent les valeurs connues des cultures, sans pouvoir être tranchés sans référentiel agronomique. Il s'agit du niébé et du sésame de `FAO_subnational` au Burkina Faso, de 5 à 16 t/ha, et du tabac de `HarvestStat` au Niger, de 12 à 29 t/ha.

**Analyse**

Les quinze rendements de tabac sont des productions exprimées en kilogrammes au lieu de tonnes. Le modèle leur prédit un rendement plausible d'environ 1 t/ha, et seule l'évaluation en est affectée. L'anomalie ayant été découverte sur les ensembles de test, sa correction est laissée à la décision du porteur du projet.

**Recommandation**

Signaler dans la préparation les rendements supérieurs à 100 fois la médiane de leur culture comme erreurs d'unité probables, et les exclure de la modélisation, puis relancer la modélisation et l'évaluation.

## 6. Importance des variables

Dans le modèle final de `regional`, les variables climatiques portent 20,5 % du gain des divisions, les sols 15,0 % et le relief 3,4 %. Dans celui de `survey`, les sols en portent 16,5 % et le relief 6,5 %. Le gain mesure l'usage d'une variable par les arbres et non sa contribution à la qualité des prédictions, que mesurent les ablations de `docs/modeling.md`.

## 7. Incertitude des prédictions

**Constat**

- Les intervalles de prédiction suivent la prédiction conforme par culture, calibrée sur les erreurs hors échantillon des trois validations internes du développement.
- Dans `regional`, les intervalles à 80 % et à 90 % couvrent 84,5 à 85,2 % et 92,8 à 92,9 % des rendements de test. Le rapport médian entre leurs bornes haute et basse vaut 3,0 et 4,9.
- Dans `survey`, ils couvrent 76,9 à 81,5 % et 88,1 à 90,8 %, avec un rapport médian de 9,8 et 18,4. La couverture tombe à 69,5 % et 81,4 % au Nigeria. Sur les grappes de `cropcut` tenues à l'écart, elle vaut 80,9 % et 90,9 %.

**Analyse**

Les intervalles de `regional` sont légèrement prudents. Ceux de `survey` couvrent un peu moins que prévu sur les vagues futures et dans quelques pays, et leur largeur traduit la variation des rendements de parcelle que les variables disponibles n'expliquent pas.

## 8. Facteurs des prédictions

**Constat**

- Selon les contributions de Shapley, la culture porte 55,4 % de la contribution absolue moyenne dans `regional`, le pays 13,5 %, le climat 9,6 %, les sols 7,6 % et l'année 5,4 %. Dans `survey`, la culture en porte 38,3 %, l'année 18,7 %, le pays 18,5 % et les sols 10,7 %.
- Pour le maïs de `regional`, la contribution de la pluie de saison croît de -0,043 sous 450 mm à environ 0,025 au-delà de 950 mm. Celle de la température maximale moyenne décroît de 0,031 vers 26 °C à -0,032 au-delà de 33,5 °C.
- La contribution de l'année croît de -0,082 vers 1990 à 0,105 en 2017, puis reste stable.

**Analyse**

- Les effets de la pluie et de la chaleur ont le sens attendu, mais restent modestes devant la variation des rendements.
- Les arbres de décision n'extrapolent pas au-delà des années d'entraînement. Le modèle reproduit le niveau de 2016 pour les années suivantes, sans prolonger la tendance.
- Les contributions décrivent le fonctionnement du modèle et non des effets causaux.

## 9. Limites

- Le climat n'explique qu'une faible part de la variation annuelle des rendements, ce qui limite l'anticipation d'une année exceptionnelle.
- Les rendements de `survey` sont des déclarations, plus élevées que les mesures par coupe.
- Les erreurs d'unité et les rendements suspects de `regional` affectent l'entraînement et l'évaluation.
- Les ensembles de test temporels de `regional` ne couvrent que 22 pays, et celui de `survey` neuf pays.
- Le modèle ne prolonge pas la tendance des rendements au-delà de 2016.
- La couverture des intervalles de `survey` reste inférieure au niveau nominal dans quelques pays.

## 10. Reproductibilité

- La commande `python -m src.models.evaluation_finale` entraîne les modèles retenus, les écrit dans `data/interim/modeles` avec leurs modalités, et écrit les prédictions des ensembles de test, en deux minutes environ.
- Le notebook `11_evaluation.ipynb` relit ces prédictions et s'exécute en moins d'une minute.
- Le notebook `12_uncertainty_interpretation.ipynb` calibre les intervalles, mesure leur couverture et calcule les contributions de Shapley sur des échantillons à graine fixe, en cinq minutes environ.
