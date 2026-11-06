# Résultats de l'étude sur la couverture conforme sous changement de distribution

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Plan préenregistré | `docs/research_conformal_shift.md`, versionné avant tout calcul |
| Code | `src/recherche/couverture.py` et `tests/test_recherche_couverture.py` |
| Notebook de référence | `notebooks/13_conformal_shift_study.ipynb` |
| Statut | Étude achevée, une hypothèse confirmée et trois réfutées |

## 1. Résumé

Les intervalles de prédiction conformes des modèles de rendement couvrent en moyenne la part annoncée des rendements, mais échouent gravement pour certains pays lorsque le modèle prédit des années futures. Sur le banc d'essai interne, le Soudan n'est couvert qu'à 34 % pour un niveau nominal de 80 %. Aucune des quatre méthodes alternatives, stratifiée par pays, hiérarchique ou normalisée par une difficulté estimée, ne corrige cet échec sous changement temporel. L'échec provient d'un biais du modèle sur les années récentes, et non d'une dispersion accrue, ce qu'aucun ajustement de largeur ne peut compenser.

## 2. Déroulement

| Étape | Commit |
|---|---|
| Plan préenregistré | `cf9a1c5` |
| Banc d'essai interne et méthodes | `01a9b56` |
| Choix des méthodes figé avant les tests | `48e1b53` |
| Évaluation unique sur les ensembles de test | `33f4afa` |

## 3. Banc d'essai interne

**Constat**

| Jeu | Condition | Couverture marginale à 80 % | Pire pays avec M0 |
|---|---|---|---|
| `regional` | Régions nouvelles | 78,2 à 80,5 % | Mali, 69,5 % |
| `regional` | Années récentes | 78,6 à 79,7 % | Soudan, 34,3 % |
| `regional` | Années récentes de régions nouvelles | 72,8 à 74,4 % | Soudan, 39,4 % |
| `survey` | Régions nouvelles | 79,1 à 79,5 % | Nigeria, 71,2 % |
| `survey` | Vagues récentes | 72,6 à 79,8 % | Mali, 57,8 % |
| `survey` | Vagues récentes de régions nouvelles | 72,7 à 79,8 % | Mali, 57,2 % |

- Dans `survey`, M4 couvre significativement mieux que M0 sur les vagues récentes, de 3,6 et 3,5 points, et M2 et M3 significativement moins bien, de 3,1 à 3,7 points.
- Dans `regional`, aucune méthode ne couvre significativement mieux que M0.

**Décisions**

La règle de la section 8 du plan retient M4 pour `survey`. Pour `regional`, aucune méthode n'atteint 79 % de couverture marginale dans les trois conditions, et la règle de repli retient M0.

## 4. Hypothèses

| Hypothèse | Énoncé résumé | Verdict | Élément décisif |
|---|---|---|---|
| H1 | Le pire pays de M0 est sous le niveau nominal de plus de 5 points | Confirmée | Soudan à 34,3 %, Mali à 57,8 % |
| H2 | M2 ou M3 ramène le pire pays à moins de 5 points du niveau nominal | Réfutée | Vrai seulement pour les régions nouvelles de `survey`. Sur les années récentes, le pire pays reste sous 63 % |
| H3 | M4 couvre au niveau requis avec des intervalles plus étroits | Réfutée | 78,3 % pour les régions nouvelles de `regional`, intervalles plus larges sur les vagues récentes de `survey` |
| H4 | Toutes les méthodes perdent au moins 2 points sur les années récentes | Réfutée | 1,2 point au plus pour les années récentes de régions connues de `regional`, aucune perte pour M4 dans `survey` |

L'énoncé de H2 ne précisait pas les conditions concernées. Il a été appliqué aux trois conditions, ce qui en est la lecture la plus exigeante.

## 5. Évaluation finale

**Constat**

- Les couvertures de M0 coïncident avec celles de `docs/evaluation.md`, ce qui contrôle la mise en œuvre.
- Dans `regional`, M0 couvre 84,5 à 85,2 % des rendements de test, mais le Zimbabwe n'est couvert qu'à 63,3 % sur les années futures.
- Dans `survey`, M4 relève le pire pays sur chaque ensemble, de 69,1 à 72,2 %, de 76,8 à 79,4 % et de 67,5 à 72,0 %. Sa couverture marginale baisse sur les vagues futures, de 77,2 à 75,8 % et de 76,9 à 75,3 %, alors que le banc d'essai annonçait 79,8 %.

**Analyse**

Le banc d'essai a correctement prédit le gain de M4 sur le pire pays, mais pas sa couverture marginale. Les vagues futures du test s'écartent davantage du passé que les vagues récentes du développement. Une validation qui imite un changement de distribution peut en sous-estimer l'ampleur.

## 6. Nature de l'échec

**Constat**

Au Soudan, l'erreur médiane passe de 0,315 sur 1981 à 2011 à 0,766 sur 2012 à 2016, et le biais logarithmique médian de 0,033 à -0,753. Le biais s'accroît de -0,21 en 2012 à -0,98 en 2016.

**Analyse**

- Le modèle sous-estime d'environ moitié les rendements récents. Un intervalle centré sur une prédiction biaisée ne peut pas couvrir, et les méthodes conformes, qui n'ajustent que la largeur, sont impuissantes face à une rupture de niveau.
- La rupture commence l'année qui suit la sécession du Soudan du Sud. Ce rapprochement reste une hypothèse non établie.

## 7. Enseignements pour la fiabilité des systèmes d'apprentissage

- Une incertitude calibrée en moyenne peut être gravement trop confiante pour un sous-groupe identifiable, sans que la métrique globale le révèle. Toute garantie de couverture devrait être rapportée par groupe.
- Sous changement temporel, l'échec par groupe relève surtout du biais du modèle. La réponse adaptée est la détection du changement, et non l'élargissement des intervalles.
- Un banc d'essai construit pour imiter un changement de distribution aide à choisir une méthode, mais peut sous-estimer le changement réel.

## 8. Limites

- Le problème a été repéré sur les ensembles de test avant l'étude.
- Le banc d'essai de `survey` ne compte que six pays d'au moins 200 lignes récentes, et le test spatio-temporel de `regional` quatre pays.
- Le bootstrap des groupes ignore la corrélation entre groupes voisins et entre années d'un même pays.
- Les erreurs de calibration proviennent de modèles de validation, entraînés sur moins de données que le modèle final.

## 9. Suite proposée

Les rendements arrivent une fois par an. L'inférence conforme adaptative, proposée par Gibbs et Candès en 2021, réajuste le niveau des intervalles à mesure que les erreurs récentes sont observées. Une seconde étude préenregistrée pourrait tester si elle rétablit la couverture d'un pays en rupture, comme le Soudan, en une ou deux saisons, et comparer cette correction à une simple détection du biais récent.
