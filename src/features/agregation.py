"""Agrégation des séries climatiques par lieu et indicateurs de chaque saison.

Un lieu est une zone de regional, une zone de repli de survey ou le voisinage de 5 km
d'une grappe. Sa série journalière est la moyenne des mailles qui le recoupent,
pondérée par la surface de leur intersection avec le lieu. Une maille sans valeur un
jour donné est ignorée ce jour-là, et les poids des autres mailles sont renormalisés.
L'évapotranspiration de référence est calculée dans chaque maille avant l'agrégation,
car elle dépend des variables de façon non linéaire.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.affinity import scale, translate
from shapely.geometry import Point

from .climat import DOSSIER_MAGASIN, ouvrir_magasin
from .indicateurs import evapotranspiration_reference, indicateurs_saison

RAYON_VOISINAGE_KM = 5.0
KM_PAR_DEGRE_LATITUDE = 110.574
KM_PAR_DEGRE_LONGITUDE_EQUATEUR = 111.320
CORRESPONDANCE_VARIABLES = {
    "tmax": ("power", "T2M_MAX"),
    "tmin": ("power", "T2M_MIN"),
    "tdew": ("power", "T2MDEW"),
    "rayonnement": ("power", "ALLSKY_SFC_SW_DWN"),
    "et0": ("power", "ET0"),
    "pluie": ("imerg", "IMERG_PRECTOT"),
}


def voisinages_grappes(latitudes, longitudes, rayon_km=RAYON_VOISINAGE_KM):
    """Retourne le disque de rayon donné autour de chaque point, exprimé en degrés.

    Le disque devient une ellipse en degrés, dont l'axe est-ouest s'allonge avec la
    latitude, ce qui conserve un rayon de 5 km au sol dans toutes les directions.
    """
    cercle = Point(0, 0).buffer(1, quad_segs=16)
    geometries = [
        translate(scale(cercle, rayon_km / (KM_PAR_DEGRE_LONGITUDE_EQUATEUR * np.cos(np.radians(lat))),
                        rayon_km / KM_PAR_DEGRE_LATITUDE, origin=(0, 0)), lon, lat)
        for lat, lon in zip(latitudes, longitudes)
    ]
    return gpd.GeoSeries(geometries, crs="EPSG:4326")


def moyenne_ponderee(tableau, indices, poids):
    """Retourne la moyenne journalière des lignes indiquées, pondérée et sans valeur manquante."""
    valeurs = np.asarray(tableau[np.sort(indices)], dtype=np.float64)
    poids = np.asarray(poids, dtype=np.float64)[np.argsort(indices)][:, None]
    presents = ~np.isnan(valeurs)
    total = (presents * poids).sum(axis=0)
    somme = np.where(presents, valeurs, 0.0).T @ poids[:, 0]
    return np.where(total > 0, somme / np.where(total > 0, total, 1), np.nan)


def calculer_et0(magasin=DOSSIER_MAGASIN, taille_bloc=200):
    """Calcule l'évapotranspiration de référence de chaque maille et l'ajoute au magasin POWER."""
    mailles, dates, tableaux = ouvrir_magasin("power", magasin)
    resultat = np.lib.format.open_memmap(magasin / "power_ET0.npy", mode="w+", dtype=np.float32,
                                         shape=tableaux["T2M_MAX"].shape)
    jour = dates.dayofyear.to_numpy()[None, :]
    for debut in range(0, len(mailles), taille_bloc):
        bloc = slice(debut, debut + taille_bloc)
        resultat[bloc] = evapotranspiration_reference(
            tableaux["T2M_MAX"][bloc].astype(np.float64), tableaux["T2M_MIN"][bloc].astype(np.float64),
            tableaux["T2MDEW"][bloc].astype(np.float64), tableaux["ALLSKY_SFC_SW_DWN"][bloc].astype(np.float64),
            tableaux["WS2M"][bloc].astype(np.float64), mailles["latitude"].to_numpy()[bloc, None],
            mailles["altitude"].to_numpy()[bloc, None], jour,
        )
    resultat.flush()


def _ouvrir_tout(magasin):
    magasins = {}
    for produit in ["power", "imerg"]:
        mailles, dates, tableaux = ouvrir_magasin(produit, magasin)
        if produit == "power":
            tableaux["ET0"] = np.load(magasin / "power_ET0.npy", mmap_mode="r")
        magasins[produit] = (pd.Series(np.arange(len(mailles)), index=mailles["maille"]), dates, tableaux)
    return magasins


def indicateurs_lieux(poids, fenetres, magasin=DOSSIER_MAGASIN):
    """Calcule les indicateurs climatiques de chaque fenêtre de chaque lieu.

    poids contient lieu, maille et poids, fenetres contient lieu, debut et fin. Les
    séries sont ramenées sur le calendrier de POWER, et les jours sans précipitations
    IMERG, antérieurs à juin 2000, sont manquants. Une fenêtre qui déborde de la
    période couverte reçoit des indicateurs manquants.
    """
    magasins = _ouvrir_tout(magasin)
    dates = magasins["power"][1]
    decalage_imerg = (magasins["imerg"][1][0] - dates[0]).days
    poids_par_lieu = dict(tuple(poids.groupby("lieu", sort=False)))
    resultats = []
    for lieu, groupe in fenetres.groupby("lieu", sort=False):
        mailles_lieu = poids_par_lieu.get(lieu, poids.iloc[:0])
        series = {}
        for nom, (produit, variable) in CORRESPONDANCE_VARIABLES.items():
            index, _, tableaux = magasins[produit]
            presentes = mailles_lieu["maille"].isin(index.index).to_numpy()
            if not presentes.any():
                series[nom] = np.full(len(dates), np.nan)
                continue
            serie = moyenne_ponderee(tableaux[variable], index[mailles_lieu["maille"][presentes]].to_numpy(),
                                     mailles_lieu["poids"].to_numpy()[presentes])
            if produit == "imerg":
                serie = np.concatenate([np.full(decalage_imerg, np.nan), serie])
            series[nom] = serie
        debuts = (pd.DatetimeIndex(groupe["debut"]) - dates[0]).days.to_numpy()
        fins = (pd.DatetimeIndex(groupe["fin"]) - dates[0]).days.to_numpy()
        couvertes = (debuts >= 0) & (fins < len(dates))
        valeurs = indicateurs_saison(series, np.where(couvertes, debuts, 0), np.where(couvertes, fins, 0))
        tableau = pd.DataFrame(valeurs, index=groupe.index)
        tableau.loc[~couvertes] = np.nan
        resultats.append(pd.concat([groupe[["lieu", "debut", "fin"]], tableau], axis=1))
    return pd.concat(resultats).reset_index(drop=True)
