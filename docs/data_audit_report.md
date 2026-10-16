## Audit des données — Data Understanding

### Objectif

Cette étape vise à comprendre la structure, la signification, la provenance et la qualité des données du projet **African Crop Yield Intelligence**, conformément à la phase *Data Understanding* de la méthodologie CRISP-DM.

L’objectif est d’évaluer si les données sont suffisamment documentées, cohérentes et adaptées à l’objectif de prédiction du rendement agricole avant d’engager leur préparation pour la modélisation.

### Datasets étudiés

L’étude porte sur les quatre fichiers suivants issus de GROW-Africa :

- `GROW-Africa_LSMS_cropcut.csv`
- `GROW-Africa_LSMS_survey.csv`
- `GROW-Africa_Point.xlsx`
- `GROW-Africa_Regional.xlsx`

Source principale : [GROW-Africa — Zenodo](https://zenodo.org/records/14961637).

Article scientifique de référence : [GROW-Africa — Scientific Data](https://www.nature.com/articles/s41597-025-05257-5).

### Méthodologie commune d'audit

Chaque dataset est étudié selon une structure commune afin de faciliter la comparaison des résultats et de garantir la cohérence de la démarche.

#### 1. Inventaire et provenance

- Identifier le fichier, son format, son nombre de lignes et de colonnes.
- Examiner les sources de données, les pays, les cultures et les périodes représentés, selon les informations disponibles.
- Vérifier la version du fichier analysé et conserver les références nécessaires à sa traçabilité.

#### 2. Compréhension des colonnes

- Documenter la signification de chaque colonne.
- Identifier son type, son unité, ses modalités et son rôle potentiel.
- Distinguer les variables explicatives candidates, la variable cible, les identifiants, les métadonnées et les variables dont le rôle reste incertain.
- Consigner les définitions inconnues ou insuffisamment documentées dans le dictionnaire des données.

Les définitions ne sont pas considérées comme confirmées lorsqu'elles reposent uniquement sur le nom d'une colonne ou sur une interprétation plausible.

#### 3. Qualité et intégrité des données

Les contrôles portent notamment sur :

- les valeurs manquantes ;
- les doublons exacts et les doublons potentiels ;
- les types de données et les formats incohérents ;
- les valeurs négatives, nulles ou extrêmes ;
- la cohérence des dates, des unités et des identifiants ;
- la cohérence des relations entre les variables.

Les anomalies détectées sont documentées avant toute décision de correction ou de suppression.

#### 4. Analyse descriptive et structurelle

Lorsque les colonnes le permettent, l'étude examine la répartition des observations par source, pays, culture, année et niveau géographique.

Cette analyse permet de comprendre la composition du dataset, d'identifier les déséquilibres éventuels et de repérer les différences de couverture entre les sources.

#### 5. Relations entre variables et risques méthodologiques

Une attention particulière est accordée aux relations entre les variables de production agricole, notamment :

- la superficie cultivée ;
- la production récoltée ;
- le rendement agricole ;
- les variables pouvant être calculées à partir de la cible ;
- les identifiants et indicateurs susceptibles d'introduire une fuite de données ou une information indirecte sur la cible.

Le rôle de chaque variable doit être évalué en fonction de sa définition et du scénario de prédiction envisagé. Une variable liée mathématiquement au rendement n'est pas automatiquement retenue comme variable explicative.

#### 6. Traitements préalablement appliqués

La documentation de GROW-Africa mentionne notamment l'harmonisation des noms de cultures et des références géographiques, la suppression de doublons et le filtrage de certains rendements aberrants dans les données ponctuelles.

Ces traitements sont considérés comme des informations documentées par les auteurs. Leur effet sur les fichiers étudiés n'est considéré comme confirmé que lorsque les éléments disponibles permettent de le vérifier.

Le nettoyage préalable effectué par les auteurs ne dispense donc pas d'un audit complémentaire.

#### 7. Actions de suivi

Pour chaque dataset, les vérifications restantes sont consignées et priorisées.

Elles peuvent concerner :

- la recherche de documentation complémentaire ;
- la confirmation de la signification des colonnes ;
- l'investigation des valeurs suspectes ;
- l'analyse des valeurs manquantes selon leur source et leur contexte ;
- la vérification des relations entre les variables ;
- la définition de règles de validation reproductibles.

Les contrôles automatisés et les transformations définitives sont définis après clarification des règles applicables.

#### 8. Conclusion et décision provisoire

Chaque audit se termine par une synthèse des constats, des risques, des incertitudes et des actions nécessaires.

La décision provisoire est exprimée selon trois niveaux :

- **Go :** les éléments nécessaires à la poursuite de l'étape considérée sont suffisamment établis.
- **Go restreint :** l'étude peut continuer, mais certaines incertitudes ou certains risques doivent être résolus avant les étapes suivantes.
- **No-go :** un problème bloquant empêche de poursuivre l'étape concernée dans les conditions actuelles.

Ces décisions sont justifiées par les résultats de l'audit et ne signifient pas qu'un dataset est automatiquement prêt pour la modélisation.

### Principes de rigueur

L'audit repose sur les principes suivants :

- **Traçabilité :** conserver la provenance des données et la justification des décisions.
- **Reproductibilité :** privilégier des contrôles dont les résultats peuvent être vérifiés et reproduits.
- **Prudence :** ne pas supprimer, corriger ou imputer une valeur sans justification.
- **Documentation explicite :** distinguer les faits documentés, les constats observés, les hypothèses et les informations inconnues.
- **Prévention de la fuite de données :** ne pas sélectionner de variables explicatives avant d'avoir compris leur relation avec la cible et leur disponibilité au moment de la prédiction.
- **Séparation des responsabilités :** utiliser l'audit pour évaluer les données, le dictionnaire pour documenter les colonnes et l'étape de préparation pour appliquer les transformations justifiées.

### Synthèse globale

Les quatre datasets sont examinés selon le même cadre méthodologique, mais leurs résultats ne sont pas nécessairement comparables directement. Ils peuvent différer par leur source, leur niveau géographique, leur période, leurs méthodes de collecte et leurs variables disponibles.

Une synthèse globale sera établie après l'examen des quatre fichiers. Elle servira à évaluer leur compatibilité, les éventuelles redondances, les différences de couverture et les conditions nécessaires avant une éventuelle fusion.

**Décision générale :** aucune préparation définitive destinée à la modélisation ne sera engagée tant que les risques importants, les définitions essentielles et les conditions de validation n'auront pas été suffisamment clarifiés.
