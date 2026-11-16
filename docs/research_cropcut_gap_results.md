# Résultats de l'étude sur l'écart entre rendements déclarés et mesures par coupe

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Plan préenregistré | `docs/research_cropcut_gap.md`, versionné avant tout calcul |
| Code | `src/recherche/ecart_cropcut.py` et `tests/test_recherche_ecart_cropcut.py` |
| Notebook de référence | `notebooks/17_cropcut_gap_study.ipynb` |
| Figure | `reports/figures/ecart_cropcut.png` |
| Statut | Étude achevée, trois hypothèses confirmées et une réfutée |

## 1. Résumé

Sur les mêmes grappes, cultures et années éthiopiennes, le rendement déclaré par les ménages dépasse la mesure par coupe d'environ 30 %, et d'environ 63 % sur les petites parcelles, alors que l'écart n'est pas significatif sur les grandes. La limite du modèle de `survey` sur `cropcut` tient donc d'abord à sa cible, le rendement déclaré. Une correction par culture, apprise sur les grappes vues, réduit l'erreur sur les grappes jamais vues de 0,669 à 0,625 et le biais de 0,333 à 0,083. Elle ne donne cependant au modèle aucune avance significative sur une référence corrigée de la même façon.

## 2. Comparaison des deux mesures

**Constat**

| Strate | Cellules | Écart déclaré moins mesuré | Intervalle à 95 % |
|---|---:|---:|---|
| Toutes les cellules | 2 071 | 0,262 | 0,206 à 0,315 |
| Petites parcelles | 691 | 0,490 | 0,406 à 0,571 |
| Parcelles moyennes | 690 | 0,224 | 0,151 à 0,299 |
| Grandes parcelles | 690 | 0,070 | -0,012 à 0,154 |
| Petites moins grandes | 1 381 | 0,420 | 0,311 à 0,536 |

- L'écart est positif pour les sept cultures étudiées, de 0,120 pour le teff à 0,435 pour l'orge.
- Sur les 6 490 mesures des cellules appariées, prédire la mesure par coupe par la moyenne déclarée de sa cellule donne une erreur `mae_log` de 0,733, contre 0,656 pour le modèle et 0,717 pour la référence, toutes deux hors pli.

**Analyse**

- Le résultat reproduit celui de Desiere et Jolliffe sur les mêmes enquêtes. La déclaration surestime surtout la récolte des petites parcelles, où une erreur sur la production pèse davantage rapportée à la surface.
- Même une connaissance parfaite des déclarations de la cellule prédit la mesure par coupe moins bien que le modèle. L'erreur sur `cropcut` provient surtout de l'écart entre méthodes et de la variabilité d'une parcelle à l'autre au sein d'une grappe, qu'un meilleur modèle du rendement déclaré ne peut pas supprimer.

## 3. Correction des prédictions

**Constat**

| Méthode | Erreur croisée du modèle | Erreur croisée de la référence |
|---|---:|---:|
| C0, aucune correction | 0,6605 | 0,7114 |
| C1, décalage unique | 0,6318 | 0,7024 |
| C2, décalage par culture | 0,6268 | 0,6985 |
| C3, droite de recalibration | 0,6264 | 0,6603 |

- La règle du plan retient C2 pour le modèle, à moins de 0,005 de C3, et C3 pour la référence. Ces choix ont été versionnés avant l'évaluation finale.
- Le décalage global vaut -0,243. Par culture, il va de -0,102 pour le mil à -0,778 pour l'arachide. La droite de la référence a une pente de 0,371.

| Grappes tenues à l'écart, 2 297 mesures | Sans correction | Avec correction |
|---|---:|---:|
| Erreur `mae_log` du modèle | 0,669 | 0,625 |
| Erreur `mae_log` de la référence | 0,676 | 0,635 |
| Compétence | 1,1 % | 1,6 % |
| Biais logarithmique du modèle | 0,333 | 0,083 |

- Le gain de la correction vaut 0,043, avec un intervalle de 0,019 à 0,070.
- L'avance du modèle corrigé sur la référence corrigée vaut 0,010, avec un intervalle de -0,019 à 0,038.

**Analyse**

- La correction se transpose aux grappes jamais vues et ramène le biais au quart de sa valeur. Le biais restant, positif, indique que l'écart des grappes tenues à l'écart dépasse celui de la calibration.
- La référence profite autant de la correction que le modèle. À l'échelle de la parcelle mesurée par coupe, les variables du modèle n'apportent presque rien au-delà de la moyenne locale.

## 4. Hypothèses

| Hypothèse | Énoncé résumé | Verdict | Élément décisif |
|---|---|---|---|
| H1 | Le rendement déclaré dépasse la mesure par coupe | Confirmée | 0,262, de 0,206 à 0,315 |
| H2 | L'écart est plus grand sur les petites parcelles que sur les grandes | Confirmée | 0,420, de 0,311 à 0,536 |
| H3 | La correction retenue réduit l'erreur sur les grappes tenues à l'écart | Confirmée | 0,043, de 0,019 à 0,070 |
| H4 | Le modèle corrigé bat la référence corrigée | Réfutée | 0,010, de -0,019 à 0,038 |

## 5. Conséquences pour le projet

- Les prédictions de `survey` sont des rendements déclarés. La documentation et l'application doivent les présenter comme tels, et jamais comme des rendements mesurés.
- Pour un usage qui exige des rendements mesurés en Éthiopie, la correction par culture de cette étude réduit l'erreur et la plus grande partie du biais. Elle n'a été validée que dans ce pays.
- L'écart dépendant fortement de la surface des parcelles, une correction par classe de surface serait plus juste. Elle exigerait de connaître la surface au moment de la prédiction, ce que `cropcut` ne fournit pas.
- Étendre la correction aux autres pays de `survey` exigerait des mesures par coupe dans ces pays.
- Le modèle retenu et l'évaluation de `docs/evaluation.md` ne sont pas modifiés. La correction n'est appliquée ni au modèle déployé ni à l'application, ce choix revenant au porteur du projet.

## 6. Écarts au plan

- 82 mesures des grappes vues, sans coordonnées et donc sans grappe ni groupe, ne pouvaient recevoir aucun pli. Elles ont été écartées de la calibration, qui compte 8 884 mesures au lieu de 8 966.

## 7. Limites

- Toutes les mesures par coupe sont éthiopiennes.
- La mesure par coupe n'est pas une vérité parfaite et peut surestimer la récolte, car le carré récolté ignore les pertes au champ et les bordures.
- La comparaison par cellule mélange des parcelles différentes. Elle mesure l'écart moyen entre deux méthodes au même lieu, pour la même culture et la même saison.
- La correction est estimée sur des prédictions hors pli et appliquée au modèle final, entraîné sur tout le développement.
- Les grappes tenues à l'écart avaient déjà été lues une fois dans `docs/evaluation.md`. Seul le gel du choix avant cette seconde lecture en garantit l'indépendance.
