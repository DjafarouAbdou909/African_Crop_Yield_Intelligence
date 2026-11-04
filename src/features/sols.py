"""Variables de sol tirées de SoilGrids 2.0 à 1 km.

SoilGrids 2.0 publie ses propriétés à 250 m et une version agrégée à 1 km, dans la
projection homolosine de Goode, qui conserve les surfaces. Le pH manque dans la
version à 1 km. Il est lu dans le premier aperçu de sa couche à 250 m, qui est un
fichier publié avec son empreinte et qui coïncide pixel à pixel avec la version à
1 km pour les autres propriétés.

Chaque fichier source est téléchargé en entier, car son empreinte SHA-256 publiée
ne peut être vérifiée que sur le fichier complet. Il est ensuite découpé sur une
fenêtre fixe couvrant tous les lieux du projet, et seul le découpage est conservé.

Les propriétés sont moyennées de 0 à 30 cm, chaque profondeur étant pondérée par son
épaisseur. La valeur d'un lieu est la moyenne de ses pixels, dont la surface est
identique dans cette projection. Les lieux sont ceux des variables climatiques.

Exécution depuis la racine du projet avec les commandes python -m src.features.sols
extraire, puis python -m src.features.sols construire.
"""

import csv
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from affine import Affine
from rasterio.errors import NotGeoreferencedWarning
from rasterio.features import geometry_mask
from rasterio.windows import Window
from rasterio.windows import transform as transformation_fenetre

from src.data.load import DOSSIER_TRAITE, empreinte_sha256

from .acquisition import DOSSIER_EXTERNE, REGISTRE, _poursuivre, consigner
from .lieux import geometries_lieux_survey, lieu_survey

URL_SOILGRIDS = "https://files.isric.org/soilgrids/latest/"
# Nom SoilGrids, puis nom de la variable, diviseur vers l'unité usuelle et unité usuelle.
PROPRIETES = {
    "clay": ("argile", 10, "%"),
    "silt": ("limon", 10, "%"),
    "sand": ("sable", 10, "%"),
    "soc": ("carbone_organique", 10, "g/kg"),
    "nitrogen": ("azote", 100, "g/kg"),
    "phh2o": ("ph", 10, "pH dans l'eau"),
    "cec": ("cec", 10, "cmolc/kg"),
    "bdod": ("densite_apparente", 100, "g/cm3"),
    "cfvo": ("elements_grossiers", 10, "% du volume"),
}
# Profondeur et épaisseur en centimètres.
PROFONDEURS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
VALEUR_MANQUANTE = -32768
CRS_SOILGRIDS = "ESRI:54052"
TRANSFORMATION_1KM = Affine(1000.0, 0.0, -19949750.0, 0.0, -1000.0, 8361000.0)
FORME_1KM = (14509, 39812)
# Fenêtre de la grille à 1 km couvrant tous les lieux avec une marge d'au moins 20
# pixels, soit de -1 800 à 5 530 km en abscisse et de -3 899 à 4 211 km en ordonnée.
FENETRE_AFRIQUE = Window(col_off=18150, row_off=4150, width=7330, height=8110)
DOSSIER_SOILGRIDS = DOSSIER_EXTERNE / "soilgrids"
COLONNES_SOURCES = ["fichier", "url", "octets_source", "sha256_source", "derniere_modification"]


def url_source(propriete, profondeur):
    """Retourne l'adresse du fichier source d'une propriété à une profondeur."""
    if propriete == "phh2o":
        return f"{URL_SOILGRIDS}data/phh2o/phh2o_{profondeur}_mean.vrt.ovr"
    return f"{URL_SOILGRIDS}data_aggregated/1000m/{propriete}/{propriete}_{profondeur}_mean_1000.tif"


def chemin_couche(propriete, profondeur, dossier=DOSSIER_SOILGRIDS):
    """Retourne le chemin du découpage local d'une propriété à une profondeur."""
    return dossier / f"{propriete}_{profondeur}_mean_1000_afrique.tif"


def empreintes_publiees(url):
    """Retourne les empreintes SHA-256 publiées dans le dossier d'un fichier source."""
    reponse = requests.get(url.rsplit("/", 1)[0] + "/checksum.sha256.txt", timeout=60)
    reponse.raise_for_status()
    return {nom: empreinte for empreinte, nom in (ligne.split() for ligne in reponse.text.splitlines() if ligne.strip())}


def decouper(source, chemin, fenetre=FENETRE_AFRIQUE, forme=FORME_1KM, transformation=TRANSFORMATION_1KM):
    """Écrit la fenêtre d'un fichier source à 1 km dans un fichier GeoTIFF compressé.

    Le premier aperçu d'une couche à 250 m n'est pas géoréférencé. Sa forme suffit
    alors à le placer sur la grille à 1 km.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(source) as raster:
            if raster.shape != forme:
                raise ValueError(f"Forme inattendue {raster.shape} pour {source}")
            if raster.crs is not None and not raster.transform.almost_equals(transformation):
                raise ValueError(f"Grille inattendue pour {source}")
            valeurs = raster.read(1, window=fenetre)
    profil = {
        "driver": "GTiff", "height": fenetre.height, "width": fenetre.width, "count": 1, "dtype": "int16",
        "crs": CRS_SOILGRIDS, "transform": transformation_fenetre(fenetre, transformation),
        "nodata": VALEUR_MANQUANTE, "compress": "deflate", "predictor": 2, "tiled": True,
        "blockxsize": 512, "blockysize": 512,
    }
    with rasterio.open(chemin, "w", **profil) as destination:
        destination.write(valeurs, 1)


def _extraire(propriete, profondeur, dossier, tentatives):
    """Télécharge, vérifie et découpe un fichier source, puis le supprime."""
    url = url_source(propriete, profondeur)
    nom = url.rsplit("/", 1)[1]
    publiee = empreintes_publiees(url)[nom]
    source = dossier / "sources" / nom
    source.parent.mkdir(parents=True, exist_ok=True)
    partiel = source.with_name(nom + ".partiel")
    for essai in range(tentatives):
        try:
            if _poursuivre(url, partiel):
                break
        except requests.RequestException:
            time.sleep(10 * (essai + 1))
    else:
        raise RuntimeError(f"Téléchargement incomplet après {tentatives} tentatives pour {url}")
    empreinte = empreinte_sha256(partiel)
    if empreinte != publiee:
        partiel.unlink()
        raise ValueError(f"Empreinte SHA-256 inattendue pour {nom}, fichier supprimé")
    partiel.rename(source)
    chemin = chemin_couche(propriete, profondeur, dossier)
    provisoire = chemin.with_name(chemin.name + ".partiel")
    decouper(source, provisoire)
    provisoire.rename(chemin)
    modification = requests.head(url, timeout=60).headers.get("Last-Modified")
    ligne = [chemin.name, url, source.stat().st_size, empreinte, modification]
    source.unlink()
    return chemin, url, ligne


def extraire_couches(dossier=DOSSIER_SOILGRIDS, registre=REGISTRE, paralleles=6, tentatives=8):
    """Obtient le découpage de chaque propriété à chaque profondeur, en sautant ceux présents.

    Le serveur limite le débit de chaque connexion, et plusieurs téléchargements
    simultanés en multiplient le débit total. Chaque découpage est consigné dans le
    registre des données externes, et l'empreinte vérifiée de sa source dans
    sources.csv.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    taches = [(p, d) for p in PROPRIETES for d in PROFONDEURS if not chemin_couche(p, d, dossier).exists()]
    sources = dossier / "sources.csv"
    with ThreadPoolExecutor(paralleles) as executeur:
        futurs = [executeur.submit(_extraire, p, d, dossier, tentatives) for p, d in taches]
        for futur in as_completed(futurs):
            chemin, url, ligne = futur.result()
            consigner(chemin, url, registre)
            nouveau = not sources.exists()
            with open(sources, "a", newline="", encoding="utf-8") as fichier:
                ecrivain = csv.writer(fichier)
                if nouveau:
                    ecrivain.writerow(COLONNES_SOURCES)
                ecrivain.writerow(ligne)
            print(f"{chemin.name} obtenu", flush=True)


def couche_0_30(propriete, dossier=DOSSIER_SOILGRIDS):
    """Retourne la moyenne de 0 à 30 cm d'une propriété en unité usuelle, pondérée par l'épaisseur.

    Un pixel est manquant dès qu'une profondeur y manque.
    """
    total, manquant = None, None
    for profondeur, epaisseur in PROFONDEURS.items():
        with rasterio.open(chemin_couche(propriete, profondeur, dossier)) as raster:
            brut = raster.read(1)
        if total is None:
            total, manquant = np.zeros(brut.shape, np.float32), np.zeros(brut.shape, bool)
        manquant |= brut == VALEUR_MANQUANTE
        valeurs = brut.astype(np.float32)
        del brut
        valeurs *= epaisseur
        total += valeurs
        del valeurs
    total /= sum(PROFONDEURS.values()) * PROPRIETES[propriete][1]
    total[manquant] = np.nan
    return total


def pixels_lieux(lieux, transformation, forme, colonne="zone"):
    """Retourne les positions à plat des pixels de chaque lieu dans une grille.

    Un pixel appartient à un lieu lorsque son centre tombe dans le contour. Un lieu
    dont aucun centre ne tombe dans le contour reçoit les pixels qu'il touche.
    """
    projetes = lieux.to_crs(CRS_SOILGRIDS)
    resultat = {}
    for nom, geometrie in zip(projetes[colonne], projetes.geometry):
        if geometrie is None or geometrie.is_empty:
            resultat[nom] = np.empty(0, dtype=np.int64)
            continue
        xmin, ymin, xmax, ymax = geometrie.bounds
        c0 = max(int(np.floor((xmin - transformation.c) / transformation.a)), 0)
        c1 = min(int(np.ceil((xmax - transformation.c) / transformation.a)), forme[1])
        r0 = max(int(np.floor((ymax - transformation.f) / transformation.e)), 0)
        r1 = min(int(np.ceil((ymin - transformation.f) / transformation.e)), forme[0])
        if c1 <= c0 or r1 <= r0:
            resultat[nom] = np.empty(0, dtype=np.int64)
            continue
        locale = transformation @ Affine.translation(c0, r0)
        masque = geometry_mask([geometrie], out_shape=(r1 - r0, c1 - c0), transform=locale, invert=True)
        if not masque.any():
            masque = geometry_mask([geometrie], out_shape=(r1 - r0, c1 - c0), transform=locale, invert=True,
                                   all_touched=True)
        lignes, colonnes = np.nonzero(masque)
        resultat[nom] = (lignes + r0).astype(np.int64) * forme[1] + colonnes + c0
    return resultat


def moyennes_lieux(pixels, couche):
    """Retourne la moyenne des pixels valides de chaque lieu et la part de pixels valides."""
    plat = couche.ravel()
    moyennes, parts = {}, {}
    for nom, positions in pixels.items():
        valeurs = plat[positions]
        valides = ~np.isnan(valeurs)
        moyennes[nom] = valeurs[valides].mean() if valides.any() else np.nan
        parts[nom] = valides.mean() if len(valeurs) else np.nan
    return pd.Series(moyennes), pd.Series(parts)


def lieux_sols(zones_regional, survey, zones_survey):
    """Retourne le contour de chaque lieu de regional et de survey, nommé dans la colonne zone."""
    return gpd.GeoDataFrame(
        pd.concat([zones_regional[["zone", "geometry"]], geometries_lieux_survey(survey, zones_survey)],
                  ignore_index=True), crs="EPSG:4326")


def verifier_fenetre(lieux, fenetre=FENETRE_AFRIQUE):
    """Lève une erreur si un lieu déborde de la fenêtre découpée."""
    xmin, ymin, xmax, ymax = lieux.to_crs(CRS_SOILGRIDS).total_bounds
    gauche, haut = TRANSFORMATION_1KM @ (fenetre.col_off, fenetre.row_off)
    droite, bas = TRANSFORMATION_1KM @ (fenetre.col_off + fenetre.width, fenetre.row_off + fenetre.height)
    if xmin < gauche or xmax > droite or ymin < bas or ymax > haut:
        raise ValueError("Des lieux débordent de la fenêtre découpée de SoilGrids")


def variables_lieux(lieux, dossier=DOSSIER_SOILGRIDS):
    """Retourne les variables de sol de chaque lieu, une propriété après l'autre."""
    verifier_fenetre(lieux)
    with rasterio.open(chemin_couche("clay", "0-5cm", dossier)) as raster:
        pixels = pixels_lieux(lieux, raster.transform, raster.shape)
    resultat = pd.DataFrame(index=pd.Index(list(pixels), name="lieu"))
    resultat["pixels_sol"] = pd.Series({nom: len(positions) for nom, positions in pixels.items()})
    for propriete, (nom, _, _) in PROPRIETES.items():
        moyennes, parts = moyennes_lieux(pixels, couche_0_30(propriete, dossier))
        resultat[f"{nom}_0_30"] = moyennes
        if propriete == "clay":
            resultat["part_sol_valide"] = parts
    return resultat.reset_index()


def construire(dossier=DOSSIER_TRAITE, sols=DOSSIER_SOILGRIDS):
    """Construit et écrit les variables de sol de regional, par zone, et de survey, par parcelle."""
    zones_regional = gpd.read_file(dossier / "zones_regional.gpkg")
    survey = pd.read_csv(dossier / "survey_modelisation.csv.gz", low_memory=False)
    zones_survey = gpd.read_file(dossier / "zones_survey.gpkg")
    variables = variables_lieux(lieux_sols(zones_regional, survey, zones_survey), sols)

    sols_regional = variables[~variables["lieu"].str.contains(":")].rename(columns={"lieu": "GDAM_ID"})
    sols_regional.to_csv(dossier / "sols_regional.csv.gz", index=False)
    lieu, nature = lieu_survey(survey)
    sols_survey = pd.DataFrame({"id_ligne": survey["id_ligne"], "lieu": lieu, "nature_lieu": nature}).merge(
        variables, on="lieu", how="left")
    sols_survey.to_csv(dossier / "sols_survey.csv.gz", index=False)
    return sols_regional, sols_survey


if __name__ == "__main__":
    if sys.argv[1:] == ["extraire"]:
        extraire_couches()
    elif sys.argv[1:] == ["construire"]:
        for nom, tableau in zip(["sols_regional", "sols_survey"], construire()):
            print(f"{nom:<14} {tableau.shape[0]:>7} lignes {tableau.shape[1]:>3} colonnes")
    else:
        raise SystemExit("Usage python -m src.features.sols extraire|construire")
