# Plan d'étude préenregistré sur les horizons de prévision

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Origine | Suite de la cinquième suggestion de la revue du projet par une mentore experte |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/estimation_et_prevision.md`, `docs/research_rolling_windows.md` et `docs/research_climate_zones_results.md` |

## 1. Motivation

La revue du projet a invité à distinguer l'estimation en fin de saison de la prévision anticipée. `docs/estimation_et_prevision.md` établit que les modèles du projet sont des modèles d'estimation et que leurs scores ne mesurent pas une capacité d'anticipation. Sa section 6 propose d'évaluer un scénario de prévision par une étude préenregistrée. Cette étude mesure ce que coûte l'anticipation, c'est-à-dire la perte de précision lorsque le rendement est prédit avant la fin de la saison avec la seule information disponible à la date de prévision.

## 2. Question de recherche

Pour le modèle retenu de `regional`, de combien l'erreur augmente-t-elle lorsque la prédiction est émise au semis, à mi-saison ou un mois avant la récolte plutôt qu'en fin de saison, et l'information climatique de la saison en cours apporte-t-elle un gain là où le climat explique le plus les rendements ?

## 3. Précautions

- L'étude n'utilise que le développement, dont les récoltes vont de 1981 à 2016. Les ensembles de test ne sont pas consultés.
- Elle s'exécute après la correction des erreurs d'unité du tabac du 16 novembre 2026, sur les expériences de `regional` relancées avec les données corrigées.
- Le modèle est celui de `src/models/selection.py`, avec ses variables, ses paramètres et son nombre d'arbres, sans réajustement. Seules les douze variables climatiques changent d'un horizon à l'autre.
- Les fenêtres d'évaluation sont celles de `docs/research_rolling_windows.md`. Pour chaque fenêtre, le modèle et la référence n'apprennent que sur les récoltes antérieures au début de la fenêtre.
- Aucune observation postérieure à la date de prévision n'entre dans les variables d'une prédiction, ni à l'entraînement, ni à l'évaluation.

## 4. Horizons

La saison d'une ligne est la fenêtre de jours de `climat_regional.csv.gz`, du premier jour du mois de semis au dernier jour du mois de récolte. Les indicateurs climatiques sont recalculés sur la partie de cette fenêtre observée à la date de prévision, avec les mêmes formules et les mêmes séries que les variables du projet.

| Horizon | Date de prévision | Jours observés | Variables climatiques |
|---|---|---|---|
| Semis | Début de la saison | Aucun | Aucune, ce qui correspond à la variante sans climat |
| Mi-saison | Milieu de la saison | Première moitié de la fenêtre, arrondie au jour inférieur | Indicateurs de la première moitié |
| Un mois avant la récolte | Fin du mois qui précède le mois de récolte | Du semis à la fin de ce mois | Indicateurs de cette période |
| Fin de saison | Fin du mois de récolte | Toute la fenêtre | Indicateurs de la saison entière, soit le modèle retenu |

Une saison d'un seul mois n'a aucun jour observé un mois avant la récolte. Ses variables climatiques sont alors manquantes à cet horizon, et leur nombre est rapporté.

**Représentation du reste de la saison**

`docs/estimation_et_prevision.md` envisageait de remplacer la partie non observée de la saison par la climatologie du lieu. Ce plan retient une autre méthode. Pour chaque horizon, le modèle est réentraîné sur les indicateurs de la seule partie observée, si bien qu'il apprend lui-même le rendement attendu compte tenu de l'information disponible. Ce choix est justifié par deux raisons. D'une part, un modèle entraîné sur des saisons entières recevrait avec une climatologie moyenne des entrées qu'il n'a jamais vues, car une moyenne de plusieurs années ne présente ni séquence sèche ni jour sans pluie en saison humide. D'autre part, la séquence sèche maximale n'est pas additive et ne se compose pas simplement d'une partie observée et d'une partie climatologique. Ce changement de méthode est un écart assumé à la proposition de `docs/estimation_et_prevision.md`.

## 5. Métriques

- L'erreur `mae_log` du modèle et de la référence, la compétence et le biais logarithmique, par horizon et par fenêtre, puis sur l'ensemble des lignes des quatre fenêtres.
- Le prix de l'anticipation d'un horizon, différence entre son erreur et celle de la fin de saison, avec un intervalle de confiance à 95 % obtenu par bootstrap des groupes du protocole, avec 2 000 tirages et la graine 0.
- Le gain du modèle sur la référence à chaque horizon, avec le même intervalle.
- Les mêmes différences par classe d'aridité, selon les classes et l'indice de `docs/research_climate_zones.md`, pour les classes d'au moins 1 000 lignes évaluées.

## 6. Hypothèses

- **H1.** À chaque horizon et dans chacune des quatre fenêtres, le modèle bat significativement la référence.
- **H2.** Sur l'ensemble des quatre fenêtres, l'erreur décroît au sens large lorsque l'horizon se rapproche de la récolte, de la prévision au semis à l'estimation en fin de saison.
- **H3.** Sur l'ensemble des quatre fenêtres, le prix de l'anticipation au semis est faible, son intervalle de confiance à 95 % étant entièrement compris entre -0,01 et 0,01.
- **H4.** Dans les zones aride et semi-aride réunies, l'erreur un mois avant la récolte est significativement inférieure à l'erreur au semis.

Une hypothèse est réfutée lorsque le résultat contredit son énoncé. Les résultats sont rapportés quelle que soit leur issue.

**Attentes déclarées avant le calcul**

Les études précédentes conditionnent ces attentes. Selon `docs/research_rolling_windows_results.md`, la variante sans climat fait aussi bien ou mieux que le modèle retenu dans les quatre fenêtres. H2 sera donc probablement réfutée et H3 probablement confirmée. Selon `docs/research_climate_zones_results.md`, le climat explique davantage les rendements en zone sèche sans que le modèle l'exploite, ce qui rend H4 incertaine. L'étude reste utile, car elle mesure directement la quantité que la section 6 de `docs/estimation_et_prevision.md` laissait ouverte, et elle teste si une information partielle de saison, moins bruitée en fin de cycle, se comporte autrement que la saison entière.

## 7. Limites connues avant l'étude

- Les séries sont IMERG Final et NASA POWER dans leur version de recherche. Une prévision réelle utiliserait IMERG Early ou Late et des données POWER plus récentes, de qualité différente. Leur latence n'est pas simulée, et l'étude mesure donc l'effet de l'information disponible et non celui du délai de mise à disposition.
- Le calendrier de chaque ligne provient souvent de ses propres mois de semis et de récolte. Le mois de récolte réel n'est connu qu'à la récolte, mais il est traité ici comme le calendrier prévu, connu dès le semis.
- La pluie IMERG ne commence qu'en juin 2000. Les premières fenêtres disposent de peu d'années d'entraînement avec pluie.
- Aucune prévision saisonnière n'est utilisée. Le gain qu'elle pourrait apporter au semis n'est pas mesuré.
- Les intervalles de prédiction ne sont pas recalibrés par horizon.
- L'étude ne porte que sur `regional`. Le modèle de `survey` n'utilise pas le climat, et sa prédiction est la même à tous les horizons.
