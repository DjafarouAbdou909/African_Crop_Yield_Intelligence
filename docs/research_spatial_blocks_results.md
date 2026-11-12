# Résultats de l'étude sur la validation par blocs géographiques

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Plan préenregistré | `docs/research_spatial_blocks.md`, versionné avant tout calcul |
| Code | `src/recherche/validation_spatiale.py` et `tests/test_recherche_validation_spatiale.py` |
| Notebook de référence | `notebooks/14_spatial_blocks_study.ipynb` |
| Figure | `reports/figures/blocs_geographiques.png` |
| Statut | Étude achevée, quatre hypothèses confirmées |

## 1. Résumé

La validation croisée du protocole surestime nettement la capacité du modèle de `regional` à prédire une région éloignée de ses données d'entraînement. Lorsque des blocs géographiques entiers ou des pays entiers sont tenus à l'écart, l'erreur passe de 0,358 à 0,504 à 0,545, et le gain du modèle sur la référence, de 14 % dans la validation du protocole, devient faible et non significatif. Le modèle bat la référence de 11 % à moins de 250 km des données d'entraînement, mais fait moins bien qu'elle au-delà de 1 000 km.

## 2. Résultats

**Constat**

| Schéma | Distance médiane à l'entraînement | Erreur du modèle | Erreur de la référence | Compétence | Gain significatif |
|---|---:|---:|---:|---:|---|
| S0, validation du protocole | | 0,358 | 0,417 | 14,1 % | Oui |
| S1, un pays tenu à l'écart | 181 km | 0,545 | 0,553 | 1,3 % | Non |
| S2, blocs géographiques | 595 km | 0,504 | 0,519 | 2,9 % | Non |
| S3, blocs et zone tampon de 250 km | 747 km | 0,537 | 0,544 | 1,3 % | Non |

- Les hausses d'erreur par rapport à S0, de 0,146 à 0,187, sont toutes significatives par bootstrap des pays.
- Dans S2, la compétence vaut 10,8 % à moins de 250 km de la zone d'entraînement la plus proche, 7,7 % de 250 à 500 km, moins de 4 % de 500 à 1 000 km et -13,7 % au-delà de 1 500 km.
- Lorsqu'il est tenu à l'écart, le modèle fait moins bien que la référence dans 18 pays sur 45, dont l'Afrique du Sud, l'Égypte et Madagascar.

**Analyse**

- L'avantage du modèle repose surtout sur ce qu'il apprend des régions voisines et du pays lui-même. Les relations entre rendement, climat, sol et relief qu'il a apprises se transposent mal d'une région du continent à une autre.
- Tenir un pays à l'écart coûte davantage que tenir un bloc à l'écart, alors que la zone d'entraînement la plus proche y est trois fois plus proche. Le pays porte des conditions agricoles et des façons de produire les statistiques que les variables explicatives ne décrivent pas.

## 3. Hypothèses

| Hypothèse | Énoncé résumé | Verdict | Élément décisif |
|---|---|---|---|
| H1 | L'erreur augmente d'au moins 0,02 de S0 à S2 | Confirmée | Hausse de 0,146 |
| H2 | La compétence reste positive dans S1, S2 et S3 | Confirmée au sens strict | De 1,3 à 2,9 %, mais aucun gain significatif |
| H3 | L'erreur croît avec la distance | Confirmée | Corrélation de rang de 0,109 |
| H4 | La zone tampon augmente l'erreur | Confirmée | Hausse de 0,033 par rapport à S2 |

L'énoncé de H2 ne demandait pas de significativité. Il était trop peu exigeant, et son verdict ne doit pas être lu comme une généralisation réussie.

## 4. Conséquences pour le projet

- Les scores spatiaux de `docs/evaluation.md` valent pour des régions proches des données d'entraînement, à quelques centaines de kilomètres au plus.
- Pour une région éloignée de plus de 500 km ou pour un pays absent de la base, le modèle n'apporte rien de mesurable par rapport à la moyenne de la culture, et il ne doit pas être utilisé dans ce cas.

## 5. Limites

- Le nombre de blocs et le rayon de la zone tampon ont été fixés a priori.
- L'effet de l'éloignement et celui de l'absence d'effet pays appris restent mêlés.
- Le modèle n'a pas été conçu pour l'extrapolation lointaine. Un modèle sans variable de pays, ou fondé sur des zones agroécologiques, reste à tester.

## 6. Suite proposée

Une seconde étude pourrait comparer, dans le schéma des blocs, le modèle retenu à un modèle privé de la variable de pays et à un modèle utilisant des zones agroécologiques. Elle dirait si une meilleure transposition lointaine est possible, et à quel prix pour les régions proches. Elle rejoindrait la troisième suggestion de la revue, sur l'analyse du climat par zone agroécologique.
