# Estimation en fin de saison et prévision anticipée

| Élément | Valeur |
|---|---|
| Projet | African Crop Yield Intelligence |
| Nature | Clarification du périmètre des modèles |
| Origine | Cinquième suggestion de la revue du projet par une mentore experte |
| Documents associés | `docs/explanatory_variables.md`, section 3, `docs/modeling.md` et `docs/deployment.md` |

## 1. Objet

La revue du projet a invité à bien distinguer l'estimation des rendements en fin de saison de la prévision anticipée, car leurs exigences méthodologiques et leurs applications diffèrent. Le projet a choisi l'estimation en fin de saison dès la construction des variables, selon la section 3 de `docs/explanatory_variables.md`. Plusieurs documents parlent pourtant de prédire des années futures, ce qui peut laisser croire à une prévision. Ce document fixe le vocabulaire, décrit ce que chaque modèle permet réellement et énonce ce qu'exigerait une prévision.

## 2. Définitions

| | Estimation en fin de saison | Prévision anticipée |
|---|---|---|
| Moment de la prédiction | À la récolte ou après | Avant le semis ou en cours de saison, à une date fixée |
| Information admissible | Toutes les conditions observées jusqu'à la récolte | Les seules conditions observées jusqu'à la date de prévision, complétées par la climatologie ou une prévision saisonnière |
| Question posée | Quel a été le rendement de cette saison | Quel sera le rendement de cette saison |
| Évaluation | Erreur sur des lieux ou des années non vus, avec le climat observé de leur saison | Erreur selon l'horizon, chaque prédiction n'utilisant que l'information disponible à sa date d'émission |
| Applications | Compléter ou contrôler des statistiques, comparer des régions, recherche sur les déterminants du rendement | Alerte précoce, planification de la sécurité alimentaire, décisions d'achat, de stockage ou d'aide |

## 3. Constat sur les modèles du projet

**Disponibilité des variables**

| Famille de variables | `regional` | `survey` | Connue avant le semis | Connue seulement à la récolte |
|---|---|---|---|---|
| Culture, saison, pays, source, niveau, système de production | Oui | Culture et pays | Oui | |
| Année de récolte | Oui | Oui | Oui | |
| Position et surface de la zone | Oui | Position | Oui | |
| Calendrier cultural | Oui | Oui | Oui, calendrier habituel du lieu | |
| Sols, altitude et pente | Oui | Oui | Oui | |
| Douze indicateurs climatiques, cumulés du semis à la récolte | Oui | Non | | Oui |

**Constat**

- Le modèle retenu pour `regional` utilise les douze indicateurs climatiques de la saison entière. Il n'est donc utilisable qu'à la fin de la saison, et constitue une estimation en fin de saison.
- Le modèle retenu pour `survey` n'utilise aucune variable climatique. Toutes ses variables sont connues avant le semis. Il prédit le rendement déclaré habituel d'un lieu, d'une culture et d'une année, sans rien savoir de la saison en cours.
- Les ensembles de test temporels, la validation temporelle interne et les fenêtres successives évaluent des années absentes de l'entraînement, mais avec le climat observé de ces années. Ils mesurent la robustesse au passage du temps, et non la capacité à anticiper une saison.
- Les données climatiques du projet sont des produits de recherche. IMERG Final, recommandé par la NASA pour la recherche, paraît environ 3,5 mois après le mois observé. Les données météorologiques de NASA POWER sont prolongées en temps quasi réel avec environ deux jours de retard, et leur partie MERRA-2 est mise à jour plusieurs mois plus tard.

**Analyse**

- Dans ce projet, une année future désigne une année postérieure aux années d'entraînement, estimée avec le climat observé de sa saison. Les scores des tests temporels sont donc des scores d'estimation, et ne peuvent pas être lus comme des scores de prévision.
- L'absence de climat ne fait pas du modèle de `survey` un modèle de prévision. Il ne peut pas annoncer une mauvaise saison, puisqu'il donne la même prédiction quelle que soit la pluie de l'année. Son erreur mesure l'écart à un rendement habituel, et non la qualité d'une anticipation.
- Même en fin de saison, une estimation qui repose sur IMERG Final n'est disponible qu'environ quatre mois après la récolte. Un usage plus rapide exigerait les versions Early ou Late d'IMERG, dont la qualité diffère et qui n'ont pas été évaluées ici.
- Les études précédentes ont montré que le climat n'améliore pas significativement la prédiction des années non vues, selon `docs/research_rolling_windows_results.md` et `docs/research_climate_zones_results.md`. Le gain d'une information sur la saison en cours, qui fait la valeur d'une prévision, n'est donc pas établi dans ce projet.

## 4. Décisions

1. Les modèles du projet sont des modèles d'estimation en fin de saison. Ils ne doivent être ni présentés ni utilisés comme des modèles de prévision ou d'alerte précoce.
2. Dans les documents à venir, l'expression année non vue à l'entraînement remplace année future lorsqu'il s'agit d'évaluation. Les documents déjà publiés ne sont pas réécrits. Ce document en fixe la lecture, et le README, `docs/deployment.md` et l'application y renvoient.
3. Le modèle de `survey` est décrit comme une estimation du rendement déclaré habituel d'un lieu, sans information sur la saison.

## 5. Exigences d'un scénario de prévision

Une prévision anticipée ne se déduit pas des modèles actuels en retirant des variables. Elle exige un protocole propre.

- **Date d'émission.** Chaque prévision est émise à une date fixée par rapport au semis, par exemple au semis, à mi-saison ou un mois avant la récolte. Les variables climatiques sont tronquées à cette date.
- **Reste de la saison.** La partie de la saison non encore observée est représentée par la climatologie du lieu ou par une prévision saisonnière, jamais par les observations réelles.
- **Données disponibles à la date d'émission.** Une évaluation honnête n'utilise que les produits qui auraient existé à cette date, avec leur latence, par exemple IMERG Early ou Late plutôt que Final.
- **Évaluation par horizon.** L'erreur et la couverture des intervalles sont rapportées pour chaque date d'émission. On attend une erreur qui diminue à mesure que la récolte approche, et l'écart à l'estimation en fin de saison mesure le prix de l'anticipation.
- **Référence adaptée.** La référence d'une prévision est le rendement habituel du lieu, que le modèle de `survey` fournit déjà. Une prévision n'a de valeur que si elle bat cette référence.
- **Calendrier.** La date de semis réelle n'est connue qu'au semis. Avant, seul le calendrier habituel du lieu peut servir.

## 6. Conséquences pour la suite

- Le scénario de prévision, prévu dès la section 3 de `docs/explanatory_variables.md`, peut être évalué par une étude préenregistrée. Elle comparerait, sur les fenêtres successives de `docs/research_rolling_windows.md`, l'estimation en fin de saison à des prévisions émises au semis et à mi-saison, la saison restante étant remplacée par la climatologie. Vu la faiblesse de l'apport du climat, l'hypothèse attendue est un écart faible entre ces horizons.
- Les intervalles conformes ont été calibrés pour l'estimation en fin de saison. Ils devraient être recalibrés pour chaque horizon de prévision.

## 7. Limites

- La disponibilité des variables est décrite pour un usage futur. La date réelle de mise à disposition de chaque produit doit être vérifiée au moment d'un usage opérationnel.
- La version d'IMERG distribuée par NASA POWER et sa latence n'ont pas été vérifiées. Les délais cités sont ceux de la NASA pour IMERG Final et pour POWER.

## 8. Sources

- NASA GPM. What determines the latency of IMERG. https://gpm.nasa.gov/resources/faq/what-determines-latency-imerg
- NASA GPM. IMERG V07 technical documentation. https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation
- NASA POWER. Data sources. https://power.larc.nasa.gov/docs/methodology/data/sources/
