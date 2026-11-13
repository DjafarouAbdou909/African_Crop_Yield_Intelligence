"""Apport du climat par culture et par zone agroclimatique.

Ce module met en œuvre le plan préenregistré de docs/research_climate_zones.md. Il
calcule l'indice d'aridité de chaque zone de regional, rapport entre la pluie annuelle
moyenne et l'évapotranspiration de référence annuelle moyenne sur 2001 à 2016, puis
ventile l'apport du climat mesuré sur les fenêtres successives par classe d'aridité et
par culture. Aucun modèle n'est entraîné.
"""

import numpy as np
import pandas as pd

from src.features.climat import DOSSIER_MAGASIN, ouvrir_magasin

from .fenetres_temporelles import CIBLE, fenetre_de

DEBUT, FIN = "2001-01-01", "2016-12-31"
ANNEES = 16
BORNES_ARIDITE = [0.0, 0.05, 0.20, 0.50, 0.65, np.inf]
CLASSES_ARIDITE = ["hyperaride", "aride", "semi_aride", "subhumide_seche", "humide"]
MINIMUM_LIGNES = 1000
NOMBRE_CULTURES = 7


def _cumul_annuel_mailles(tableau, dates, taille_bloc=500):
    """Retourne, pour chaque maille, le cumul annuel moyen sur la période, manquant si un jour manque."""
    debut, fin = dates.get_loc(pd.Timestamp(DEBUT)), dates.get_loc(pd.Timestamp(FIN)) + 1
    resultat = np.empty(tableau.shape[0])
    for i in range(0, tableau.shape[0], taille_bloc):
        bloc = np.asarray(tableau[i:i + taille_bloc, debut:fin], dtype=np.float64)
        resultat[i:i + taille_bloc] = np.where(np.isnan(bloc).any(axis=1), np.nan, bloc.sum(axis=1) / ANNEES)
    return resultat


def climat_annuel_mailles(magasin=DOSSIER_MAGASIN):
    """Retourne la pluie IMERG et l'évapotranspiration de référence annuelles moyennes de chaque maille."""
    mailles_imerg, dates_imerg, tableaux_imerg = ouvrir_magasin("imerg", magasin)
    mailles_power, dates_power, _ = ouvrir_magasin("power", magasin)
    et0 = np.load(magasin / "power_ET0.npy", mmap_mode="r")
    pluie = pd.Series(_cumul_annuel_mailles(tableaux_imerg["IMERG_PRECTOT"], dates_imerg), index=mailles_imerg["maille"])
    evapo = pd.Series(_cumul_annuel_mailles(et0, dates_power), index=mailles_power["maille"])
    return pd.DataFrame({"pluie_annuelle": pluie, "et0_annuelle": evapo})


def indice_aridite_zones(poids, climat_mailles):
    """Retourne l'indice d'aridité de chaque lieu, à partir des poids de ses mailles.

    Les moyennes pondérées de la pluie et de l'évapotranspiration ne retiennent que les
    mailles où la variable est connue, et leurs poids sont renormalisés.
    """
    table = poids.join(climat_mailles, on="maille")
    resultat = {}
    for variable in ["pluie_annuelle", "et0_annuelle"]:
        connues = table[variable].notna()
        ponderee = (table[variable] * table["poids"]).where(connues).groupby(table["lieu"]).sum()
        resultat[variable] = ponderee / table["poids"].where(connues).groupby(table["lieu"]).sum()
    resultat = pd.DataFrame(resultat)
    resultat["indice_aridite"] = resultat["pluie_annuelle"] / resultat["et0_annuelle"]
    resultat["classe_aridite"] = classe_aridite(resultat["indice_aridite"])
    return resultat


def classe_aridite(indice):
    """Classe un indice d'aridité selon les seuils du Programme des Nations unies pour l'environnement."""
    return pd.cut(indice, BORNES_ARIDITE, right=False, labels=CLASSES_ARIDITE).astype("string")


def apport_par_strate(predictions, strate, minimum=MINIMUM_LIGNES):
    """Retourne, par modalité d'une strate, l'apport du climat et la compétence, avec intervalles bootstrap.

    predictions contient les colonnes complet, sans_climat et reference, la cible et le
    groupe du protocole, restreintes aux lignes des fenêtres.
    """
    from src.models.bilan import intervalle_bootstrap

    log_reel = np.log(predictions[CIBLE])
    erreur = {c: np.abs(np.log(predictions[c]) - log_reel) for c in ["complet", "sans_climat", "reference"]}
    lignes = []
    for modalite, masque in predictions.groupby(strate).groups.items():
        if len(masque) < minimum:
            continue
        apport = (erreur["sans_climat"] - erreur["complet"]).loc[masque]
        bas, haut = intervalle_bootstrap(apport, predictions.loc[masque, "groupe"])
        lignes.append({
            "strate": modalite, "lignes": len(masque), "pays": predictions.loc[masque, "country"].nunique(),
            "mae_log": erreur["complet"].loc[masque].mean(),
            "competence": 1 - erreur["complet"].loc[masque].mean() / erreur["reference"].loc[masque].mean(),
            "apport_climat": apport.mean(), "apport_bas": bas, "apport_haut": haut,
        })
    return pd.DataFrame(lignes).set_index("strate")


def predictions_avec_strates(developpement, predictions_fenetres, aridite):
    """Ajoute aux prédictions des fenêtres la culture, la zone et la classe d'aridité de chaque ligne."""
    lignes = predictions_fenetres[fenetre_de(predictions_fenetres).notna().to_numpy()]
    lignes = lignes.join(developpement[["GDAM_ID", "crop"]], how="left")
    lignes["classe_aridite"] = lignes["GDAM_ID"].map(aridite["classe_aridite"])
    return lignes


def cultures_principales(lignes, nombre=NOMBRE_CULTURES):
    """Retourne les cultures qui comptent le plus de lignes évaluées."""
    return list(lignes["crop"].value_counts().index[:nombre])
