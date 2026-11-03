"""Métriques d'évaluation des prédictions de rendement.

La métrique principale est l'erreur absolue moyenne sur le logarithme népérien du
rendement. Elle mesure une erreur relative, comparable d'une culture à l'autre
malgré des ordres de grandeur très différents. Les métriques en tonnes par hectare
restent calculées pour l'interprétation.
"""

import numpy as np
import pandas as pd


def metriques(reel, predit):
    """Calcule les métriques d'une prédiction sur des rendements strictement positifs.

    Le biais est la moyenne de la prédiction moins la valeur réelle. L'erreur relative
    typique est l'exponentielle de l'erreur logarithmique diminuée de un.
    """
    reel = np.asarray(reel, dtype=float)
    predit = np.asarray(predit, dtype=float)
    erreur = predit - reel
    erreur_log = np.log(predit) - np.log(reel)
    dispersion = np.sum((reel - reel.mean()) ** 2)
    mae_log = float(np.mean(np.abs(erreur_log)))
    return {
        "n": int(reel.size),
        "mae_log": mae_log,
        "erreur_relative_typique": float(np.expm1(mae_log)),
        "mae": float(np.mean(np.abs(erreur))),
        "rmse": float(np.sqrt(np.mean(erreur ** 2))),
        "biais": float(np.mean(erreur)),
        "biais_log": float(np.mean(erreur_log)),
        "r2": float(1 - np.sum(erreur ** 2) / dispersion) if dispersion > 0 else np.nan,
    }


def metriques_par(df, cles, reel, predit):
    """Calcule les métriques pour chaque modalité des clés indiquées."""
    lignes = {
        modalite: metriques(groupe[reel], groupe[predit])
        for modalite, groupe in df.groupby(cles, dropna=False)
    }
    resultat = pd.DataFrame.from_dict(lignes, orient="index")
    resultat.index.names = cles if isinstance(cles, list) else [cles]
    return resultat


def moyenne_macro(table, colonne="mae_log"):
    """Moyenne non pondérée d'une métrique sur les modalités d'une ventilation.

    Elle donne le même poids à chaque pays ou à chaque culture, quel que soit son
    nombre de lignes.
    """
    return float(table[colonne].mean())


def score_competence(erreur_modele, erreur_reference):
    """Part de l'erreur de la référence supprimée par le modèle.

    Une valeur positive indique que le modèle fait mieux que la référence, une valeur
    nulle qu'il fait aussi bien et une valeur négative qu'il fait moins bien.
    """
    return 1 - erreur_modele / erreur_reference
