# Protocole d'évaluation des modèles GROW-Africa

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Méthodologie | CRISP-DM, phase 4 Modeling, conception du plan de test |
| Code | `src/evaluation/` et `tests/` |
| Notebook de référence | `notebooks/04_evaluation_protocol.ipynb` |
| Documents associés | `docs/data_preparation.md` et `docs/data_understanding.md` |
| Statut | Protocole défini, implémenté et testé |

## 1. Objet du document

Ce document fixe la manière dont les modèles de rendement seront évalués, avant l'entraînement du premier modèle. Il remplit la troisième condition de la décision issue du Data Understanding.

## 2. Exigences

- Aucun lieu ne doit figurer à la fois dans l'entraînement et dans l'évaluation. Les parcelles d'une même grappe partagent leur sol et leur climat, les ménages du panel reviennent d'une vague à l'autre, et une région de niveau 1 recouvre ses unités de niveau 2.
- La capacité à prédire une période future et la capacité à prédire un lieu jamais observé sont mesurées séparément.
- Les ensembles de test ne servent qu'une fois, à la fin de la modélisation. Toute sélection de modèle s'appuie sur la validation croisée du développement.
- Tout modèle est comparé à une référence dépourvue de variable explicative.

## 3. Organisation du code

| Module | Rôle |
|---|---|
| `src/evaluation/partitions.py` | Construction des groupes, affectation aux partitions et aux plis de validation croisée |
| `src/evaluation/metriques.py` | Métriques globales, ventilées et moyennes non pondérées, score de compétence |
| `src/evaluation/references.py` | Modèle de référence par moyenne géométrique hiérarchique |

La suite de tests compte 40 tests unitaires à la création du protocole.

## 4. Partitions

### 4.1 Principe

Le croisement de deux critères définit quatre partitions.

| Partition | Lieu | Période |
|---|---|---|
| `developpement` | Groupe conservé | Passée |
| `test_temporel` | Groupe conservé | Future |
| `test_spatial` | Groupe tenu à l'écart | Passée |
| `test_spatio_temporel` | Groupe tenu à l'écart | Future |

Un groupe est tenu à l'écart lorsque l'empreinte SHA-256 de son identifiant tombe dans les 20 premiers centièmes. Le développement est réparti en 5 plis, chaque groupe appartenant à un seul pli. Cette affectation est reproductible, indépendante de l'ordre des lignes et stable lorsque des données sont ajoutées.

### 4.2 Groupes et période future

| Jeu | Groupe | Période future |
|---|---|---|
| `regional` | Région de niveau 1 et unités de niveau 2 rattachées, réunies par composantes connexes | Années de récolte à partir de 2017 |
| `survey` | Grappes et ménages partageant des parcelles, réunis par composantes connexes. À défaut, zone de niveau 2 puis ligne | Dernière vague des pays qui en comptent au moins deux |
| `cropcut` | Groupe de la grappe dans `survey` | Sans objet |

Les composantes connexes placent du même côté un agrégat régional et ses composantes, y compris au Ghana où des unités de niveau 2 sont rattachées à plusieurs régions. Elles suivent aussi un ménage du panel d'une vague à l'autre lorsque ses coordonnées changent.

### 4.3 Effectifs

| Partition | `regional` | Pays | `survey` | Pays |
|---|---:|---:|---:|---:|
| `developpement` | 105 724 | 45 | 82 301 | 12 |
| `test_temporel` | 13 226 | 22 | 39 112 | 9 |
| `test_spatial` | 23 817 | 39 | 20 495 | 12 |
| `test_spatio_temporel` | 3 110 | 17 | 9 230 | 9 |

Aucun groupe n'est présent des deux côtés de la partition. 23 pays de `regional` n'ont aucune donnée à partir de 2017, et 6 pays n'ont aucune région tenue à l'écart. Le Bénin, la Côte d'Ivoire et la Guinée-Bissau ne comptent qu'une vague dans `survey` et ne contribuent qu'à l'évaluation spatiale.

### 4.4 Validation externe sur `cropcut`

454 des 497 grappes de `cropcut` figurent dans `survey`. Seules les 2 297 mesures appartenant aux 99 grappes tenues à l'écart constituent une validation indépendante de l'entraînement. `cropcut` n'est jamais utilisé pour l'entraînement.

## 5. Métriques

| Métrique | Rôle |
|---|---|
| `mae_log` | Métrique principale. Erreur absolue moyenne sur le logarithme népérien du rendement, comparable entre cultures |
| Erreur relative typique | Exponentielle de `mae_log` diminuée de un |
| Erreurs absolue et quadratique en tonnes par hectare | Interprétation en unités physiques |
| Biais et biais logarithmique | Détection d'une surestimation ou d'une sous-estimation systématique |
| Coefficient de détermination | Part de la variance expliquée |
| Moyenne non pondérée par pays | Même poids pour chaque pays, quel que soit son nombre de lignes |
| Score de compétence | Part de l'erreur `mae_log` de la référence supprimée par le modèle |

L'erreur quadratique en tonnes par hectare varie de 3,559 à 16,048 selon l'ensemble de `regional`, alors que `mae_log` reste comprise entre 0,388 et 0,417. Elle est dominée par les cultures à rendement élevé et ne peut servir de métrique principale.

## 6. Modèles de référence

La référence prédit la moyenne géométrique des rendements d'entraînement au niveau le plus fin observé, puis se replie sur des niveaux plus larges.

| Jeu | Niveaux successifs |
|---|---|
| `regional` | Culture, saison et zone. Culture, saison et région de niveau 1. Culture et pays. Culture |
| `survey` | Culture et grappe. Culture et zone de niveau 2. Culture et zone de niveau 1. Culture et pays. Culture |

Une saison manquante forme une modalité, car elle désigne une culture à saison unique. Toute autre valeur manquante fait passer au niveau suivant, afin que des lignes sans localisation ne soient pas traitées comme un lieu commun.

**Scores de référence à battre, en `mae_log`**

| Jeu | Validation croisée | Test temporel | Test spatial | Test spatio-temporel |
|---|---:|---:|---:|---:|
| `regional` | 0,417 | 0,398 | 0,388 | 0,404 |
| `survey` | 0,772 | 0,828 | 0,756 | 0,822 |
| `cropcut`, validation externe | | | 0,676 | |

## 7. Enseignements des références

- **Variabilité annuelle.** Dans `regional`, la moyenne de la culture dans le pays prédit une région inconnue presque aussi bien que l'historique de la zone ne prédit une année future. Les variations d'une année à l'autre pèsent donc autant que les différences entre régions, ce qui justifie des variables climatiques annuelles.
- **Tendance.** Le biais logarithmique vaut -0,086 sur le test temporel et -0,113 sur le test spatio-temporel de `regional`, et -0,236 sur le test temporel de `survey`. Les rendements récents sont sous-estimés, et les modèles devront intégrer une tendance temporelle.
- **Sources.** En validation croisée, `FAO_subnational` présente un biais logarithmique de -0,249, contre 0,018 pour `HarvestStat`. La source devra figurer parmi les variables ou dans la ventilation des scores.
- **Échelle de la parcelle.** L'erreur de la référence est près de deux fois plus élevée dans `survey` que dans `regional`, ce qui reflète le bruit de mesure et l'hétérogénéité entre parcelles voisines.
- **Biais des enquêtes.** Sur `cropcut`, le biais logarithmique de 0,252 indique que les rendements d'enquête dépassent les mesures directes d'environ 29 %. Ce biais sera rapporté pour chaque modèle et ne sera pas corrigé sans validation spécifique.
- **Surfaces GPS recopiées.** Les retirer ne modifie pas l'erreur de la référence en validation croisée et la fait passer de 0,828 à 0,835 sur le test temporel. Leur effet devra être réévalué avec les modèles, qui pourront utiliser la surface.

## 8. Règles du protocole

1. Les modèles et leurs hyperparamètres sont sélectionnés par validation croisée à 5 plis groupés, sur le développement uniquement.
2. Les ensembles de test sont évalués une seule fois, à la fin de la modélisation, pour les modèles retenus.
3. Un modèle n'est retenu que s'il obtient un score de compétence positif en validation croisée et le confirme sur les ensembles de test.
4. Les variables explicatives doivent être disponibles au moment de la prédiction et ne jamais provenir d'une colonne classée comme fuite dans `docs/data_dictionary.md`.
5. Tout encodage fondé sur la cible, comme une moyenne par zone, est recalculé à l'intérieur de chaque pli d'entraînement.
6. Les scores sont ventilés par partition, pays, culture et niveau administratif, et par source pour `regional`.
7. Les scores de `survey` sont rapportés avec et sans les surfaces GPS recopiées.

## 9. Limites

- Les plis de `regional` comptent de 17 347 à 25 647 lignes, car un groupe correspond à une région entière. Cette inégalité est le prix de l'étanchéité.
- Le test temporel de `regional` ne couvre que 22 pays et provient de `HarvestStat` pour 10 838 de ses 13 226 lignes.
- La validation croisée du développement mesure la généralisation spatiale. Aucun pli ne mesure spécifiquement la généralisation temporelle à l'intérieur du développement.
- Les groupes ne tiennent pas compte de la proximité entre régions voisines. Une région tenue à l'écart peut ressembler à une région voisine présente dans le développement.

## 10. Reproductibilité

- Les tests s'exécutent depuis la racine du projet avec la commande `python -m unittest discover -s tests -t .`.
- Le notebook de référence s'appuie sur les jeux produits par `python -m src.data.prepare` et s'exécute en moins de deux minutes.

## 11. Suite du pipeline

Les jeux préparés ne contiennent que la cible, la culture, le lieu, la saison et l'année. Les variables explicatives doivent maintenant être choisies et acquises, notamment pour le climat, les sols et la végétation observée par satellite, puis raccordées par les identifiants GADM ou les coordonnées.
