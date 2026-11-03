"""Acquisition des séries climatiques journalières de NASA POWER.

NASA POWER diffuse sans compte des séries journalières issues de la réanalyse
MERRA-2 et, pour le rayonnement, du produit CERES. Chaque requête renvoie la série
complète d'une maille de 0,5 degré de latitude sur 0,625 degré de longitude. Les
mailles interrogées sont celles qui recoupent une zone de regional ou de survey, ou le
voisinage de 5 km d'une grappe. La valeur d'une zone est la moyenne des mailles
pondérée par la surface de leur intersection avec la zone.

Exécution depuis la racine du projet avec la commande python -m src.features.climat.
"""

import gzip
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import box

from .acquisition import DOSSIER_EXTERNE, REGISTRE, consigner
from .geographie import PROJECTION_EQUIVALENTE

URL_POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETRES_POWER = ["T2M_MAX", "T2M_MIN", "T2MDEW", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M", "GWETROOT"]
DEBUT_POWER = "19810101"
FIN_POWER = "20231231"
VALEUR_MANQUANTE_POWER = -999.0
PAS_LATITUDE = 0.5
PAS_LONGITUDE = 0.625
DOSSIER_POWER = DOSSIER_EXTERNE / "power"
RAYON_GRAPPE_DEGRES = 0.05


def centre_maille(latitude, longitude):
    """Retourne le centre de la maille MERRA-2 qui contient un point."""
    lat = np.round(np.asarray(latitude) / PAS_LATITUDE) * PAS_LATITUDE
    lon = np.round((np.asarray(longitude) + 180) / PAS_LONGITUDE) * PAS_LONGITUDE - 180
    return lat + 0.0, lon + 0.0


def nom_maille(latitude, longitude):
    """Retourne l'identifiant textuel d'une maille à partir de son centre."""
    return f"{latitude:+06.1f}_{longitude:+08.3f}"


def grille_mailles(geometries):
    """Retourne les mailles MERRA-2 qui recoupent au moins une des géométries.

    Le résultat contient maille, latitude et longitude du centre, et geometry.
    """
    xmin, ymin, xmax, ymax = geometries.total_bounds
    lat_min, lon_min = centre_maille(ymin, xmin)
    lat_max, lon_max = centre_maille(ymax, xmax)
    latitudes = np.arange(lat_min, lat_max + PAS_LATITUDE / 2, PAS_LATITUDE)
    longitudes = np.arange(lon_min, lon_max + PAS_LONGITUDE / 2, PAS_LONGITUDE)
    lat, lon = (grille.ravel() for grille in np.meshgrid(latitudes, longitudes, indexing="ij"))
    mailles = gpd.GeoDataFrame(
        {"latitude": np.round(lat, 4), "longitude": np.round(lon, 4)},
        geometry=[
            box(x - PAS_LONGITUDE / 2, y - PAS_LATITUDE / 2, x + PAS_LONGITUDE / 2, y + PAS_LATITUDE / 2)
            for y, x in zip(lat, lon)
        ],
        crs="EPSG:4326",
    )
    touchees = gpd.sjoin(mailles, gpd.GeoDataFrame(geometry=geometries.to_numpy(), crs=geometries.crs),
                         predicate="intersects").index.unique()
    mailles = mailles.loc[touchees].sort_index().reset_index(drop=True)
    mailles.insert(0, "maille", [nom_maille(y, x) for y, x in zip(mailles["latitude"], mailles["longitude"])])
    return mailles


def poids_mailles(zones, mailles, colonne_zone="zone"):
    """Retourne le poids de chaque maille dans chaque zone.

    Le poids est la part de la surface de la zone couverte par la maille, calculée
    dans une projection à surfaces équivalentes. Les poids d'une zone somment à un.
    """
    intersection = gpd.overlay(
        zones[[colonne_zone, "geometry"]].to_crs(PROJECTION_EQUIVALENTE),
        mailles[["maille", "geometry"]].to_crs(PROJECTION_EQUIVALENTE),
        how="intersection",
        keep_geom_type=True,
    )
    intersection["surface"] = intersection.geometry.area
    intersection = intersection.groupby([colonne_zone, "maille"], as_index=False)["surface"].sum()
    intersection["poids"] = intersection["surface"] / intersection.groupby(colonne_zone)["surface"].transform("sum")
    return intersection.drop(columns="surface").rename(columns={colonne_zone: "zone"})


def chemin_maille(maille, dossier=DOSSIER_POWER):
    """Retourne le chemin du fichier compressé d'une maille."""
    return dossier / f"power_{maille}.csv.gz"


def lire_power(chemin):
    """Lit la série journalière d'une maille et remplace le code -999 par une valeur manquante."""
    with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
        texte = fichier.read()
    donnees = pd.read_csv(io.StringIO(texte.split("-END HEADER-", 1)[1]))
    donnees = donnees.replace(VALEUR_MANQUANTE_POWER, np.nan)
    date = pd.to_datetime(donnees["YEAR"].astype(str), format="%Y") + pd.to_timedelta(donnees["DOY"] - 1, unit="D")
    return donnees.drop(columns=["YEAR", "DOY"]).set_index(date.rename("date"))


def telecharger_maille(latitude, longitude, dossier=DOSSIER_POWER, registre=REGISTRE, tentatives=6):
    """Télécharge la série d'une maille si elle est absente, la compresse et la consigne.

    Une réponse incomplète ou refusée est retentée avec une attente croissante. Le
    fichier n'est écrit que si la réponse contient l'en-tête et l'ensemble des jours.
    """
    chemin = chemin_maille(nom_maille(latitude, longitude), dossier)
    if chemin.exists():
        return chemin
    parametres = {
        "parameters": ",".join(PARAMETRES_POWER),
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": DEBUT_POWER,
        "end": FIN_POWER,
        "format": "CSV",
        "time-standard": "LST",
    }
    jours = (pd.Timestamp(FIN_POWER) - pd.Timestamp(DEBUT_POWER)).days + 1
    for tentative in range(tentatives):
        try:
            reponse = requests.get(URL_POWER, params=parametres, timeout=120)
            if reponse.status_code == 200 and "-END HEADER-" in reponse.text:
                corps = reponse.text.split("-END HEADER-", 1)[1].strip().splitlines()
                if len(corps) == jours + 1:
                    dossier.mkdir(parents=True, exist_ok=True)
                    temporaire = chemin.with_name(chemin.name + ".partiel")
                    with gzip.open(temporaire, "wt", encoding="utf-8") as fichier:
                        fichier.write(reponse.text)
                    temporaire.rename(chemin)
                    consigner(chemin, reponse.url, registre)
                    return chemin
        except requests.RequestException:
            pass
        time.sleep(5 * 2 ** tentative)
    raise RuntimeError(f"Série POWER indisponible pour la maille {nom_maille(latitude, longitude)}")


def telecharger_mailles(mailles, dossier=DOSSIER_POWER, registre=REGISTRE, paralleles=3):
    """Télécharge les séries manquantes de plusieurs mailles et retourne les mailles en échec."""
    manquantes = [
        (lat, lon) for lat, lon in zip(mailles["latitude"], mailles["longitude"])
        if not chemin_maille(nom_maille(lat, lon), dossier).exists()
    ]
    echecs = []
    with ThreadPoolExecutor(max_workers=paralleles) as executeur:
        taches = {executeur.submit(telecharger_maille, lat, lon, dossier, registre): (lat, lon) for lat, lon in manquantes}
        for rang, tache in enumerate(as_completed(taches), start=1):
            try:
                tache.result()
            except RuntimeError:
                echecs.append(nom_maille(*taches[tache]))
            if rang % 100 == 0 or rang == len(taches):
                print(f"{rang} mailles sur {len(taches)}, {len(echecs)} en échec", flush=True)
    return echecs


def geometries_a_couvrir(zones_regional, zones_survey, survey):
    """Réunit les contours des zones et le voisinage de 5 km de chaque grappe de survey.

    Le voisinage est un disque de 0,05 degré, qui dépasse 5 km dans toutes les
    directions aux latitudes des grappes de survey, comprises entre 18 degrés sud et
    21 degrés nord. Il ne sert qu'à choisir les mailles à télécharger.
    """
    grappes = survey.dropna(subset=["GPS_lat", "GPS_lon"]).drop_duplicates(["GPS_lat", "GPS_lon"])
    voisinages = gpd.GeoSeries(gpd.points_from_xy(grappes["GPS_lon"], grappes["GPS_lat"]), crs="EPSG:4326")
    voisinages = voisinages.buffer(RAYON_GRAPPE_DEGRES)
    return pd.concat([zones_regional.geometry, zones_survey.geometry, voisinages], ignore_index=True)


if __name__ == "__main__":
    from src.data.load import DOSSIER_TRAITE

    geometries = geometries_a_couvrir(
        gpd.read_file(DOSSIER_TRAITE / "zones_regional.gpkg"),
        gpd.read_file(DOSSIER_TRAITE / "zones_survey.gpkg"),
        pd.read_csv(DOSSIER_TRAITE / "survey_modelisation.csv.gz", low_memory=False),
    )
    mailles = grille_mailles(gpd.GeoSeries(geometries, crs="EPSG:4326"))
    print(f"{len(mailles)} mailles à couvrir", flush=True)
    echecs = telecharger_mailles(mailles)
    print("Mailles en échec :", echecs)
