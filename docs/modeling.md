# Modélisation des rendements GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 4 Modeling |
| Code | `src/models/` et `tests/test_modeles.py` |
| Notebook de référence | `notebooks/10_modeling.ipynb` |
| Documents associés | `docs/evaluation_protocol.md` et `docs/explanatory_variables.md` |
| Statut | Modèles retenus et figés avant l'évaluation des ensembles de test |

## 1. Objet du document

Ce document présente la technique de modélisation, les variantes comparées et le choix du modèle retenu pour `regional` et pour `survey`. Toutes les comparaisons portent sur le développement. Les ensembles de test sont réservés à la phase d'évaluation.

## 2. Technique

| Élément | Choix | Justification |
|---|---|---|
| Algorithme | Gradient boosting sur arbres de décision, LightGBM 4.7.0 | Interactions entre culture, climat et sol, valeurs manquantes traitées sans imputation, variables catégorielles |
| Cible | Logarithme népérien du rendement | Erreur relative comparable entre cultures, cohérente avec la métrique `mae_log` |
| Perte | Erreur absolue | Correspond à la métrique principale et fait mieux que la perte quadratique en validation croisée |
| Paramètres | 63 feuilles, 50 lignes par feuille au minimum, pas d'apprentissage de 0,05, sous-échantillonnage de 80 % des lignes et des variables | Valeurs usuelles. Les variantes de 31 et 127 feuilles et de 200 lignes par feuille ne changent pas significativement l'erreur |
| Reproductibilité | Graine fixe et calcul déterministe | Résultats identiques d'une exécution à l'autre |

## 3. Variables

| Jeu | Variables |
|---|---|
| `regional` | Culture, saison, pays, source, niveau administratif, système de production, année de récolte, latitude, longitude et logarithme de la surface de la zone, mois de semis et de récolte et durée de saison, douze indicateurs climatiques, neuf variables de sol, altitude et pente |
| `survey` | Culture, pays, année de récolte, position de la grappe ou centroïde de la zone de repli, calendrier, climat, sols et relief |

Aucune colonne classée comme fuite dans `docs/data_dictionary.md` n'est utilisée. La surface GPS des parcelles en fait partie. Le protocole envisageait de l'utiliser comme variable, mais elle est le dénominateur de la cible et ses erreurs de mesure se reporteraient sur le rendement.

## 4. Validation

### 4.1 Validation croisée du protocole

**Constat**

- Dans `regional`, le modèle complet atteint 0,358 en `mae_log` contre 0,417 pour la référence recalculée sur les mêmes lignes, soit une compétence de 14,1 %. Dans `survey`, il atteint 0,718 contre 0,772, soit 7,0 %. Les intervalles de confiance à 95 % des écarts à la référence, obtenus par bootstrap des groupes, vont de 0,052 à 0,065 et de 0,049 à 0,059.
- Retirer l'année ou le pays dégrade nettement les deux jeux. Retirer le climat, les sols et le relief ou la source ne change pas significativement l'erreur de `regional`.

**Analyse**

Les plis tiennent à l'écart des régions, mais pas des années. Le modèle apprend le choc d'une année dans un pays à partir des autres régions du même pays et de la même année, sans passer par le climat. La validation croisée sous-estime donc la valeur du climat pour une année future. Le protocole relevait déjà qu'aucun pli ne mesure la généralisation temporelle.

### 4.2 Extension temporelle interne

**Décision**

Deux schémas internes au développement complètent la validation croisée, sans modifier les ensembles de test.

| Schéma | Entraînement | Évaluation |
|---|---|---|
| Temporel | `regional`, récoltes antérieures à 2012. `survey`, lignes hors de la dernière vague de développement des pays qui en comptent au moins deux | `regional`, récoltes de 2012 à 2016, soit 24 371 lignes de 29 pays. `survey`, ces dernières vagues, soit 19 204 lignes de 7 pays |
| Spatio-temporel | Mêmes lignes, privées du pli évalué | Mêmes lignes, pli par pli |

**Constat**

| Jeu et schéma | Modèle complet | Sans climat | Sans sols ni relief | Référence |
|---|---:|---:|---:|---:|
| `regional`, temporel | 0,372 | 0,375 | 0,379 | 0,432 |
| `regional`, spatio-temporel | 0,426 | 0,429 | 0,420 | 0,484 |
| `survey`, temporel | 0,767 | 0,757 | 0,774 | 0,789 |
| `survey`, spatio-temporel | 0,765 | 0,758 | 0,775 | 0,795 |

**Analyse**

- Dans `regional`, le climat améliore la prédiction des années futures de 0,003, sans que l'écart soit significatif. La source l'améliore autant, significativement en schéma temporel. Les sols et le relief l'améliorent de 0,007 en schéma temporel et la dégradent de 0,006 en schéma spatio-temporel.
- Dans `survey`, le climat dégrade significativement la prédiction des vagues futures. Il ne varie que d'une zone et d'une vague à l'autre, et chaque pays ne compte que deux à sept vagues. Le modèle s'en sert pour reconnaître les vagues plutôt que pour apprendre une réponse au climat.

## 5. Questions tranchées

| Question | Constat | Décision |
|---|---|---|
| Précipitations manquantes avant 2001 | L'entraînement restreint aux récoltes postérieures à 2000 donne 0,365 sur ces récoltes, comme le modèle complet, et 0,448 au lieu de 0,342 sur les récoltes antérieures | Toutes les récoltes postérieures ou égales à 1981 sont conservées |
| Calendrier GGCMI | Compétence de 3,4 % sur les 2 464 lignes concernées, contre 12,9 % pour les lignes au calendrier propre | Lignes conservées |
| Source | Compétence positive pour chaque source, biais logarithmiques compris entre -0,014 et 0,025 hors `USAID_KadunaState` | Source conservée comme variable |
| Alignement de l'Éthiopie | Levé par les dates de coupe de `cropcut`, selon la section 14 de `docs/explanatory_variables.md` | Analyse de sensibilité non nécessaire |

## 6. Part du climat dans la variation annuelle

**Constat**

Une fois retirées la moyenne et la tendance de chaque série, sur les 44 481 récoltes postérieures à 2000 de séries d'au moins dix ans, les variables climatiques et leurs carrés expliquent 1,7 % de la variation annuelle du logarithme du rendement. Cette part atteint 26,0 % en Afrique du Sud, 13,1 % au Niger et 8,1 % au Malawi, mais 1,9 % en Éthiopie.

**Analyse**

La variation annuelle des rendements infranationaux est dominée par des facteurs que le climat de saison ne décrit pas, dont les erreurs des statistiques elles-mêmes. Le gain que le climat peut apporter est borné par les données, et non par le modèle.

## 7. Modèles retenus

| Élément | `regional` | `survey` |
|---|---|---|
| Variante | Modèle complet | Modèle sans variables climatiques |
| Nombre d'arbres | 2 000 | 100 |
| Validation croisée, modèle et référence | 0,358 et 0,417 | 0,719 et 0,772 |
| Validation temporelle interne | 0,372 et 0,432 | 0,757 et 0,789 |
| Validation spatio-temporelle interne | 0,428 et 0,484 | 0,758 et 0,795 |

Le nombre d'arbres minimise la moyenne non pondérée des erreurs des trois schémas. Pour `survey`, une grille de 20 à 400 arbres a été ajoutée lorsque la grille initiale plaçait l'optimum à sa borne inférieure. La sélection est figée dans `src/models/selection.py` et a été versionnée avant toute évaluation des ensembles de test.

## 8. Limites

- Le climat explique au plus 1,7 % de la variation annuelle des rendements de `regional`.
- La validation temporelle interne de `survey` repose sur sept pays et une vague chacun.
- Les intervalles de confiance ignorent la corrélation entre groupes voisins et entre années d'un même pays.
- Les scores de ce document ont servi à la sélection et sont donc légèrement optimistes. Les ensembles de test en donneront une mesure indépendante.

## 9. Reproductibilité

- Les expériences s'exécutent avec les commandes `python -m src.models.experiences regional` et `python -m src.models.experiences survey`. Elles écrivent leurs prédictions dans `data/interim/modeles` et sautent les expériences déjà calculées. Leur durée totale est de deux heures environ sur ce poste.
- Le notebook `10_modeling.ipynb` relit ces prédictions et s'exécute en deux minutes.
