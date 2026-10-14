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