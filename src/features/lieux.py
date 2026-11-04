"""Lieux climatiques des lignes de regional et de survey et poids de leurs mailles.

Une ligne de regional a pour lieu sa zone GDAM_ID. Une parcelle de survey a pour lieu
le voisinage de 5 km de sa grappe lorsque ses coordonnées sont connues, sinon sa
zone administrative de repli. Les coordonnées de survey sont déplacées de 0 à 5 km,
et le voisinage couvre ce déplacement.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from .agregation import voisinages_grappes
from .climat import PAS_LATITUDE, PAS_LONGITUDE, poids_mailles
from .geographie import zone_survey


def geometries_mailles(mailles):
    """Retourne le contour de chaque maille du magasin à partir de son centre."""
    return gpd.GeoDataFrame(
        mailles[["maille"]],
        geometry=[
            box(x - PAS_LONGITUDE / 2, y - PAS_LATITUDE / 2, x + PAS_LONGITUDE / 2, y + PAS_LATITUDE / 2)
            for y, x in zip(mailles["latitude"], mailles["longitude"])
        ],
        crs="EPSG:4326",
    )


def lieu_survey(survey):
    """Retourne le lieu climatique de chaque parcelle de survey et sa nature, grappe ou zone."""
    grappe = survey["id_grappe"].where(survey["GPS_lat"].notna() & survey["GPS_lon"].notna())
    zone = zone_survey(survey)
    lieu = ("grappe:" + grappe).fillna("zone:" + zone)
    nature = np.where(grappe.notna(), "grappe", np.where(zone.notna(), "zone", None))
    return lieu, pd.Series(nature, index=survey.index, name="nature_lieu")


def poids_regional(zones_regional, mailles):
    """Retourne les poids des mailles de chaque zone de regional, le lieu valant GDAM_ID."""
    return poids_mailles(zones_regional, geometries_mailles(mailles)).rename(columns={"zone": "lieu"})


def poids_survey(survey, zones_survey, mailles):
    """Retourne les poids des mailles de chaque lieu de survey, grappe ou zone de repli."""
    cellules = geometries_mailles(mailles)
    grappes = survey.dropna(subset=["GPS_lat", "GPS_lon", "id_grappe"]).drop_duplicates("id_grappe")
    voisinages = gpd.GeoDataFrame(
        {"zone": "grappe:" + grappes["id_grappe"].to_numpy()},
        geometry=voisinages_grappes(grappes["GPS_lat"], grappes["GPS_lon"]).to_numpy(), crs="EPSG:4326",
    )
    zones = zones_survey[["zone", "geometry"]].assign(zone=lambda x: "zone:" + x["zone"])
    lieux = pd.concat([voisinages, zones], ignore_index=True)
    return poids_mailles(gpd.GeoDataFrame(lieux, crs="EPSG:4326"), cellules).rename(columns={"zone": "lieu"})
