# Plan d'étude préenregistré sur l'apport du climat par culture et par zone agroclimatique

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Origine | Troisième suggestion de la revue du projet par une mentore experte |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/research_rolling_windows_results.md` et `docs/modeling.md`, section 6 |

## 1. Motivation

Les variables climatiques n'améliorent pas la prédiction des années futures en moyenne, selon `docs/research_rolling_windows_results.md`, et le climat n'explique qu'environ 1,7 % de la variation annuelle des rendements de `regional`. Une moyenne nulle peut cacher un apport réel dans certaines cultures ou certaines zones, compensé ailleurs. La revue du projet a suggéré d'explorer les raisons de ce résultat selon les cultures et les zones agroécologiques.

## 2. Question de recherche

L'apport des variables climatiques à la prédiction des années futures, et la part de la variation annuelle des rendements qu'elles expliquent, diffèrent-ils selon la culture et selon la zone agroclimatique ?

## 3. Précautions

- L'étude n'entraîne aucun nouveau modèle. Elle réutilise les prédictions des quatre fenêtres successives de `docs/research_rolling_windows.md`, avec et sans variables climatiques.
- Seul le développement est utilisé, et les ensembles de test ne sont pas consultés.

## 4. Zones agroclimatiques

Chaque zone de `regional` reçoit l'indice d'aridité du Programme des Nations unies pour l'environnement, rapport entre la pluie annuelle moyenne et l'évapotranspiration de référence annuelle moyenne. Les deux sont calculés à partir du magasin climatique du projet, sur les années complètes 2001 à 2016, avec les poids des mailles de chaque zone.

| Classe | Indice d'aridité |
|---|---|
| Hyperaride | Moins de 0,05 |
| Aride | De 0,05 à moins de 0,20 |
| Semi-aride | De 0,20 à moins de 0,50 |
| Subhumide sèche | De 0,50 à moins de 0,65 |
| Humide | 0,65 ou plus |

Les cultures étudiées sont les sept cultures de `regional` qui comptent le plus de lignes évaluées dans les fenêtres.

## 5. Métriques

- L'apport du climat, différence entre l'erreur `mae_log` du modèle privé de climat et celle du modèle retenu, sur les lignes des quatre fenêtres, par classe d'aridité et par culture, avec un intervalle de confiance à 95 % obtenu par bootstrap des groupes du protocole.
- La part de la variation annuelle du rendement expliquée par le climat, calculée comme dans `docs/modeling.md` sur les séries d'au moins dix récoltes postérieures à 2000, par classe d'aridité et par culture.
- Une strate n'est analysée que si elle compte au moins 1 000 lignes évaluées.

## 6. Hypothèses

- **H1.** L'apport du climat est significativement positif dans au moins une classe d'aridité.
- **H2.** L'apport du climat est plus élevé dans les classes aride et semi-aride réunies que dans la classe humide.
- **H3.** La part de la variation annuelle expliquée par le climat est plus élevée dans les classes aride et semi-aride réunies que dans la classe humide.
- **H4.** L'apport du climat est significativement positif pour au moins une des sept cultures étudiées.

Une hypothèse est réfutée lorsque le résultat contredit son énoncé. Les résultats sont rapportés quelle que soit leur issue.

## 7. Limites connues avant l'étude

- L'indice d'aridité ne résume que le climat moyen. Il ne tient compte ni des sols, ni du relief, ni de l'irrigation, contrairement à un zonage agroécologique complet comme celui de la FAO.
- Les classes et les cultures ne sont pas indépendantes, certaines cultures se concentrant dans certaines classes.
- Comparer plusieurs strates multiplie les tests. Un résultat significatif isolé doit être lu avec prudence.
