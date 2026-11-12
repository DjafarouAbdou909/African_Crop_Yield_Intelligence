# Plan d'étude préenregistré sur la validation par blocs géographiques

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Étude de recherche prolongeant la phase Evaluation |
| Origine | Première suggestion de la revue du projet par une mentore experte |
| Statut | Plan préenregistré, versionné avant tout calcul de l'étude |
| Documents associés | `docs/evaluation_protocol.md`, section 9, et `docs/modeling.md` |

## 1. Motivation

La validation croisée du protocole tient à l'écart des régions de niveau 1, réunies avec leurs unités de niveau 2. Le protocole relève lui-même sa limite à la section 9. Une région tenue à l'écart peut ressembler fortement à une région voisine présente à l'entraînement, par son climat, ses sols et ses pratiques. La validation mesure alors la prédiction d'une région nouvelle, mais pas celle d'une région éloignée des données d'entraînement. La revue du projet a suggéré de mesurer cet écart par une validation par blocs géographiques.

## 2. Question de recherche

De combien l'erreur du modèle retenu de `regional` augmente-t-elle lorsque les régions évaluées sont éloignées de toute région d'entraînement, et le modèle bat-il encore la référence dans ce cas ?

## 3. Précautions

- L'étude n'utilise que le développement. Les ensembles de test ne sont pas consultés.
- Le modèle est celui de `src/models/selection.py`, avec ses variables, ses paramètres et ses 2 000 arbres. Il n'est pas réajusté pour les nouveaux schémas, afin de mesurer la généralisation du modèle tel qu'il a été choisi.
- La référence hiérarchique est recalculée dans chaque schéma, sur les mêmes lignes d'entraînement.

## 4. Schémas comparés

| Code | Schéma | Lignes évaluées |
|---|---|---|
| S0 | Validation croisée à cinq plis groupés du protocole | Tout le développement |
| S1 | Un pays tenu à l'écart à chaque fois | Tout le développement |
| S2 | Blocs géographiques. Les centroïdes des zones sont regroupés en 8 blocs par la méthode des k-moyennes sur leurs coordonnées cartésiennes à la surface du globe, avec une graine fixe, et chaque bloc est tenu à l'écart à son tour | Tout le développement |
| S3 | Blocs de S2 avec zone tampon. Les zones d'entraînement dont le centroïde est à moins de 250 km d'une zone du bloc évalué sont retirées de l'entraînement | Tout le développement |

## 5. Métriques

- L'erreur `mae_log` du modèle et de la référence, et la compétence, part de l'erreur de la référence supprimée par le modèle.
- Les écarts entre schémas, accompagnés d'intervalles de confiance à 95 % obtenus par bootstrap des pays, unité la plus large commune à tous les schémas.
- Pour S2, l'erreur du modèle selon la distance entre la zone évaluée et la zone d'entraînement la plus proche, par classes de distance.

## 6. Hypothèses

- **H1.** L'erreur du modèle augmente d'au moins 0,02 en passant de S0 à S2.
- **H2.** Le modèle conserve une compétence positive dans S1, S2 et S3.
- **H3.** Dans S2, l'erreur croît avec la distance à la zone d'entraînement la plus proche, avec une corrélation de rang positive entre distance et erreur absolue.
- **H4.** La zone tampon de S3 augmente l'erreur par rapport à S2.

Une hypothèse est réfutée lorsque le résultat contredit son énoncé. Les résultats sont rapportés quelle que soit leur issue.

## 7. Limites connues avant l'étude

- Le nombre de blocs et le rayon de la zone tampon sont fixés a priori et ne sont pas optimisés. D'autres choix pourraient donner des écarts différents.
- Dans S1 et S2, la modalité du pays évalué est inconnue du modèle, ce qui mêle l'effet de l'éloignement et celui de l'absence d'effet pays appris.
- Le modèle n'est pas réajusté pour chaque schéma. Un modèle conçu pour l'extrapolation lointaine pourrait faire mieux.
