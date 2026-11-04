"""Acquisition des séries climatiques journalières de NASA POWER.

NASA POWER diffuse sans compte des séries journalières issues de la réanalyse
MERRA-2 et, pour le rayonnement, du produit CERES. Chaque requête renvoie la série
complète d'une maille de 0,5 degré de latitude sur 0,625 degré de longitude. Les
précipitations proviennent du produit satellitaire IMERG, que NASA POWER diffuse au
pas journalier en temps universel à partir de juin 2000. Elles ne proviennent pas de
PRECTOTCORR, dont l'intensité n'est pas homogène dans le temps, avec des cumuls
journaliers aberrants et un excès de 11 à 20 % par rapport à IMERG de 2020 à 2022.
IMERG est interrogé au centre de chaque maille. Les mailles interrogées sont celles qui recoupent une zone de regional ou de survey, ou le
voisinage de 5 km d'une grappe. La valeur d'une zone est la moyenne des mailles
pondérée par la surface de leur intersection avec la zone.

Exécution depuis la racine du projet avec la commande python -m src.features.climat.
"""

import gzip
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import box

from src.data.load import DOSSIER_INTERMEDIAIRE

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
PARAMETRES_IMERG = ["IMERG_PRECTOT"]
DEBUT_IMERG = "20000601"
DOSSIER_IMERG = DOSSIER_EXTERNE / "imerg"
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


def chemin_maille(maille, dossier=DOSSIER_POWER, prefixe="power"):
    """Retourne le chemin du fichier compressé d'une maille."""
    return dossier / f"{prefixe}_{maille}.csv.gz"


def lire_power(chemin):
    """Lit la série journalière d'une maille et remplace le code -999 par une valeur manquante."""
    with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
        texte = fichier.read()
    donnees = pd.read_csv(io.StringIO(texte.split("-END HEADER-", 1)[1]))
    donnees = donnees.replace(VALEUR_MANQUANTE_POWER, np.nan)
    date = pd.to_datetime(donnees["YEAR"].astype(str), format="%Y") + pd.to_timedelta(donnees["DOY"] - 1, unit="D")
    return donnees.drop(columns=["YEAR", "DOY"]).set_index(date.rename("date"))


DOSSIER_MAGASIN = DOSSIER_INTERMEDIAIRE / "climat"
VARIABLES_RETENUES = {
    "power": ["T2M_MAX", "T2M_MIN", "T2MDEW", "ALLSKY_SFC_SW_DWN", "WS2M"],
    "imerg": ["IMERG_PRECTOT"],
}

PRODUITS = {
    "power": {"parametres": PARAMETRES_POWER, "debut": DEBUT_POWER, "temps": "LST", "dossier": DOSSIER_POWER},
    "imerg": {"parametres": PARAMETRES_IMERG, "debut": DEBUT_IMERG, "temps": "UTC", "dossier": DOSSIER_IMERG},
}


def telecharger_maille(latitude, longitude, produit="power", dossier=None, registre=REGISTRE, tentatives=6):
    """Télécharge la série d'une maille si elle est absente, la compresse et la consigne.

    Le produit vaut power pour les six variables issues de MERRA-2 et de CERES, ou
    imerg pour les précipitations. IMERG n'est diffusé qu'en temps universel. Une
    réponse incomplète ou refusée est retentée avec une attente croissante. Le fichier
    n'est écrit que si la réponse contient l'en-tête et l'ensemble des jours.
    """
    choix = PRODUITS[produit]
    dossier = choix["dossier"] if dossier is None else dossier
    chemin = chemin_maille(nom_maille(latitude, longitude), dossier, produit)
    if chemin.exists():
        return chemin
    parametres = {
        "parameters": ",".join(choix["parametres"]),
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": choix["debut"],
        "end": FIN_POWER,
        "format": "CSV",
        "time-standard": choix["temps"],
    }
    jours = (pd.Timestamp(FIN_POWER) - pd.Timestamp(choix["debut"])).days + 1
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


def telecharger_mailles(mailles, produit="power", dossier=None, registre=REGISTRE, paralleles=3):
    """Télécharge les séries manquantes de plusieurs mailles et retourne les mailles en échec."""
    dossier = PRODUITS[produit]["dossier"] if dossier is None else dossier
    manquantes = [
        (lat, lon) for lat, lon in zip(mailles["latitude"], mailles["longitude"])
        if not chemin_maille(nom_maille(lat, lon), dossier, produit).exists()
    ]
    echecs = []
    with ThreadPoolExecutor(max_workers=paralleles) as executeur:
        taches = {
            executeur.submit(telecharger_maille, lat, lon, produit, dossier, registre): (lat, lon)
            for lat, lon in manquantes
        }
        for rang, tache in enumerate(as_completed(taches), start=1):
            try:
                tache.result()
            except RuntimeError:
                echecs.append(nom_maille(*taches[tache]))
            if rang % 100 == 0 or rang == len(taches):
                print(f"{rang} mailles sur {len(taches)}, {len(echecs)} en échec", flush=True)
    return echecs


def mailles_telechargees(produit="power", dossier=None):
    """Retourne les mailles dont la série d'un produit est présente, triées par nom."""
    dossier = PRODUITS[produit]["dossier"] if dossier is None else dossier
    noms = sorted(c.name[len(produit) + 1:-len(".csv.gz")] for c in dossier.glob(f"{produit}_*.csv.gz"))
    centres = [tuple(float(x) for x in nom.split("_")) for nom in noms]
    return pd.DataFrame({
        "maille": noms,
        "latitude": [c[0] for c in centres],
        "longitude": [c[1] for c in centres],
    })


def altitude_power(chemin):
    """Retourne l'altitude moyenne de la maille, en mètres, inscrite dans l'en-tête de NASA POWER."""
    with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
        for ligne in fichier:
            trouve = re.search(r"elevation from MERRA-2.*= *(-?[\d.]+) meters", ligne)
            if trouve or "-END HEADER-" in ligne:
                return float(trouve.group(1)) if trouve else np.nan
    return np.nan


def _lire_maille(arguments):
    chemin, variables = arguments
    return altitude_power(chemin), lire_power(chemin)[variables].to_numpy(dtype=np.float32).T


def construire_magasin(mailles, produit="power", dossier=None, magasin=DOSSIER_MAGASIN, processus=6):
    """Réunit les séries d'un produit dans un tableau par variable, indexé par maille et par jour.

    Chaque tableau est écrit au format npy dans le magasin et se relit sans être chargé
    en mémoire. Le fichier des mailles donne l'ordre des lignes et celui des dates
    l'ordre des colonnes. Seules les variables retenues comme explicatives sont copiées.
    L'altitude de chaque maille, fournie par NASA POWER pour MERRA-2, accompagne les mailles.
    """
    choix = PRODUITS[produit]
    dossier = choix["dossier"] if dossier is None else dossier
    variables = VARIABLES_RETENUES[produit]
    dates = pd.date_range(choix["debut"], FIN_POWER, freq="D")
    magasin.mkdir(parents=True, exist_ok=True)
    tableaux = {
        v: np.lib.format.open_memmap(magasin / f"{produit}_{v}.npy", mode="w+", dtype=np.float32,
                                     shape=(len(mailles), len(dates)))
        for v in variables
    }
    chemins = [(chemin_maille(m, dossier, produit), variables) for m in mailles["maille"]]
    altitudes = np.full(len(mailles), np.nan)
    with Pool(processus) as pool:
        for rang, (altitude, valeurs) in enumerate(pool.imap(_lire_maille, chemins, chunksize=20)):
            altitudes[rang] = altitude
            for position, variable in enumerate(variables):
                tableaux[variable][rang] = valeurs[position]
    for tableau in tableaux.values():
        tableau.flush()
    mailles = mailles[["maille", "latitude", "longitude"]].assign(altitude=altitudes)
    mailles.to_csv(magasin / f"{produit}_mailles.csv", index=False)
    pd.Series(dates.strftime("%Y-%m-%d"), name="date").to_csv(magasin / f"{produit}_dates.csv", index=False)


def ouvrir_magasin(produit="power", magasin=DOSSIER_MAGASIN):
    """Retourne les mailles, les dates et les tableaux du magasin d'un produit, lus à la demande."""
    mailles = pd.read_csv(magasin / f"{produit}_mailles.csv")
    dates = pd.DatetimeIndex(pd.read_csv(magasin / f"{produit}_dates.csv")["date"])
    tableaux = {v: np.load(magasin / f"{produit}_{v}.npy", mmap_mode="r") for v in VARIABLES_RETENUES[produit]}
    return mailles, dates, tableaux


def geometries_a_couvrir(zones_regional, zones_survey, survey):
    """Réunit les contours des zones et le voisinage de 5 km de chaque grappe de survey.

    Le voisinage est un disque de 0,05 degré, qui dépasse 5 km dans toutes les
    directions aux latitudes des grappes de survey, comprises entre 18 degrés sud et
    21 degrés nord. Il ne sert qu'à choisir les mailles à télécharger. Les
    coordonnées nulles, qui codent une position manquante, sont ignorées.
    """
    grappes = survey.dropna(subset=["GPS_lat", "GPS_lon"]).drop_duplicates(["GPS_lat", "GPS_lon"])
    grappes = grappes[(grappes["GPS_lat"] != 0) | (grappes["GPS_lon"] != 0)]
    voisinages = gpd.GeoSeries(gpd.points_from_xy(grappes["GPS_lon"], grappes["GPS_lat"]), crs="EPSG:4326")
    voisinages = voisinages.buffer(RAYON_GRAPPE_DEGRES)
    return pd.concat([zones_regional.geometry, zones_survey.geometry, voisinages], ignore_index=True)


if __name__ == "__main__":
    import sys

    from src.data.load import DOSSIER_TRAITE

    produit = sys.argv[1] if len(sys.argv) > 1 else "power"

    geometries = geometries_a_couvrir(
        gpd.read_file(DOSSIER_TRAITE / "zones_regional.gpkg"),
        gpd.read_file(DOSSIER_TRAITE / "zones_survey.gpkg"),
        pd.read_csv(DOSSIER_TRAITE / "survey_modelisation.csv.gz", low_memory=False),
    )
    mailles = grille_mailles(gpd.GeoSeries(geometries, crs="EPSG:4326"))
    print(f"{len(mailles)} mailles à couvrir", flush=True)
    echecs = telecharger_mailles(mailles, produit)
    print("Mailles en échec :", echecs)
