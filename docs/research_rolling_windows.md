# Plan d'étude préenregistré sur la stabilité temporelle par fenêtres successives

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Origine | Deuxième suggestion de la revue du projet par une mentore experte |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/modeling.md`, section 4.2, et `docs/research_spatial_blocks_results.md` |

## 1. Motivation

La validation temporelle interne du projet repose sur une seule coupure, en 2012. Un résultat obtenu sur une seule période peut dépendre de cette période, de ses conditions climatiques ou de ses sources de données. L'étude sur la couverture conforme a d'ailleurs montré un écart entre la validation interne et les ensembles de test. La revue du projet a suggéré d'évaluer le modèle sur plusieurs fenêtres chronologiques successives pour vérifier la stabilité des résultats.

## 2. Question de recherche

Le modèle retenu de `regional` bat-il la référence de façon stable d'une période à l'autre, et l'apport des variables climatiques est-il lui aussi stable ?

## 3. Précautions

- L'étude n'utilise que le développement, dont les récoltes vont de 1981 à 2016. Les ensembles de test ne sont pas consultés.
- Le modèle est celui de `src/models/selection.py`, avec ses variables, ses paramètres et ses 2 000 arbres, sans réajustement.
- Pour chaque fenêtre, le modèle et la référence n'apprennent que sur les récoltes antérieures au début de la fenêtre, selon une origine glissante à fenêtre d'entraînement croissante.

## 4. Fenêtres

| Fenêtre | Années évaluées | Années d'entraînement |
|---|---|---|
| F1 | 2004 à 2006 | 1981 à 2003 |
| F2 | 2007 à 2009 | 1981 à 2006 |
| F3 | 2010 à 2012 | 1981 à 2009 |
| F4 | 2013 à 2016 | 1981 à 2012 |

Deux variantes sont évaluées dans chaque fenêtre, le modèle retenu et le même modèle privé des douze variables climatiques.

## 5. Métriques

- L'erreur `mae_log` du modèle et de la référence, la compétence et le biais logarithmique, par fenêtre.
- Le gain du modèle sur la référence et l'apport du climat, différence d'erreur entre la variante sans climat et le modèle retenu, chacun avec un intervalle de confiance à 95 % obtenu par bootstrap des groupes du protocole.

## 6. Hypothèses

- **H1.** Le modèle bat significativement la référence dans chacune des quatre fenêtres.
- **H2.** La compétence est stable, l'écart entre la plus forte et la plus faible compétence des quatre fenêtres ne dépassant pas 10 points.
- **H3.** Le climat améliore le modèle dans au moins trois fenêtres sur quatre.
- **H4.** Dans chaque fenêtre, le biais logarithmique du modèle est plus faible en valeur absolue que celui de la référence.

Une hypothèse est réfutée lorsque le résultat contredit son énoncé. Les résultats sont rapportés quelle que soit leur issue.

## 7. Limites connues avant l'étude

- La pluie IMERG ne commence qu'en juin 2000. Les premières fenêtres disposent donc de peu d'années d'entraînement avec pluie, ce qui peut réduire l'apport apparent du climat au début de la période.
- Les fenêtres n'ont pas les mêmes pays ni les mêmes sources, ce qui mêle l'effet du temps et celui de la composition.
- L'étude ne porte que sur `regional`. `survey` compte trop peu de vagues par pays pour une validation sur plusieurs fenêtres.
