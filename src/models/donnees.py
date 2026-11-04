"""Assemblage des tables de modélisation de regional, de survey et de cropcut.

Chaque table réunit la cible, les partitions du protocole d'évaluation et les
variables explicatives construites dans src/features. Seules des variables
disponibles en fin de saison sont retenues, et aucune colonne classée comme fuite
dans docs/data_dictionary.md n'y figure.
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from src.data.load import DOSSIER_TRAITE
from src.data.regional import zone_geographique
from src.evaluation.partitions import partitionner_cropcut, partitionner_regional, partitionner_survey
from src.features.geographie import descripteurs_geographiques, signaler_surface_superieure_zone, zone_survey

ANNEE_MINIMALE_REGIONAL = 1981
CIBLE_REGIONAL = "yieldTonHa"
CIBLE_SURVEY = "YieldUsingGPS_ton_ha_"
CIBLE_CROPCUT = "Yield_ton_ha_"

VARIABLES_CLIMAT = [
    "pluie_cumul", "pluie_jours", "sequence_seche_max", "bilan_hydrique", "et0_cumul", "degres_jours",
    "degres_jours_30", "degres_jours_35", "tmax_moyenne", "tmin_moyenne", "dpv_moyen", "rayonnement_moyen",
]
VARIABLES_SOLS = [
    "argile_0_30", "limon_0_30", "sable_0_30", "carbone_organique_0_30", "azote_0_30", "ph_0_30", "cec_0_30",
    "densite_apparente_0_30", "elements_grossiers_0_30",
]
VARIABLES_RELIEF = ["altitude_moyenne", "pente_moyenne"]
VARIABLES_CALENDRIER = ["mois_semis", "mois_recolte", "duree_saison"]
VARIABLES_PLUIE = ["pluie_cumul", "pluie_jours", "sequence_seche_max", "bilan_hydrique"]

CATEGORIELLES_REGIONAL = ["crop", "saison", "country", "Source", "level", "crop_production_system"]
NUMERIQUES_REGIONAL = (
    ["harvest_year", "latitude", "longitude", "log_surface_zone"]
    + VARIABLES_CALENDRIER + VARIABLES_CLIMAT + VARIABLES_SOLS + VARIABLES_RELIEF
)
CATEGORIELLES_SURVEY = ["Crop", "Country"]
NUMERIQUES_SURVEY = ["annee_recolte", "latitude", "longitude"] + VARIABLES_CALENDRIER + VARIABLES_CLIMAT + VARIABLES_SOLS + VARIABLES_RELIEF


def duree_saison(mois_semis, mois_recolte):
    """Retourne le nombre de mois de la fenêtre de saison, bornes comprises.

    Des mois égaux désignent un cycle de douze mois, selon la règle de fenetre_saison.
    """
    ecart = (np.asarray(mois_recolte, dtype=float) - np.asarray(mois_semis, dtype=float)) % 12
    return np.where(ecart == 0, 12, ecart + 1)


def _ajouter_variables(table, cle, *tableaux):
    for tableau in tableaux:
        table = table.merge(tableau, on=cle, how="left", validate="many_to_one")
    return table


def table_regional(dossier=DOSSIER_TRAITE):
    """Retourne la table de modélisation de regional et le masque des lignes retenues.

    Les lignes retenues ont une année de récolte postérieure ou égale à 1981 et une
    surface récoltée compatible avec la surface de leur zone. Les autres restent dans la
    table pour la traçabilité.
    """
    regional = pd.read_csv(dossier / "regional_modelisation.csv.gz", low_memory=False)
    regional["zone"] = zone_geographique(regional)
    regional = partitionner_regional(regional)
    geographie = pd.read_csv(dossier / "geographie_regional.csv.gz")
    regional["flag_surface_superieure_zone"] = signaler_surface_superieure_zone(regional, geographie)

    cle = ["GDAM_ID", "crop", "saison", "harvest_year"]
    climat = pd.read_csv(dossier / "climat_regional.csv.gz").drop(columns=["lieu", "debut", "fin", "annee_saison"])
    sols = pd.read_csv(dossier / "sols_regional.csv.gz")
    relief = pd.read_csv(dossier / "relief_regional.csv.gz")
    table = regional.merge(climat, on=cle, how="left", validate="one_to_one")
    table = _ajouter_variables(table, "GDAM_ID", sols, relief)
    geographie = geographie.rename(columns={"zone": "GDAM_ID"})
    table = table.merge(geographie, on="GDAM_ID", how="left", validate="many_to_one")
    table["log_surface_zone"] = np.log(table["surface_km2"])
    table["duree_saison"] = duree_saison(table["mois_semis"], table["mois_recolte"])
    retenue = (table["harvest_year"] >= ANNEE_MINIMALE_REGIONAL) & ~table["flag_surface_superieure_zone"]
    return table, retenue


def table_survey(dossier=DOSSIER_TRAITE):
    """Retourne la table de modélisation de survey.

    La position d'une parcelle est celle de sa grappe, déplacée de 0 à 5 km par
    l'enquête, ou à défaut le centroïde de sa zone de repli.
    """
    survey = partitionner_survey(pd.read_csv(dossier / "survey_modelisation.csv.gz", low_memory=False))
    climat = pd.read_csv(dossier / "climat_survey.csv.gz").drop(columns=["debut", "fin", "annee_saison"])
    sols = pd.read_csv(dossier / "sols_survey.csv.gz").drop(columns=["lieu", "nature_lieu"])
    relief = pd.read_csv(dossier / "relief_survey.csv.gz").drop(columns=["lieu", "nature_lieu"])
    table = _ajouter_variables(survey, "id_ligne", climat, sols, relief)
    return _position_survey(table, dossier)


def _position_survey(table, dossier):
    centroides = descripteurs_geographiques(gpd.read_file(dossier / "zones_survey.gpkg")).set_index("zone")
    zone = zone_survey(table)
    table["latitude"] = table["GPS_lat"].fillna(zone.map(centroides["latitude"]))
    table["longitude"] = table["GPS_lon"].fillna(zone.map(centroides["longitude"]))
    table["duree_saison"] = duree_saison(table["mois_semis"], table["mois_recolte"])
    table["Crop"] = table["Crop"].str.strip()
    return table


def table_cropcut(survey_partitionne, dossier=DOSSIER_TRAITE):
    """Retourne la table de validation externe de cropcut, avec les noms de colonnes de survey.

    La culture, le pays et l'année de récolte prennent les noms de survey, pour qu'un
    modèle entraîné sur survey puisse prédire directement.
    """
    cropcut = partitionner_cropcut(pd.read_csv(dossier / "cropcut_validation.csv.gz", low_memory=False),
                                   survey_partitionne)
    climat = pd.read_csv(dossier / "climat_cropcut.csv.gz").drop(columns=["debut", "fin", "annee_saison"])
    sols = pd.read_csv(dossier / "sols_cropcut.csv.gz").drop(columns=["lieu", "nature_lieu"])
    relief = pd.read_csv(dossier / "relief_cropcut.csv.gz").drop(columns=["lieu", "nature_lieu"])
    table = _ajouter_variables(cropcut, "id_mesure", climat, sols, relief)
    table = table.assign(annee_recolte=table["Year"])
    return _position_survey(table, dossier)
