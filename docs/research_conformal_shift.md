# Plan d'étude préenregistré sur la couverture conforme sous changement de distribution

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/evaluation.md`, sections 7 et 9, et `notebooks/12_uncertainty_interpretation.ipynb` |

## 1. Motivation

Les intervalles de prédiction conformes du projet garantissent une couverture marginale, c'est-à-dire en moyenne sur toutes les lignes, lorsque les lignes de calibration et les lignes à prédire sont échangeables. Cette hypothèse est violée par construction lorsque le modèle prédit des régions nouvelles ou des années futures. Sur les ensembles de test, l'intervalle à 80 % de `survey` couvre 76,9 à 77,2 % des vagues futures et 69,5 % des parcelles du Nigeria. Une garantie globale peut donc échouer sur un sous-groupe identifiable, ce qui pose un problème de fiabilité pour tout usage qui s'appuie sur ces intervalles.

La question intéresse la sûreté des systèmes d'apprentissage au-delà de l'agriculture. Un système qui annonce une incertitude calibrée en moyenne peut être systématiquement trop confiant pour une population donnée, sans que la métrique globale le révèle.

## 2. Question de recherche

Quelles méthodes de prédiction conforme maintiennent la couverture nominale à la fois en moyenne et dans chaque pays, sous changement spatial et temporel, et à quel coût en largeur d'intervalle ?

## 3. Précaution contre le surajustement aux ensembles de test

Le problème a été observé sur les ensembles de test. Développer une méthode en les consultant reviendrait à l'ajuster à ces ensembles. L'étude suit donc trois règles.

1. Les méthodes sont comparées et choisies sur un banc d'essai interne au développement, décrit à la section 4.
2. Le choix est figé et versionné avant toute nouvelle évaluation sur les ensembles de test.
3. Toutes les méthodes de la section 5 sont rapportées sur les ensembles de test, et pas seulement la méthode choisie.

## 4. Banc d'essai interne

Les erreurs hors échantillon du modèle retenu, au nombre d'arbres retenu, proviennent des trois validations internes de `docs/modeling.md`.

| Élément | `regional` | `survey` |
|---|---|---|
| Lignes anciennes | Récoltes antérieures à 2012 | Lignes hors de la dernière vague de développement des pays qui en comptent au moins deux |
| Lignes récentes | Récoltes de 2012 à 2016 | Ces dernières vagues |
| Calibration | Erreurs de validation croisée des lignes anciennes | Idem |
| Condition temporelle | Erreurs de validation temporelle des lignes récentes | Idem |
| Condition spatio-temporelle | Erreurs de validation spatio-temporelle des lignes récentes | Idem |
| Condition spatiale | Erreurs de validation croisée des lignes anciennes des plis 3 et 4, la calibration se limitant alors aux plis 0, 1 et 2 | Idem |

Un modèle auxiliaire éventuel, comme celui de la méthode M4, n'est entraîné que sur les lignes de calibration.

## 5. Méthodes comparées

| Code | Méthode | Principe |
|---|---|---|
| M0 | Conformité par culture | Méthode actuelle. Quantile des erreurs absolues sur le logarithme par culture, et de l'ensemble pour une culture de moins de 200 erreurs |
| M1 | Conformité globale | Un seul quantile pour toutes les lignes |
| M2 | Conformité par pays | Quantile par pays, et de l'ensemble pour un pays de moins de 200 erreurs |
| M3 | Conformité hiérarchique par pays et culture | Quantile du couple pays et culture s'il compte au moins 200 erreurs, sinon du pays, sinon de l'ensemble |
| M4 | Conformité normalisée | L'erreur absolue est divisée par une difficulté estimée par un modèle LightGBM de l'erreur absolue, entraîné sur la moitié des groupes de calibration. Le quantile des erreurs normalisées est calculé sur l'autre moitié |

Le quantile retenu est le quantile conforme, de rang égal au plafond du produit de n plus un par le niveau, pour n erreurs.

## 6. Métriques

Les métriques sont calculées aux niveaux nominaux de 80 et 90 %, pour chaque jeu et chaque condition.

| Métrique | Définition |
|---|---|
| Couverture marginale | Part des lignes évaluées comprises dans leur intervalle |
| Couverture du pire pays | Couverture minimale parmi les pays d'au moins 200 lignes évaluées |
| Écart moyen de couverture | Moyenne non pondérée, sur ces pays, de l'écart absolu entre couverture et niveau nominal |
| Largeur médiane | Médiane du rapport entre borne haute et borne basse |

Les écarts entre méthodes sont accompagnés d'intervalles de confiance à 95 % obtenus par bootstrap des groupes du protocole.

## 7. Hypothèses

- **H1.** Avec M0, la couverture du pire pays est inférieure de plus de 5 points au niveau nominal dans au moins une condition de chaque jeu.
- **H2.** M2 ou M3 ramène la couverture du pire pays à moins de 5 points du niveau nominal, pour une largeur médiane supérieure d'au plus 25 % à celle de M0.
- **H3.** M4 atteint une couverture marginale d'au moins le niveau nominal diminué d'un point, avec une largeur médiane inférieure à celle de M0.
- **H4.** Toutes les méthodes calibrées sur les lignes anciennes perdent au moins 2 points de couverture marginale dans les conditions temporelles par rapport à la condition spatiale.

Une hypothèse est réfutée lorsque le résultat contredit l'énoncé dans l'un des jeux concernés. Les résultats sont rapportés quelle que soit leur issue.

## 8. Règle de décision

Pour chaque jeu, la méthode retenue est, parmi celles dont la couverture marginale atteint au moins le niveau nominal diminué d'un point dans les trois conditions, celle dont l'écart moyen de couverture est le plus faible à 80 %. Entre deux méthodes dont les écarts moyens diffèrent de moins d'un point, la plus étroite est retenue. Si aucune méthode ne remplit la condition de couverture marginale, la méthode de couverture marginale la plus élevée est retenue et l'échec est rapporté.

## 9. Évaluation finale

La méthode retenue et les autres méthodes sont calibrées sur toutes les erreurs hors échantillon du développement, comme les intervalles actuels, puis évaluées une seule fois sur les trois ensembles de test et sur les grappes de `cropcut` tenues à l'écart.

## 10. Limites connues avant l'étude

- Le problème a été repéré sur les ensembles de test, et l'étude ne peut prétendre l'avoir découvert de manière indépendante.
- Les erreurs de calibration proviennent de modèles de validation, entraînés sur moins de données que le modèle final.
- Le banc d'essai de `survey` ne compte que six pays d'au moins 200 lignes récentes, ce qui limite la puissance de H1 et de H2 pour ce jeu.
- Aucune méthode conforme ne peut garantir la couverture d'un pays absent de la calibration.
