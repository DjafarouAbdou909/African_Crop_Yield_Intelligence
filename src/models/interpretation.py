"""Interprétation des modèles retenus par les contributions de Shapley.

LightGBM calcule pour chaque prédiction la contribution exacte de chaque variable,
au sens des valeurs de Shapley des arbres, sur l'échelle du logarithme du rendement.
La somme des contributions et de la valeur de base donne la prédiction. Une
contribution de 0,1 multiplie donc le rendement prédit par exp(0,1), soit environ
1,105.
"""

import numpy as np
import pandas as pd

from .apprentissage import matrice

FAMILLES = {
    "climat": ["pluie_cumul", "pluie_jours", "sequence_seche_max", "bilan_hydrique", "et0_cumul", "degres_jours",
               "degres_jours_30", "degres_jours_35", "tmax_moyenne", "tmin_moyenne", "dpv_moyen", "rayonnement_moyen"],
    "sols": ["argile_0_30", "limon_0_30", "sable_0_30", "carbone_organique_0_30", "azote_0_30", "ph_0_30", "cec_0_30",
             "densite_apparente_0_30", "elements_grossiers_0_30"],
    "relief": ["altitude_moyenne", "pente_moyenne"],
    "calendrier": ["mois_semis", "mois_recolte", "duree_saison"],
    "annee": ["harvest_year", "annee_recolte"],
    "position": ["latitude", "longitude", "log_surface_zone"],
    "culture": ["crop", "Crop", "saison", "crop_production_system"],
    "pays": ["country", "Country"],
    "source": ["Source", "level"],
}


def contributions(modele, description, table):
    """Retourne la contribution de chaque variable à chaque prédiction, et la valeur de base."""
    x, _ = matrice(table, description["categorielles"], description["numeriques"], description["categories"])
    valeurs = modele.predict(x, pred_contrib=True)
    colonnes = list(x.columns)
    return pd.DataFrame(valeurs[:, :-1], index=table.index, columns=colonnes), pd.Series(valeurs[:, -1], index=table.index)


def importance_shapley(contribs):
    """Retourne la moyenne des contributions absolues par variable et par famille."""
    variables = contribs.abs().mean().sort_values(ascending=False)
    familles = {nom: variables.reindex(membres).dropna().sum() for nom, membres in FAMILLES.items()}
    return variables, pd.Series(familles).loc[lambda s: s > 0].sort_values(ascending=False)


def dependance(contribs, table, variable, quantiles=10):
    """Retourne la contribution médiane d'une variable par classe de quantile de sa valeur."""
    valeurs = pd.to_numeric(table[variable], errors="coerce")
    classes = pd.qcut(valeurs, quantiles, duplicates="drop")
    return pd.DataFrame({"valeur": valeurs, "contribution": contribs[variable]}).groupby(classes, observed=True).agg(
        valeur_mediane=("valeur", "median"), contribution_mediane=("contribution", "median"),
        lignes=("valeur", "size"))
