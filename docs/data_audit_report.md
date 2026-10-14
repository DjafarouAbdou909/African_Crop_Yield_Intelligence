## Traitements préalablement appliqués aux données

D’après la documentation de GROW-Africa, plusieurs traitements ont été appliqués aux données avant leur diffusion :

- **Harmonisation des noms de cultures :** uniformisation des noms de cultures afin de faciliter leur comparaison entre les différentes sources.
- **Suppression des doublons :** élimination des observations identifiées comme doublons.
- **Harmonisation des références géographiques :** harmonisation des références géographiques et attribution d’identifiants administratifs uniques.
- **Filtrage des rendements aberrants dans les données ponctuelles :** exclusion de certaines valeurs selon des seuils calculés à partir des distributions régionales propres aux cultures.
- **Conservation des rendements aberrants dans les données nationales et infranationales :** contrairement aux données ponctuelles, ces données n’ont pas fait l’objet du même filtrage des rendements aberrants.

### Limites de la documentation

La documentation décrit ces traitements à l’échelle générale, mais ne fournit pas de dictionnaire complet précisant la signification de chaque colonne, son type, son unité, son rôle ou les règles exactes de validation applicables.

Il reste donc nécessaire d’examiner les fichiers effectivement utilisés afin de :

- documenter la signification et le type de chaque colonne ;
- vérifier les valeurs manquantes, les doublons et les incohérences ;
- identifier les relations entre les variables et les éventuelles redondances ;
- vérifier, lorsque cela est possible, les effets des traitements déjà appliqués ;
- distinguer les traitements documentés par les auteurs des constats établis lors de notre propre audit.

**Conséquence méthodologique :** le fait que les auteurs aient déjà nettoyé certaines parties du jeu de données ne garantit pas que les fichiers soient exempts d’anomalies ou adaptés directement à notre objectif de prédiction. Un audit complémentaire reste nécessaire avant toute préparation destinée à la modélisation.

### Premières observations — LSMS Crop Cut

L'examen préliminaire du fichier `GROW-Africa_LSMS_cropcut` a permis d'identifier plusieurs points nécessitant une vérification avant la préparation des données.

| Observation | Risque identifié | Action prévue | Statut |
|---|---|---|---|
| Le rendement `Yield_ton_ha_` semble dépendre de `dryWeightKg`. | Fuite de données potentielle si le poids sec intervient directement dans le calcul de la cible. | Vérifier la relation mathématique, son coefficient et les éventuelles exceptions. Exclure provisoirement `dryWeightKg` des variables explicatives. | À confirmer |
| L'année 2012 apparaît sous la forme `2,012`. | Incohérence de représentation pouvant créer une valeur distincte ou provoquer une erreur de conversion. | Vérifier la valeur d'origine et normaliser sa représentation en `2012` dans les données de travail, sans modifier les données brutes. | À vérifier |
| Plusieurs colonnes contiennent des identifiants ou des codes. | Risque d'utilisation de variables non pertinentes, de redondance ou de fuite indirecte. Risque également de perdre des informations utiles au regroupement des observations. | Examiner la signification et l'utilisation de chaque colonne. Distinguer les variables à exclure du modèle des identifiants à conserver pour l'audit et les partitions de données. | À investiguer |

Ces constats sont préliminaires. Ils devront être confirmés par des contrôles reproductibles sur le fichier complet. Aucune suppression définitive de colonne ni transformation irréversible ne sera effectuée à ce stade.

### Dataset 2 — LSMS Survey : constats préliminaires

Le fichier `GROW-Africa_LSMS_survey.csv` contient des informations associées aux enquêtes agricoles, notamment sur les cultures, la production, les superficies, les rendements, la localisation et les campagnes agricoles.

Plusieurs variantes de production, de superficie et de rendement sont présentes. Leur définition et leurs relations doivent être établies avant de sélectionner la variable cible et les variables explicatives.

Une attention particulière sera portée aux risques de fuite de données, notamment lorsque les variables candidates peuvent servir à calculer directement ou indirectement le rendement à prédire.

Les identifiants, les champs de provenance et les informations géographiques seront conservés pendant l'audit. Aucune suppression ou transformation définitive ne sera décidée avant la vérification de leur rôle, de la qualité des données et de leur utilité pour le projet.

### Dataset 3 — GROW-Africa Point : constats préliminaires

**Inventaire**

Le fichier `GROW-Africa_Point.xlsx` contient 131 812 lignes et 17 colonnes. Il rassemble des observations associées à 24 cultures, 21 pays et 6 sources distinctes.

**Structure des données**

Les variables couvrent les cultures, les années de récolte, les rendements, les superficies, les dates agricoles, les informations géographiques et la provenance des observations.

**Constats de qualité**

- Absence de coordonnées géographiques pour environ 41 % des observations.
- Absence de `L3_GID` pour environ 36,7 % des observations.
- Absence de `Area_ha_` pour environ 28,4 % des observations.
- Absence de `HarvestYear` pour 20 933 observations, associée dans le fichier à la source `CEEPA_time_avg`.
- Présence de 1 282 lignes identiques sur l'ensemble des colonnes.
- Présence de rendements élevés, avec un maximum observé de 150 tonnes par hectare.
- Présence de superficies égales à zéro et de dates dont le format ou la plausibilité doit être vérifié.

**Risques méthodologiques**

La comparabilité des observations provenant de différentes sources doit être examinée. Les valeurs extrêmes, les doublons et les données manquantes nécessitent une investigation avant toute transformation. Si `Yield_ton_ha_` est retenue comme variable cible, elle devra être exclue des variables d'entrée.
