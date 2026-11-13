# Résultats de l'étude sur la stabilité temporelle par fenêtres successives

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Plan préenregistré | `docs/research_rolling_windows.md`, versionné avant tout calcul |
| Code | `src/recherche/fenetres_temporelles.py` et `tests/test_recherche_fenetres_temporelles.py` |
| Notebook de référence | `notebooks/15_rolling_windows_study.ipynb` |
| Figure | `reports/figures/fenetres_temporelles.png` |
| Statut | Étude achevée, trois hypothèses confirmées et une réfutée |

## 1. Résumé

Sur quatre fenêtres successives de 2004 à 2016, chacune prédite par un modèle qui n'a appris que sur les années antérieures, le modèle de `regional` bat la référence de façon significative et stable, avec une compétence de 7,8 à 14,6 %. En revanche, les variables climatiques n'améliorent la prédiction dans aucune fenêtre, et la dégradent significativement dans trois. L'apport léger du climat mesuré avec une seule coupure en 2012 ne résiste pas à cette évaluation, et son signe s'inverse lorsqu'une seule année est ajoutée à l'entraînement.

## 2. Résultats

**Constat**

| Fenêtre | Lignes | Compétence | Gain significatif | Apport du climat | Intervalle à 95 % |
|---|---:|---:|---|---:|---|
| 2004 à 2006 | 12 309 | 7,8 % | Oui | -0,0050 | -0,0090 à -0,0009 |
| 2007 à 2009 | 13 957 | 9,1 % | Oui | -0,0071 | -0,0111 à -0,0027 |
| 2010 à 2012 | 13 478 | 14,6 % | Oui | -0,0008 | -0,0046 à 0,0035 |
| 2013 à 2016 | 19 103 | 13,0 % | Oui | -0,0063 | -0,0097 à -0,0025 |

- Le biais logarithmique du modèle reste compris entre -0,053 et 0,038, contre -0,036 à -0,161 pour la référence.
- Sur les années 2013 à 2016, l'apport du climat vaut +0,0034 avec un entraînement de 1981 à 2011, et -0,0063 avec un entraînement de 1981 à 2012.

**Analyse**

- Le gain du modèle est durable, et il croît avec la quantité de données d'entraînement, faisant plus que doubler entre la première et la troisième fenêtre.
- L'apport des variables climatiques n'est pas établi. Il est faible, de signe instable, et dépend de la coupure choisie. Ce résultat rejoint la mesure directe de `docs/modeling.md`, selon laquelle le climat n'explique qu'environ 1,7 % de la variation annuelle des rendements.

## 3. Hypothèses

| Hypothèse | Énoncé résumé | Verdict | Élément décisif |
|---|---|---|---|
| H1 | Gain significatif sur la référence dans chaque fenêtre | Confirmée | Quatre fenêtres sur quatre |
| H2 | Écart de compétence entre fenêtres d'au plus 10 points | Confirmée | 6,7 points |
| H3 | Le climat améliore le modèle dans au moins trois fenêtres | Réfutée | Aucune fenêtre, trois défavorables |
| H4 | Biais du modèle plus faible que celui de la référence dans chaque fenêtre | Confirmée | Quatre fenêtres sur quatre |

## 4. Conséquences pour le projet

- L'avantage du modèle sur la référence pour les années futures de régions connues est stable, ce qui conforte cet usage.
- Le modèle retenu pour `regional` conserve le climat. Ce choix reposait sur un apport faible et non significatif mesuré avec une seule coupure, que cette étude ne confirme pas. Les ensembles de test ayant déjà été utilisés, le modèle n'est pas modifié ici. Une prochaine itération de modélisation devrait comparer les deux variantes sur ces fenêtres avant de trancher.

## 5. Limites

- Les fenêtres mêlent l'effet du temps à celui de la quantité d'entraînement, de la disponibilité de la pluie et de la composition des sources.
- Les premières fenêtres disposent de peu d'années d'entraînement avec pluie.
- L'étude ne porte que sur `regional`, `survey` comptant trop peu de vagues par pays.
