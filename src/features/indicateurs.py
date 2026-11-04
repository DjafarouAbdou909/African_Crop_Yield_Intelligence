"""Indicateurs climatiques d'une saison à partir des séries journalières d'un lieu.

L'évapotranspiration de référence suit l'équation de Penman-Monteith du bulletin
FAO-56, avec un flux de chaleur dans le sol nul au pas journalier. Un indicateur est
manquant dès qu'un jour de la fenêtre manque pour l'une des variables qu'il utilise.
"""

import numpy as np

SEUIL_JOUR_PLUIE = 1.0
BASE_DEGRES_JOURS = 10.0
PLAFOND_DEGRES_JOURS = 30.0
SEUILS_CHALEUR = [30.0, 35.0]
ALBEDO = 0.23
CONSTANTE_SOLAIRE = 0.0820
STEFAN_BOLTZMANN = 4.903e-9


def pression_saturante(temperature):
    """Retourne la pression de vapeur saturante en kilopascals, équation 11 de FAO-56."""
    return 0.6108 * np.exp(17.27 * temperature / (temperature + 237.3))


def rayonnement_extraterrestre(latitude, jour):
    """Retourne le rayonnement extraterrestre journalier en MJ par m², équation 21 de FAO-56."""
    phi = np.radians(latitude)
    dr = 1 + 0.033 * np.cos(2 * np.pi * jour / 365)
    declinaison = 0.409 * np.sin(2 * np.pi * jour / 365 - 1.39)
    omega = np.arccos(np.clip(-np.tan(phi) * np.tan(declinaison), -1, 1))
    return 24 * 60 / np.pi * CONSTANTE_SOLAIRE * dr * (
        omega * np.sin(phi) * np.sin(declinaison) + np.cos(phi) * np.cos(declinaison) * np.sin(omega)
    )


def evapotranspiration_reference(tmax, tmin, tdew, rayonnement, vent, latitude, altitude, jour):
    """Retourne l'évapotranspiration de référence journalière en millimètres, équation 6 de FAO-56.

    Les températures sont en degrés Celsius, le rayonnement incident en MJ par m² et par
    jour, le vent à 2 m en mètres par seconde et l'altitude en mètres.
    """
    tmoy = (tmax + tmin) / 2
    pente = 4098 * pression_saturante(tmoy) / (tmoy + 237.3) ** 2
    pression = 101.3 * ((293 - 0.0065 * altitude) / 293) ** 5.26
    gamma = 0.000665 * pression
    es = (pression_saturante(tmax) + pression_saturante(tmin)) / 2
    ea = pression_saturante(tdew)
    ra = rayonnement_extraterrestre(latitude, jour)
    rso = (0.75 + 2e-5 * altitude) * ra
    rapport = np.clip(rayonnement / np.where(rso > 0, rso, np.nan), 0, 1)
    rnl = STEFAN_BOLTZMANN * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (
        0.34 - 0.14 * np.sqrt(ea)
    ) * (1.35 * rapport - 0.35)
    rn = (1 - ALBEDO) * rayonnement - rnl
    return (0.408 * pente * rn + gamma * 900 / (tmoy + 273) * vent * (es - ea)) / (pente + gamma * (1 + 0.34 * vent))


def _somme_fenetres(valeurs, debuts, fins):
    """Retourne la somme de valeurs sur chaque fenêtre de jours, manquante si un jour manque."""
    cumul = np.concatenate([[0.0], np.cumsum(np.nan_to_num(valeurs, nan=0.0))])
    manquants = np.concatenate([[0], np.cumsum(np.isnan(valeurs))])
    somme = cumul[fins + 1] - cumul[debuts]
    return np.where(manquants[fins + 1] - manquants[debuts] > 0, np.nan, somme)


def sequence_seche_maximale(pluie, debuts, fins, seuil=SEUIL_JOUR_PLUIE):
    """Retourne la plus longue suite de jours sans pluie de chaque fenêtre."""
    sec = np.nan_to_num(pluie, nan=np.inf) < seuil
    rang = np.arange(len(pluie))
    duree = rang - np.maximum.accumulate(np.where(sec, -1, rang))
    resultat = np.empty(len(debuts))
    for rang, (debut, fin) in enumerate(zip(debuts, fins)):
        resultat[rang] = np.minimum(duree[debut:fin + 1], np.arange(1, fin - debut + 2)).max()
    return resultat


def indicateurs_saison(series, debuts, fins):
    """Calcule les indicateurs de chaque fenêtre à partir des séries journalières d'un lieu.

    series associe à chaque variable un tableau journalier, et debuts et fins donnent
    les positions incluses des fenêtres dans ces tableaux. Les variables attendues sont
    pluie, tmax, tmin, tdew, rayonnement et et0.
    """
    debuts, fins = np.asarray(debuts), np.asarray(fins)
    jours = fins - debuts + 1
    tmoy = (series["tmax"] + series["tmin"]) / 2
    pluie = series["pluie"]
    resultat = {
        "pluie_cumul": _somme_fenetres(pluie, debuts, fins),
        "pluie_jours": _somme_fenetres(np.where(np.isnan(pluie), np.nan, pluie >= SEUIL_JOUR_PLUIE), debuts, fins),
        "degres_jours": _somme_fenetres(np.clip(np.minimum(tmoy, PLAFOND_DEGRES_JOURS) - BASE_DEGRES_JOURS, 0, None),
                                        debuts, fins),
        "tmax_moyenne": _somme_fenetres(series["tmax"], debuts, fins) / jours,
        "tmin_moyenne": _somme_fenetres(series["tmin"], debuts, fins) / jours,
        "dpv_moyen": _somme_fenetres(
            (pression_saturante(series["tmax"]) + pression_saturante(series["tmin"])) / 2
            - pression_saturante(series["tdew"]), debuts, fins) / jours,
        "rayonnement_moyen": _somme_fenetres(series["rayonnement"], debuts, fins) / jours,
        "et0_cumul": _somme_fenetres(series["et0"], debuts, fins),
    }
    for seuil in SEUILS_CHALEUR:
        resultat[f"degres_jours_{seuil:.0f}"] = _somme_fenetres(np.clip(series["tmax"] - seuil, 0, None), debuts, fins)
    sequence = sequence_seche_maximale(pluie, debuts, fins)
    resultat["sequence_seche_max"] = np.where(np.isnan(resultat["pluie_cumul"]), np.nan, sequence)
    resultat["bilan_hydrique"] = resultat["pluie_cumul"] - resultat["et0_cumul"]
    return resultat
