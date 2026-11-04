"""Variables de relief tirées de Copernicus DEM à 90 m.

Copernicus DEM GLO-90 est diffusé sans compte sur Amazon S3, en tuiles d'un degré de
1 200 sur 1 200 pixels de 3 secondes d'arc. Chaque tuile est accompagnée d'un masque
des eaux. L'empreinte MD5 de chaque fichier est publiée par le serveur dans son ETag.

Chaque tuile est téléchargée avec son masque, vérifiée, puis traitée à 90 m. La pente
y est calculée par la méthode de Horn, avec des pas en mètres qui tiennent compte de
la latitude. Les pixels de mer, de lac et de rivière sont écartés. L'altitude et la
pente sont ensuite agrégées sur la grille à 1 km de SoilGrids, qui conserve les
surfaces, chaque pixel de 90 m étant pondéré par sa surface. Seuls ces résumés par
tuile sont conservés, ce qui permet de reprendre une extraction interrompue.

Exécution depuis la racine du projet avec les commandes python -m src.features.relief
extraire, puis python -m src.features.relief construire.
"""

import csv
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rasterio.windows
import requests
from pyproj import Transformer
from shapely.geometry import box
from shapely.prepared import prep

from src.data.load import DOSSIER_INTERMEDIAIRE, DOSSIER_TRAITE

from .acquisition import DOSSIER_EXTERNE, _poursuivre, empreinte_md5
from .lieux import lieu_survey
from .sols import CRS_SOILGRIDS, FENETRE_AFRIQUE, TRANSFORMATION_1KM, lieux_sols, moyennes_lieux, pixels_lieux, verifier_fenetre

URL_COPERNICUS = "https://copernicus-dem-90m.s3.amazonaws.com/"
DOSSIER_COPERNICUS = DOSSIER_EXTERNE / "copernicus"
DOSSIER_RELIEF = DOSSIER_INTERMEDIAIRE / "relief"
RAYON_TERRE = 6371008.8
COLONNES_SOURCES = ["tuile", "url", "octets", "md5", "derniere_modification"]
VARIABLES_RELIEF = {"altitude": "altitude_moyenne", "pente": "pente_moyenne"}


def nom_tuile(latitude, longitude):
    """Retourne le nom de la tuile dont le coin sud-ouest est donné en degrés entiers."""
    return (f"Copernicus_DSM_COG_30_{'N' if latitude >= 0 else 'S'}{abs(latitude):02d}_00_"
            f"{'E' if longitude >= 0 else 'W'}{abs(longitude):03d}_00_DEM")


def url_tuile(nom, masque=False):
    """Retourne l'adresse du modèle numérique d'une tuile ou de son masque des eaux."""
    if masque:
        return f"{URL_COPERNICUS}{nom}/AUXFILES/{nom.replace('_DEM', '_WBM')}.tif"
    return f"{URL_COPERNICUS}{nom}/{nom}.tif"


def tuiles_a_couvrir(lieux, existantes):
    """Retourne les tuiles existantes qui recoupent au moins un lieu."""
    union = prep(lieux.to_crs("EPSG:4326").geometry.union_all())
    xmin, ymin, xmax, ymax = lieux.to_crs("EPSG:4326").total_bounds
    noms = [
        nom_tuile(lat, lon)
        for lat in range(int(np.floor(ymin)), int(np.ceil(ymax)))
        for lon in range(int(np.floor(xmin)), int(np.ceil(xmax)))
        if union.intersects(box(lon, lat, lon + 1, lat + 1))
    ]
    return [nom for nom in noms if nom in existantes]


def liste_tuiles():
    """Retourne l'ensemble des tuiles publiées."""
    reponse = requests.get(URL_COPERNICUS + "tileList.txt", timeout=60)
    reponse.raise_for_status()
    return set(reponse.text.split())


def pente_horn(altitude, latitudes, pas_degres):
    """Retourne la pente en degrés par la méthode de Horn, les bords étant prolongés.

    latitudes donne la latitude de chaque ligne et pas_degres la taille d'un pixel en
    degrés. Le pas est-ouest en mètres diminue avec le cosinus de la latitude.
    """
    z = np.pad(altitude.astype(np.float64), 1, mode="edge")
    pas_y = RAYON_TERRE * np.radians(pas_degres)
    pas_x = (pas_y * np.cos(np.radians(latitudes)))[:, None]
    dzdx = ((z[:-2, 2:] + 2 * z[1:-1, 2:] + z[2:, 2:]) - (z[:-2, :-2] + 2 * z[1:-1, :-2] + z[2:, :-2])) / (8 * pas_x)
    dzdy = ((z[2:, :-2] + 2 * z[2:, 1:-1] + z[2:, 2:]) - (z[:-2, :-2] + 2 * z[:-2, 1:-1] + z[:-2, 2:])) / (8 * pas_y)
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy)))


def agreger_grille(longitudes, latitudes, valeurs, poids, transformation=TRANSFORMATION_1KM,
                   fenetre=FENETRE_AFRIQUE):
    """Somme des poids et des valeurs pondérées par pixel de la grille à 1 km.

    Les points sont projetés dans la projection de SoilGrids, et chaque point est
    affecté au pixel de la fenêtre qui contient son centre. Retourne les positions à
    plat des pixels dans la fenêtre, la somme des poids et la somme pondérée de chaque
    tableau de valeurs.
    """
    x, y = Transformer.from_crs("EPSG:4326", CRS_SOILGRIDS, always_xy=True).transform(longitudes, latitudes)
    colonne = np.floor((x - transformation.c) / transformation.a).astype(np.int64) - fenetre.col_off
    ligne = np.floor((y - transformation.f) / transformation.e).astype(np.int64) - fenetre.row_off
    dedans = (colonne >= 0) & (colonne < fenetre.width) & (ligne >= 0) & (ligne < fenetre.height)
    position = ligne[dedans] * fenetre.width + colonne[dedans]
    pixels, inverse = np.unique(position, return_inverse=True)
    sommes = [np.bincount(inverse, weights=poids[dedans], minlength=len(pixels))]
    for tableau in valeurs:
        sommes.append(np.bincount(inverse, weights=(tableau * poids)[dedans], minlength=len(pixels)))
    return pixels, sommes


def traiter_tuile(chemin_altitude, chemin_masque):
    """Calcule l'altitude et la pente d'une tuile et les agrège sur la grille à 1 km."""
    with rasterio.open(chemin_altitude) as raster:
        altitude = raster.read(1).astype(np.float64)
        transformation = raster.transform
    with rasterio.open(chemin_masque) as raster:
        eau = raster.read(1) > 0
        if not raster.transform.almost_equals(transformation) or eau.shape != altitude.shape:
            raise ValueError(f"Le masque des eaux ne suit pas la grille de {chemin_altitude.name}")
    lignes, colonnes = np.indices(altitude.shape)
    longitudes = transformation.c + (colonnes + 0.5) * transformation.a
    latitudes = transformation.f + (lignes + 0.5) * transformation.e
    pente = pente_horn(altitude, latitudes[:, 0], transformation.a)
    terre = ~eau & np.isfinite(altitude)
    pixels, sommes = agreger_grille(longitudes[terre], latitudes[terre], [altitude[terre], pente[terre]],
                                    np.cos(np.radians(latitudes[terre])))
    return pixels, sommes, int(terre.sum())


def _telecharger(url, chemin, tentatives):
    """Télécharge un fichier et vérifie son empreinte MD5 publiée dans l'ETag."""
    entetes = requests.head(url, timeout=60).headers
    etag = entetes["ETag"].strip('"')
    if "-" in etag:
        raise ValueError(f"ETag composite sans empreinte MD5 pour {url}")
    for essai in range(tentatives):
        try:
            if _poursuivre(url, chemin):
                break
        except requests.RequestException:
            time.sleep(5 * (essai + 1))
    else:
        raise RuntimeError(f"Téléchargement incomplet après {tentatives} tentatives pour {url}")
    if empreinte_md5(chemin) != etag:
        chemin.unlink()
        raise ValueError(f"Empreinte MD5 inattendue pour {url}, fichier supprimé")
    return [url, chemin.stat().st_size, etag, entetes.get("Last-Modified")]


def _extraire(nom, dossier_tuiles, tentatives):
    """Télécharge, vérifie et traite une tuile, puis écrit son résumé et supprime les fichiers."""
    with tempfile.TemporaryDirectory() as temporaire:
        lignes = []
        chemins = []
        for masque in [False, True]:
            chemin = Path(temporaire) / url_tuile(nom, masque).rsplit("/", 1)[1]
            lignes.append([nom, *_telecharger(url_tuile(nom, masque), chemin, tentatives)])
            chemins.append(chemin)
        pixels, sommes, terre = traiter_tuile(*chemins)
    partiel = dossier_tuiles / f"{nom}.partiel.npz"
    np.savez_compressed(partiel, pixels=pixels, poids=sommes[0], altitude=sommes[1], pente=sommes[2], terre=terre)
    partiel.rename(dossier_tuiles / f"{nom}.npz")
    return lignes


def extraire_tuiles(dossier=DOSSIER_TRAITE, relief=DOSSIER_RELIEF, sources=DOSSIER_COPERNICUS, processus=8,
                    tentatives=6):
    """Traite chaque tuile qui recoupe un lieu du projet, en sautant celles déjà résumées.

    Les empreintes vérifiées des tuiles et de leurs masques sont consignées dans
    sources.csv, et les tuiles elles-mêmes ne sont pas conservées.
    """
    lieux = lieux_sols(gpd.read_file(dossier / "zones_regional.gpkg"),
                       pd.read_csv(dossier / "survey_modelisation.csv.gz", low_memory=False),
                       gpd.read_file(dossier / "zones_survey.gpkg"))
    dossier_tuiles = relief / "tuiles"
    dossier_tuiles.mkdir(parents=True, exist_ok=True)
    sources.mkdir(parents=True, exist_ok=True)
    taches = [nom for nom in tuiles_a_couvrir(lieux, liste_tuiles()) if not (dossier_tuiles / f"{nom}.npz").exists()]
    print(f"{len(taches)} tuiles à traiter", flush=True)
    fichier_sources = sources / "sources.csv"
    echecs = []
    with ProcessPoolExecutor(processus) as executeur:
        futurs = {executeur.submit(_extraire, nom, dossier_tuiles, tentatives): nom for nom in taches}
        for rang, futur in enumerate(as_completed(futurs), 1):
            try:
                lignes = futur.result()
            except Exception as erreur:
                echecs.append(futurs[futur])
                print(f"Échec pour {futurs[futur]} {erreur!r}", flush=True)
                continue
            nouveau = not fichier_sources.exists()
            with open(fichier_sources, "a", newline="", encoding="utf-8") as fichier:
                ecrivain = csv.writer(fichier)
                if nouveau:
                    ecrivain.writerow(COLONNES_SOURCES)
                ecrivain.writerows(lignes)
            if rang % 100 == 0 or rang == len(taches):
                print(f"{rang} tuiles traitées sur {len(taches)}", flush=True)
    if echecs:
        raise RuntimeError(f"{len(echecs)} tuiles en échec, à reprendre en relançant la commande")


def construire_mosaique(relief=DOSSIER_RELIEF, fenetre=FENETRE_AFRIQUE):
    """Réunit les résumés des tuiles en deux rasters à 1 km, altitude et pente moyennes.

    Un pixel partagé entre plusieurs tuiles reçoit la moyenne pondérée de tous ses
    points. Un pixel sans terre émergée reste manquant.
    """
    chemins = [c for c in sorted((relief / "tuiles").glob("*.npz")) if not c.name.endswith(".partiel.npz")]

    def cumuler(nom):
        total = np.zeros(fenetre.width * fenetre.height, dtype=np.float32)
        for chemin in chemins:
            with np.load(chemin) as resume:
                np.add.at(total, resume["pixels"], resume[nom].astype(np.float32))
        return total

    profil = {
        "driver": "GTiff", "height": fenetre.height, "width": fenetre.width, "count": 1, "dtype": "float32",
        "crs": CRS_SOILGRIDS, "transform": rasterio.windows.transform(fenetre, TRANSFORMATION_1KM),
        "nodata": np.nan, "compress": "deflate", "predictor": 3, "tiled": True, "blockxsize": 512, "blockysize": 512,
    }
    poids = cumuler("poids")
    for nom in VARIABLES_RELIEF:
        total = cumuler(nom)
        with np.errstate(invalid="ignore", divide="ignore"):
            moyenne = np.where(poids > 0, total / poids, np.nan).reshape(fenetre.height, fenetre.width)
        del total
        with rasterio.open(relief / f"{nom}_1km.tif", "w", **profil) as destination:
            destination.write(moyenne.astype(np.float32), 1)


def variables_lieux(lieux, relief=DOSSIER_RELIEF):
    """Retourne l'altitude et la pente moyennes de chaque lieu et la part de pixels avec terre émergée."""
    verifier_fenetre(lieux)
    resultat = None
    for nom, variable in VARIABLES_RELIEF.items():
        with rasterio.open(relief / f"{nom}_1km.tif") as raster:
            couche = raster.read(1)
            if resultat is None:
                pixels = pixels_lieux(lieux, raster.transform, raster.shape)
                resultat = pd.DataFrame(index=pd.Index(list(pixels), name="lieu"))
                resultat["pixels_relief"] = pd.Series({lieu: len(positions) for lieu, positions in pixels.items()})
        moyennes, parts = moyennes_lieux(pixels, couche)
        resultat[variable] = moyennes
        if nom == "altitude":
            resultat["part_relief_valide"] = parts
    return resultat.reset_index()


def construire(dossier=DOSSIER_TRAITE, relief=DOSSIER_RELIEF):
    """Construit la mosaïque à 1 km et écrit les variables de relief de regional et de survey."""
    construire_mosaique(relief)
    zones_regional = gpd.read_file(dossier / "zones_regional.gpkg")
    survey = pd.read_csv(dossier / "survey_modelisation.csv.gz", low_memory=False)
    zones_survey = gpd.read_file(dossier / "zones_survey.gpkg")
    variables = variables_lieux(lieux_sols(zones_regional, survey, zones_survey), relief)

    relief_regional = variables[~variables["lieu"].str.contains(":")].rename(columns={"lieu": "GDAM_ID"})
    relief_regional.to_csv(dossier / "relief_regional.csv.gz", index=False)
    lieu, nature = lieu_survey(survey)
    relief_survey = pd.DataFrame({"id_ligne": survey["id_ligne"], "lieu": lieu, "nature_lieu": nature}).merge(
        variables, on="lieu", how="left")
    relief_survey.to_csv(dossier / "relief_survey.csv.gz", index=False)
    return relief_regional, relief_survey


if __name__ == "__main__":
    if sys.argv[1:] == ["extraire"]:
        extraire_tuiles()
    elif sys.argv[1:] == ["construire"]:
        for nom, tableau in zip(["relief_regional", "relief_survey"], construire()):
            print(f"{nom:<16} {tableau.shape[0]:>7} lignes {tableau.shape[1]:>3} colonnes")
    else:
        raise SystemExit("Usage python -m src.features.relief extraire|construire")
