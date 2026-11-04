"""Assemblage des variables climatiques de saison pour regional et survey.

Chaque ligne reçoit un lieu, un calendrier, une fenêtre de saison et les indicateurs
de cette fenêtre. Les indicateurs sont calculés une seule fois par couple de lieu et
de fenêtre, puis rattachés aux lignes. La clé de regional est le quadruplet GDAM_ID,
crop, saison et harvest_year, unique dans regional_modelisation, et celle de survey
est id_ligne.

Exécution depuis la racine du projet avec la commande python -m src.features.variables.
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from src.data.load import DOSSIER_TRAITE

from .agregation import indicateurs_lieux
from .calendrier import attribuer_calendrier, calendriers_harveststat, fenetre_saison
from .climat import DOSSIER_MAGASIN, ouvrir_magasin
from .geographie import descripteurs_geographiques, zone_survey
from .lieux import lieu_survey, poids_regional, poids_survey

CLE_REGIONAL = ["GDAM_ID", "crop", "saison", "harvest_year"]
# Pays dont l'année de récolte HarvestStat désigne l'année de semis, d'après les tests
# fondés sur la température et sur la pluie de la saison. Les autres sources ne sont pas
# concernées, faute de test.
DECALAGE_ANNEE_REGIONAL = {"Lesotho": 1}
# Pays dont l'enquête porte sur la saison récoltée l'année AgYearStart, même lorsque le
# calendrier de la zone chevauche deux années civiles.
RECOLTE_ANNEE_DEBUT_SURVEY = {"Tanzania"}


def annee_recolte_survey(debut_campagne, mois_semis, mois_recolte, pays=None):
    """Retourne l'année civile de récolte d'une parcelle d'enquête.

    La campagne commence avec le semis de l'année AgYearStart. La récolte a lieu la même
    année lorsque la saison tient dans l'année civile, et l'année suivante lorsqu'elle
    la chevauche. Dans les pays de RECOLTE_ANNEE_DEBUT_SURVEY, la récolte a lieu l'année
    AgYearStart.
    """
    semis = np.asarray(mois_semis, dtype=float)
    chevauche = semis > np.asarray(mois_recolte, dtype=float)
    if pays is not None:
        chevauche &= ~pd.Series(pays).isin(RECOLTE_ANNEE_DEBUT_SURVEY).to_numpy()
    annee = pd.Series(debut_campagne, dtype="Float64").to_numpy(dtype=float) + chevauche
    return pd.array(np.where(np.isnan(semis), np.nan, annee), dtype="Int64")


def fenetres_regional(regional, tables, geographie):
    """Retourne le lieu, le calendrier et la fenêtre de saison de chaque ligne de regional.

    La fenêtre s'achève l'année de récolte, sauf pour les lignes HarvestStat des pays de
    DECALAGE_ANNEE_REGIONAL.
    """
    centroides = geographie.set_index("zone")
    calendrier = attribuer_calendrier(
        regional, tables, {"zone": "GDAM_ID", "niveau_1": "L1_GID", "pays": "L0_GID"}, "crop",
        regional["GDAM_ID"].map(centroides["latitude"]), regional["GDAM_ID"].map(centroides["longitude"]),
    )
    decalage = regional["country"].map(DECALAGE_ANNEE_REGIONAL).fillna(0).astype(int)
    annee = regional["harvest_year"] + decalage.where(regional["Source"] == "HarvestStat", 0)
    debut, fin = fenetre_saison(annee, calendrier["mois_semis"], calendrier["mois_recolte"])
    return pd.concat([regional[CLE_REGIONAL], calendrier], axis=1).assign(
        annee_saison=annee.to_numpy(),
        lieu=regional["GDAM_ID"].to_numpy(), debut=debut, fin=fin,
    )


def fenetres_survey(survey, tables, zones_survey):
    """Retourne le lieu, le calendrier et la fenêtre de saison de chaque parcelle de survey.

    Le calendrier GGCMI est lu aux coordonnées de la grappe lorsqu'elles existent, sinon
    au centroïde de la zone de repli.
    """
    zone = zone_survey(survey)
    centroides = descripteurs_geographiques(zones_survey).set_index("zone")
    calendrier = attribuer_calendrier(
        survey.assign(zone=zone, crop=survey["Crop"].str.strip()), tables,
        {"zone": "zone", "niveau_1": "L1_GID", "pays": "L0_GID"}, "crop",
        survey["GPS_lat"].fillna(zone.map(centroides["latitude"])),
        survey["GPS_lon"].fillna(zone.map(centroides["longitude"])),
    )
    lieu, nature = lieu_survey(survey)
    annee = annee_recolte_survey(survey["AgYearStart"], calendrier["mois_semis"], calendrier["mois_recolte"],
                                 survey["Country"])
    debut, fin = fenetre_saison(annee, calendrier["mois_semis"], calendrier["mois_recolte"])
    return pd.concat([survey[["id_ligne"]], calendrier], axis=1).assign(
        lieu=lieu, nature_lieu=nature, annee_saison=annee, debut=debut, fin=fin
    )


def rattacher_indicateurs(fenetres, poids, magasin=DOSSIER_MAGASIN):
    """Calcule les indicateurs des fenêtres distinctes et les rattache à chaque ligne."""
    distinctes = fenetres.dropna(subset=["lieu", "debut", "fin"]).drop_duplicates(["lieu", "debut", "fin"])
    indicateurs = indicateurs_lieux(poids, distinctes[["lieu", "debut", "fin"]], magasin)
    return fenetres.merge(indicateurs, on=["lieu", "debut", "fin"], how="left")


def construire(dossier=DOSSIER_TRAITE, magasin=DOSSIER_MAGASIN):
    """Construit et écrit les variables climatiques de saison de regional et de survey.

    Les poids des mailles de chaque lieu sont recalculés et écrits dans le magasin.
    """
    regional = pd.read_csv(dossier / "regional_modelisation.csv.gz", low_memory=False)
    survey = pd.read_csv(dossier / "survey_modelisation.csv.gz", low_memory=False)
    zones_survey = gpd.read_file(dossier / "zones_survey.gpkg")
    mailles, _, _ = ouvrir_magasin("power", magasin)
    tables = calendriers_harveststat(regional)

    poids = poids_regional(gpd.read_file(dossier / "zones_regional.gpkg"), mailles)
    poids.to_csv(magasin / "poids_regional.csv", index=False)
    fenetres = fenetres_regional(regional, tables, pd.read_csv(dossier / "geographie_regional.csv.gz"))
    climat_regional = rattacher_indicateurs(fenetres, poids, magasin)
    climat_regional.to_csv(dossier / "climat_regional.csv.gz", index=False)

    poids = poids_survey(survey, zones_survey, mailles)
    poids.to_csv(magasin / "poids_survey.csv", index=False)
    fenetres = fenetres_survey(survey, tables, zones_survey)
    climat_survey = rattacher_indicateurs(fenetres, poids, magasin)
    climat_survey.to_csv(dossier / "climat_survey.csv.gz", index=False)
    return climat_regional, climat_survey


if __name__ == "__main__":
    for nom, tableau in zip(["climat_regional", "climat_survey"], construire()):
        print(f"{nom:<16} {tableau.shape[0]:>7} lignes {tableau.shape[1]:>3} colonnes")
