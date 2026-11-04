"""Contrôles des couches de SoilGrids et des variables de sol.

Ces fonctions produisent les constats du notebook 07_soil_variables. Elles ne
modifient aucune donnée. Les comparaisons avec la résolution de 250 m lisent à
distance des fenêtres de quelques centaines de pixels.
"""

import warnings

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.windows import Window

from .sols import CRS_SOILGRIDS, DOSSIER_SOILGRIDS, PROFONDEURS, PROPRIETES, URL_SOILGRIDS, VALEUR_MANQUANTE, chemin_couche


def url_250m(propriete, profondeur):
    """Retourne l'adresse de la mosaïque virtuelle à 250 m d'une propriété."""
    return f"/vsicurl/{URL_SOILGRIDS}data/{propriete}/{propriete}_{profondeur}_mean.vrt"


def _lire(chemin, fenetre=None):
    with rasterio.open(chemin) as raster:
        valeurs = raster.read(1, window=fenetre).astype(np.float64)
        transformation = raster.transform
    valeurs[valeurs == VALEUR_MANQUANTE] = np.nan
    return valeurs, transformation


def fenetre_autour(longitude, latitude, cote, dossier=DOSSIER_SOILGRIDS):
    """Retourne la fenêtre carrée de la grille découpée, de cote pixels, centrée sur un point."""
    x, y = Transformer.from_crs("EPSG:4326", CRS_SOILGRIDS, always_xy=True).transform(longitude, latitude)
    with rasterio.open(chemin_couche("clay", "0-5cm", dossier)) as raster:
        ligne, colonne = raster.index(x, y)
    return Window(colonne - cote // 2, ligne - cote // 2, cote, cote)


def resumer_couches(dossier=DOSSIER_SOILGRIDS):
    """Retourne la part de pixels valides et les quantiles de chaque couche découpée, en unité usuelle."""
    lignes = []
    for propriete, (nom, diviseur, unite) in PROPRIETES.items():
        for profondeur in PROFONDEURS:
            valeurs, _ = _lire(chemin_couche(propriete, profondeur, dossier))
            valides = valeurs[~np.isnan(valeurs)] / diviseur
            quantiles = np.percentile(valides, [0, 1, 50, 99, 100])
            lignes.append({"propriete": nom, "profondeur": profondeur, "unite": unite,
                           "part_valide": len(valides) / valeurs.size, "zeros": int((valides == 0).sum()),
                           **dict(zip(["minimum", "q01", "mediane", "q99", "maximum"], quantiles))})
    return pd.DataFrame(lignes)


def fermeture_texture(dossier=DOSSIER_SOILGRIDS, profondeur="0-5cm"):
    """Retourne les quantiles de la somme des parts d'argile, de limon et de sable en pour cent."""
    somme = sum(_lire(chemin_couche(p, profondeur, dossier))[0] for p in ["clay", "silt", "sand"]) / 10
    return pd.Series(np.nanpercentile(somme, [0, 0.1, 1, 50, 99, 99.9, 100]),
                     index=["minimum", "q0.1", "q01", "mediane", "q99", "q99.9", "maximum"])


def lire_250m(propriete, profondeur, fenetre, transformation, marge=0):
    """Lit à 250 m l'étendue d'une fenêtre de la grille à 1 km, avec une marge en pixels fins."""
    x, y = transformation @ (fenetre.col_off, fenetre.row_off)
    with rasterio.open(url_250m(propriete, profondeur)) as raster:
        colonne = int(round((x - raster.transform.c) / raster.transform.a)) - marge
        ligne = int(round((y - raster.transform.f) / raster.transform.e)) - marge
        valeurs = raster.read(1, window=Window(colonne, ligne, 4 * fenetre.width + 2 * marge,
                                               4 * fenetre.height + 2 * marge)).astype(np.float64)
        origine = raster.transform.c
    valeurs[valeurs == VALEUR_MANQUANTE] = np.nan
    return valeurs, origine


def comparer_apercu(propriete, profondeur, fenetre, dossier=DOSSIER_SOILGRIDS):
    """Compare une fenêtre de la couche découpée au premier aperçu de la mosaïque à 250 m.

    Retourne l'abscisse d'origine de la mosaïque et la part de pixels identiques.
    """
    local, _ = _lire(chemin_couche(propriete, profondeur, dossier), fenetre)
    with rasterio.open(chemin_couche(propriete, profondeur, dossier)) as raster:
        x, y = raster.transform @ (fenetre.col_off, fenetre.row_off)
    with rasterio.open(url_250m(propriete, profondeur)) as raster:
        colonne = int(round((x - raster.transform.c) / raster.transform.a))
        ligne = int(round((y - raster.transform.f) / raster.transform.e))
        apercu = raster.read(1, window=Window(colonne, ligne, 4 * fenetre.width, 4 * fenetre.height),
                             out_shape=(fenetre.height, fenetre.width), resampling=Resampling.nearest)
        origine = raster.transform.c
    apercu = apercu.astype(np.float64)
    apercu[apercu == VALEUR_MANQUANTE] = np.nan
    egaux = (local == apercu) | (np.isnan(local) & np.isnan(apercu))
    return origine, egaux.mean()


def decalage_agregat(propriete, profondeur, fenetre, dossier=DOSSIER_SOILGRIDS, portee=6):
    """Cherche le décalage, en pixels de 250 m, qui rapproche le plus la couche à 1 km des moyennes de blocs.

    Chaque pixel à 1 km est comparé à la moyenne des 4 sur 4 pixels à 250 m de même
    étendue, puis de blocs décalés de dx colonnes vers l'est et de dy lignes vers le
    sud. Retourne l'écart absolu moyen pour chaque décalage.
    """
    with rasterio.open(chemin_couche(propriete, profondeur, dossier)) as raster:
        transformation = raster.transform
    local, _ = _lire(chemin_couche(propriete, profondeur, dossier), fenetre)
    fin, origine = lire_250m(propriete, profondeur, fenetre, transformation, marge=portee)
    lignes = []
    for dy in range(-portee, portee + 1):
        for dx in range(-portee, portee + 1):
            bloc = fin[portee + dy:portee + dy + 4 * fenetre.height, portee + dx:portee + dx + 4 * fenetre.width]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                moyenne = np.nanmean(bloc.reshape(fenetre.height, 4, fenetre.width, 4), axis=(1, 3))
            lignes.append({"dx": dx, "dy": dy, "ecart": np.nanmean(np.abs(moyenne - local))})
    return pd.DataFrame(lignes).assign(origine_250m=origine, ecart_type=np.nanstd(local))


def ecart_echelle(propriete, profondeur, longitude, latitude, dossier=DOSSIER_SOILGRIDS, cote_km=50, echelle_km=5):
    """Compare, sur des carrés de echelle_km de côté, la moyenne de la couche à 1 km à celle des pixels à 250 m.

    Le carré de cote_km centré sur le point est lu aux deux résolutions. Retourne
    l'écart-type des moyennes à 250 m, l'écart absolu moyen et la corrélation.
    """
    chemin = chemin_couche(propriete, profondeur, dossier)
    with rasterio.open(chemin) as raster:
        transformation = raster.transform
    fenetre = fenetre_autour(longitude, latitude, cote_km, dossier)
    local, _ = _lire(chemin, fenetre)
    fin, _ = lire_250m(propriete, profondeur, fenetre, transformation)
    n = cote_km // echelle_km
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        grossier = np.nanmean(local[:n * echelle_km, :n * echelle_km].reshape(n, echelle_km, n, echelle_km), axis=(1, 3))
        exact = np.nanmean(fin[:4 * n * echelle_km, :4 * n * echelle_km].reshape(n, 4 * echelle_km, n, 4 * echelle_km),
                           axis=(1, 3))
    diviseur = PROPRIETES[propriete][1]
    valides = ~np.isnan(grossier) & ~np.isnan(exact)
    return {"ecart_type_5km": np.std(exact[valides]) / diviseur,
            "ecart_moyen_5km": np.mean(np.abs(grossier - exact)[valides]) / diviseur,
            "correlation_5km": np.corrcoef(grossier[valides], exact[valides])[0, 1]}
