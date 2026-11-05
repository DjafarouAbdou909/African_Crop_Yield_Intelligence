"""Intervalles de prédiction des modèles retenus.

Les intervalles suivent la prédiction conforme par catégorie. Pour chaque culture, la
demi-largeur de l'intervalle sur le logarithme est le quantile des erreurs absolues
hors échantillon du développement, corrigé pour garantir la couverture nominale. Les
erreurs de calibration proviennent des trois schémas de validation interne, ce qui
représente la prédiction de lieux nouveaux, d'années futures et des deux. Une culture
qui compte moins de MINIMUM_CALIBRATION erreurs reçoit la demi-largeur de l'ensemble.

L'intervalle d'une prédiction p est compris entre p divisé par exp(q) et p multiplié
par exp(q). Seul le développement sert à le calibrer.
"""

import numpy as np
import pandas as pd

from .experiences import JEUX, SCHEMAS, lire_experience
from .selection import VARIANTES_RETENUES, courbes_retenues

NIVEAUX = [0.8, 0.9]
MINIMUM_CALIBRATION = 200


def quantile_conforme(erreurs, niveau):
    """Retourne le quantile des erreurs qui garantit la couverture nominale d'une prédiction conforme."""
    erreurs = np.sort(np.asarray(erreurs, dtype=float))
    rang = int(np.ceil((len(erreurs) + 1) * niveau)) - 1
    return erreurs[min(rang, len(erreurs) - 1)]


def erreurs_calibration(jeu, developpement):
    """Retourne les erreurs hors échantillon du modèle retenu dans les trois schémas, avec la culture."""
    cible = JEUX[jeu][0]
    culture = "crop" if jeu == "regional" else "Crop"
    palier = int(courbes_retenues(jeu, developpement)["moyenne"].idxmin())
    morceaux = []
    for schema in SCHEMAS:
        prediction = lire_experience(jeu, schema, VARIANTES_RETENUES[jeu])[palier]
        lignes = developpement.loc[prediction.index]
        morceaux.append(pd.DataFrame({
            "schema": schema, "culture": lignes[culture].to_numpy(),
            "erreur": np.abs(np.log(prediction.to_numpy()) - np.log(lignes[cible].to_numpy())),
        }))
    return pd.concat(morceaux, ignore_index=True)


def demi_largeurs(erreurs, niveaux=NIVEAUX, minimum=MINIMUM_CALIBRATION):
    """Retourne la demi-largeur sur le logarithme par culture et pour l'ensemble, à chaque niveau."""
    lignes = {"ensemble": {n: quantile_conforme(erreurs["erreur"], n) for n in niveaux}}
    for culture, groupe in erreurs.groupby("culture"):
        if len(groupe) >= minimum:
            lignes[culture] = {n: quantile_conforme(groupe["erreur"], n) for n in niveaux}
    return pd.DataFrame(lignes).T


def intervalles(prediction, cultures, largeurs, niveau):
    """Retourne les bornes basse et haute des intervalles de prédiction."""
    q = pd.Series(cultures).map(largeurs[niveau]).fillna(largeurs.loc["ensemble", niveau]).to_numpy()
    prediction = np.asarray(prediction, dtype=float)
    return prediction * np.exp(-q), prediction * np.exp(q)


def couverture(evaluation, cultures, largeurs, niveaux=NIVEAUX, cles=("partition",)):
    """Retourne la couverture et la largeur relative médiane des intervalles par modalité des clés."""
    resultat = {}
    for niveau in niveaux:
        bas, haut = intervalles(evaluation["prediction"], cultures, largeurs, niveau)
        dedans = (evaluation["reel"].to_numpy() >= bas) & (evaluation["reel"].to_numpy() <= haut)
        tableau = pd.DataFrame({"dedans": dedans, "rapport": haut / bas}, index=evaluation.index).join(
            evaluation[list(cles)])
        groupes = tableau.groupby(list(cles))
        resultat[f"couverture_{niveau:.0%}"] = groupes["dedans"].mean()
        resultat[f"rapport_haut_bas_median_{niveau:.0%}"] = groupes["rapport"].median()
    resultat["lignes"] = evaluation.groupby(list(cles)).size()
    return pd.DataFrame(resultat)
