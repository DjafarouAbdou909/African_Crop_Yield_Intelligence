"""Variables explicatives des mesures de cropcut.

Les mesures de cropcut proviennent des grappes de l'enquête éthiopienne de survey.
Chaque mesure reçoit les variables qu'aurait une parcelle de survey de même grappe,
de même culture et de même vague, avec les mêmes règles de lieu, de calendrier et
d'année. La vague dont l'année Year vaut A + 1 commence en A, comme la campagne
AgYearStart de survey.

Les dates de coupe suivent le calendrier éthiopien, qui compte douze mois de 30 jours
et un treizième mois de 5 ou 6 jours. Elles sont converties en dates grégoriennes
pour contrôler la saison mesurée.

Exécution depuis la racine du projet avec la commande python -m src.features.variables_cropcut.
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from src.data.load import DOSSIER_TRAITE

from . import relief, sols
from .calendrier import calendriers_harveststat
from .climat import DOSSIER_MAGASIN, ouvrir_magasin
from .geographie import zone_survey
from .lieux import geometries_lieux_survey, lieu_survey, poids_survey
from .variables import fenetres_survey, rattacher_indicateurs


def cropcut_comme_survey(cropcut):
    """Retourne cropcut avec les colonnes de survey qu'utilisent les variables explicatives."""
    return cropcut.assign(AgYearStart=cropcut["Year"] - 1, id_ligne=cropcut["id_mesure"])


def date_calendrier_ethiopien(annee_debut, mois, jour):
    """Convertit une date du calendrier éthiopien en date grégorienne.

    annee_debut est l'année grégorienne au cours de laquelle commence l'année
    éthiopienne. Celle-ci commence le 11 septembre, ou le 12 septembre lorsque l'année
    grégorienne suivante est bissextile. La règle vaut de 1901 à 2099.
    """
    annee = pd.Series(annee_debut, dtype="Float64").to_numpy(dtype=float)
    debut = pd.to_datetime(
        pd.DataFrame({"year": annee, "month": 9, "day": np.where((annee + 1) % 4 == 0, 12, 11)}), errors="coerce"
    )
    ecart = 30 * (np.asarray(mois, dtype=float) - 1) + np.asarray(jour, dtype=float) - 1
    return debut + pd.to_timedelta(ecart, unit="D")


def construire(dossier=DOSSIER_TRAITE, magasin=DOSSIER_MAGASIN):
    """Construit et écrit les variables climatiques, de sol et de relief de cropcut, par mesure."""
    cropcut = cropcut_comme_survey(pd.read_csv(dossier / "cropcut_validation.csv.gz", low_memory=False))
    regional = pd.read_csv(dossier / "regional_modelisation.csv.gz", low_memory=False)
    zones_survey = gpd.read_file(dossier / "zones_survey.gpkg")
    zones = zones_survey[zones_survey["zone"].isin(zone_survey(cropcut))]
    mailles, _, _ = ouvrir_magasin("power", magasin)

    poids = poids_survey(cropcut, zones, mailles)
    fenetres = fenetres_survey(cropcut, calendriers_harveststat(regional), zones)
    climat = rattacher_indicateurs(fenetres, poids, magasin).rename(columns={"id_ligne": "id_mesure"})
    climat.to_csv(dossier / "climat_cropcut.csv.gz", index=False)

    lieux = geometries_lieux_survey(cropcut, zones)
    lieu, nature = lieu_survey(cropcut)
    base = pd.DataFrame({"id_mesure": cropcut["id_mesure"], "lieu": lieu, "nature_lieu": nature})
    sorties = [climat]
    for nom, module in [("sols", sols), ("relief", relief)]:
        tableau = base.merge(module.variables_lieux(lieux), on="lieu", how="left")
        tableau.to_csv(dossier / f"{nom}_cropcut.csv.gz", index=False)
        sorties.append(tableau)
    return sorties


if __name__ == "__main__":
    for nom, tableau in zip(["climat_cropcut", "sols_cropcut", "relief_cropcut"], construire()):
        print(f"{nom:<15} {tableau.shape[0]:>7} lignes {tableau.shape[1]:>3} colonnes")
