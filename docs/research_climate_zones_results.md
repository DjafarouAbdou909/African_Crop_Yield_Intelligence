# Résultats de l'étude sur l'apport du climat par culture et par zone agroclimatique

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Plan préenregistré | `docs/research_climate_zones.md`, versionné avant tout calcul |
| Code | `src/recherche/zones_climatiques.py` et `tests/test_recherche_zones_climatiques.py` |
| Notebook de référence | `notebooks/16_climate_zones_study.ipynb` |
| Figure | `reports/figures/climat_aridite.png` |
| Statut | Étude achevée, deux hypothèses confirmées et deux réfutées |

## 1. Résumé

La part de la variation annuelle des rendements expliquée par le climat croît nettement avec l'aridité, de 0,9 % en zone humide à 6,3 % en zone aride, et elle est la plus forte pour l'arachide et le mil. Le signal climatique existe donc là où l'agronomie l'attend. Pourtant, les variables climatiques n'améliorent la prédiction des années futures dans aucune zone ni pour aucune culture. Le modèle ne parvient pas à exploiter ce signal.

## 2. Résultats

**Constat**

| Classe d'aridité | Zones | Part expliquée | Apport à la prédiction | Intervalle à 95 % |
|---|---:|---:|---:|---|
| Aride | 142 | 6,3 % | -0,0014 | -0,0081 à 0,0051 |
| Semi-aride | 338 | 3,0 % | -0,0033 | -0,0068 à 0,0003 |
| Subhumide sèche | 198 | 1,8 % | -0,0080 | -0,0115 à -0,0043 |
| Humide | 543 | 0,9 % | -0,0053 | -0,0087 à -0,0015 |

- La classe hyperaride, avec 179 lignes évaluées, n'atteint pas le seuil de 1 000 lignes et n'est pas analysée.
- Parmi les sept cultures étudiées, la part expliquée va de 2,5 % pour le riz à 6,8 % pour l'arachide. L'apport à la prédiction n'est positif que pour le mil, de 0,0028 sans être significatif, et il est significativement négatif pour le maïs et la patate douce.

**Analyse**

- Le gradient de la part expliquée est celui qu'attend l'agronomie. La variation de la pluie pèse davantage là où elle est rare, et sur les cultures des zones sèches.
- L'écart entre la part expliquée et l'apport à la prédiction signifie que le modèle n'exploite pas un signal pourtant présent. Plusieurs causes, que l'étude ne distingue pas, peuvent l'expliquer. Le signal reste faible, au plus 6 % même en zone aride. Les variables climatiques décrivent aussi le lieu, et le modèle peut s'en servir pour reconnaître les régions. Les seuils appris par les arbres sur les années d'entraînement se transposent mal aux années suivantes.

## 3. Hypothèses

| Hypothèse | Énoncé résumé | Verdict | Élément décisif |
|---|---|---|---|
| H1 | Apport significativement positif dans au moins une classe d'aridité | Réfutée | Aucune classe |
| H2 | Apport plus élevé en zones aride et semi-aride qu'en zone humide | Confirmée de justesse | -0,0028 contre -0,0053, sans test de la différence |
| H3 | Part expliquée plus élevée en zones aride et semi-aride qu'en zone humide | Confirmée | 3,2 % contre 0,9 % |
| H4 | Apport significativement positif pour au moins une culture | Réfutée | Aucune culture |

## 4. Conséquences pour le projet

- La faiblesse de l'apport du climat ne vient pas d'une moyenne qui masquerait un apport réel dans certaines zones. Elle vient de la difficulté du modèle à exploiter un signal faible et concentré dans les zones sèches.
- Une prochaine itération pourrait représenter le climat par ses anomalies à la normale de chaque zone, le réduire à quelques variables pertinentes en zone sèche avec des contraintes de monotonie, ou ne l'utiliser que dans les zones arides et semi-arides. Chaque variante devrait être évaluée sur les fenêtres successives.

## 5. Limites

- L'indice d'aridité ne résume que le climat moyen, sans les sols, le relief ni l'irrigation, contrairement à un zonage agroécologique complet.
- Cultures et classes ne sont pas indépendantes.
- Comparer plusieurs strates multiplie les tests, ce qui invite à la prudence sur tout résultat isolé.
