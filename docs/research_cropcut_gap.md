# Plan d'étude préenregistré sur l'écart entre rendements déclarés et mesures par coupe

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Origine | Quatrième suggestion de la revue du projet par une mentore experte |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/evaluation.md`, section 4, et `docs/evaluation_protocol.md`, section 4.4 |

## 1. Motivation

Sur les 2 297 mesures par coupe des grappes tenues à l'écart, le modèle de `survey` atteint une erreur `mae_log` de 0,669 contre 0,676 pour la référence, soit une compétence de 1 %, avec un biais logarithmique de 0,333. Le modèle apprend le rendement déclaré par les ménages, rapporté à la surface mesurée par GPS, alors que `cropcut` mesure la récolte d'un carré du champ. La revue du projet a demandé comment traiter les limites observées sur ces mesures directes.

Deux explications sont possibles et n'appellent pas la même réponse. La première est un écart systématique entre les deux méthodes de mesure, que le modèle reproduit fidèlement. La seconde est une faiblesse propre au modèle. Desiere et Jolliffe ont montré en Éthiopie, à partir des mêmes enquêtes, que la production déclarée est surestimée sur les petites parcelles et sous-estimée sur les grandes, et que la relation inverse entre surface et rendement disparaît avec les mesures par coupe.

## 2. Questions de recherche

1. Sur les mêmes grappes, cultures et années, les rendements déclarés dépassent-ils les mesures par coupe, et cet écart dépend-il de la taille des parcelles ?
2. Une correction apprise sur les mesures par coupe des grappes vues à l'entraînement réduit-elle l'erreur sur les grappes tenues à l'écart ?

## 3. Données et précautions

- Seules les mesures de `cropcut` déjà retenues par `jeu_validation_cropcut` sont utilisées, soit 11 263 mesures, toutes éthiopiennes.
- Les mesures des grappes vues forment l'ensemble de calibration. Les 2 297 mesures des grappes tenues à l'écart ne servent qu'à l'évaluation finale, faite une seule fois après le gel de la méthode.
- Les lignes de `survey` utilisées pour la comparaison des mesures appartiennent toutes au développement. Les ensembles de test de `survey` ne sont pas consultés.
- `cropcut` ne sert toujours pas à l'entraînement du modèle de rendement. Il ne sert qu'à apprendre une correction appliquée après la prédiction.
- L'appariement à la parcelle n'est pas utilisé. Les identifiants de ménage de `survey` sont tronqués pour une partie des vagues et n'ont pas le même format que ceux de `cropcut`, et la clé formée de la grappe, de la culture, de l'année, de la parcelle et du champ associe plusieurs lignes de `survey` à 2 406 mesures. L'unité de comparaison est donc la cellule formée de la grappe, de la culture et de l'année de récolte.

## 4. Partie A, comparaison des deux mesures

Pour chaque cellule présente à la fois dans `cropcut` et dans le développement de `survey`, parmi les grappes vues, l'écart vaut la moyenne du logarithme du rendement déclaré diminuée de la moyenne du logarithme du rendement mesuré par coupe. Chaque cellule pèse autant.

- L'écart moyen est rapporté avec un intervalle de confiance à 95 % obtenu par bootstrap des groupes du protocole.
- Les cellules sont réparties en trois classes de même effectif selon la moyenne du logarithme de la surface GPS de leurs parcelles de `survey`. L'écart des petites parcelles est comparé à celui des grandes, avec un intervalle bootstrap sur la différence.
- L'écart est aussi rapporté par culture, pour les cultures qui comptent au moins 100 cellules.
- À titre descriptif, l'erreur `mae_log` obtenue en prédisant chaque mesure par coupe par la moyenne géométrique des rendements déclarés de sa cellule est comparée à celle du modèle sur les mêmes mesures. Elle indique la part de l'erreur que la seule différence de méthode impose.

## 5. Partie B, correction des prédictions

### 5.1 Prédictions hors pli

Les prédictions des mesures de calibration ne doivent pas provenir d'un modèle qui a vu leur grappe. Le modèle retenu pour `survey`, avec sa configuration figée dans `src/models/selection.py`, est donc entraîné cinq fois, chaque fois sans un pli du développement. Chaque mesure de calibration est prédite par le modèle qui n'a pas vu le pli de son groupe, le pli étant calculé par la même empreinte que dans le protocole. La référence hiérarchique est calculée de la même façon.

### 5.2 Méthodes comparées

| Code | Correction du logarithme de la prédiction |
|---|---|
| C0 | Aucune |
| C1 | Ajout d'un décalage unique, médiane de l'écart entre le logarithme de la mesure et celui de la prédiction |
| C2 | Décalage propre à chaque culture, remplacé par le décalage unique pour une culture de moins de 100 mesures de calibration |
| C3 | Droite de recalibration estimée par moindres carrés, le logarithme de la mesure étant expliqué par celui de la prédiction |

La médiane est retenue pour C1 et C2, car elle minimise l'erreur absolue.

### 5.3 Règle de choix

Chaque méthode est évaluée par validation croisée à cinq plis groupés sur l'ensemble de calibration, les plis étant ceux du protocole. La méthode retenue a la plus faible erreur `mae_log` moyenne. Une méthode plus complexe n'est retenue que si elle fait mieux que la plus simple de plus de 0,005, l'ordre de complexité étant C0, C1, C2 puis C3. La même règle choisit la correction de la référence, estimée sur ses propres prédictions hors pli. Les deux choix sont versionnés avant l'évaluation finale.

### 5.4 Évaluation finale

La correction retenue est estimée sur tout l'ensemble de calibration, puis appliquée aux prédictions du modèle final de `docs/evaluation.md` sur les 2 297 mesures des grappes tenues à l'écart. La référence reçoit sa propre correction. L'erreur `mae_log`, le biais logarithmique et la compétence sont rapportés avant et après correction.

## 6. Hypothèses

- **H1.** Les rendements déclarés dépassent les mesures par coupe des mêmes cellules, avec un écart moyen significativement positif.
- **H2.** L'écart est plus grand dans le tiers des cellules aux plus petites parcelles que dans le tiers aux plus grandes, avec une différence significativement positive.
- **H3.** La correction retenue réduit significativement l'erreur `mae_log` du modèle sur les grappes tenues à l'écart. Si la méthode retenue est C0, H3 est réfutée.
- **H4.** Après correction, le modèle bat significativement la référence corrigée sur les grappes tenues à l'écart.

Une différence est significative lorsque son intervalle de confiance à 95 %, obtenu par bootstrap des groupes du protocole avec 2 000 tirages, exclut zéro. Une hypothèse est réfutée lorsque le résultat contredit son énoncé. Les résultats sont rapportés quelle que soit leur issue.

## 7. Limites connues avant l'étude

- Toutes les mesures par coupe sont éthiopiennes. Une correction apprise ici ne vaut pas pour les onze autres pays de `survey`.
- La mesure par coupe n'est pas une vérité parfaite. Elle peut surestimer la récolte, car le carré récolté ignore les pertes au champ et les bordures moins productives.
- La comparaison par cellule mélange des parcelles différentes. Elle mesure l'écart moyen entre deux méthodes appliquées au même lieu, à la même culture et à la même saison, et non l'écart sur une même parcelle.
- La correction est estimée sur des prédictions hors pli, mais appliquée au modèle final entraîné sur tout le développement, dont les erreurs peuvent être un peu plus faibles.
- La mesure finale a déjà été consultée une fois, lors de l'évaluation de `docs/evaluation.md`. Seul le gel de la méthode avant cette seconde lecture garantit que le choix n'en dépend pas.

## 8. Référence

Desiere, S. et Jolliffe, D. 2018. Land productivity and plot size. Is measurement error driving the inverse relationship? Journal of Development Economics, volume 130, pages 84 à 98. https://doi.org/10.1016/j.jdeveco.2017.10.002
