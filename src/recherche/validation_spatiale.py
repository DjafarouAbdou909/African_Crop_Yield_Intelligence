"""Validation par blocs géographiques du modèle retenu de regional.

Ce module met en œuvre le plan préenregistré de docs/research_spatial_blocks.md. Il
compare la validation croisée groupée du protocole à trois schémas qui éloignent les
régions évaluées des régions d'entraînement, un pays tenu à l'écart, des blocs
géographiques et des blocs entourés d'une zone tampon. Seul le développement est
utilisé, et le modèle retenu n'est pas réajusté.

Exécution depuis la racine du projet avec la commande python -m src.recherche.validation_spatiale.
"""

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.data.load import DOSSIER_INTERMEDIAIRE
from src.evaluation.partitions import DEVELOPPEMENT
from src.evaluation.references import NIVEAUX_REGIONAL
from src.models.apprentissage import predictions_hors_echantillon, reference_hors_echantillon
from src.models.experiences import charger_table, lire_experience
from src.models.selection import configuration_retenue

CIBLE = "yieldTonHa"
NOMBRE_BLOCS = 8
RAYON_TAMPON_KM = 250.0
GRAINE_BLOCS = 20261112
RAYON_TERRE_KM = 6371.0088
SCHEMAS = ["S0", "S1", "S2", "S3"]
DOSSIER_RECHERCHE = DOSSIER_INTERMEDIAIRE / "recherche"


def developpement_regional():
    """Retourne les lignes du développement de regional retenues pour la modélisation."""
    table = charger_table("regional")
    return table[table["partition"] == DEVELOPPEMENT]


def zones(developpement):
    """Retourne une ligne par zone avec son pays et les coordonnées de son centroïde."""
    return developpement.groupby("GDAM_ID").agg(country=("country", "first"), latitude=("latitude", "first"),
                                                longitude=("longitude", "first"))


def cartesiennes(latitudes, longitudes):
    """Convertit des coordonnées géographiques en points de la sphère unité."""
    phi, lam = np.radians(np.asarray(latitudes, float)), np.radians(np.asarray(longitudes, float))
    return np.column_stack([np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])


def distances_km(points_a, points_b):
    """Retourne la matrice des distances de grand cercle entre deux ensembles de points de la sphère unité."""
    produit = np.clip(points_a @ points_b.T, -1.0, 1.0)
    return RAYON_TERRE_KM * np.arccos(produit)


def blocs_geographiques(table_zones, nombre=NOMBRE_BLOCS, graine=GRAINE_BLOCS):
    """Regroupe les zones en blocs par les k-moyennes sur leurs coordonnées cartésiennes."""
    points = cartesiennes(table_zones["latitude"], table_zones["longitude"])
    etiquettes = KMeans(n_clusters=nombre, n_init=20, random_state=graine).fit_predict(points)
    return pd.Series(etiquettes, index=table_zones.index, name="bloc")


def decoupages(developpement, schema):
    """Retourne les couples de masques d'entraînement et d'évaluation d'un schéma S1, S2 ou S3."""
    table_zones = zones(developpement)
    if schema == "S1":
        return [(developpement["country"] != pays, developpement["country"] == pays)
                for pays in sorted(developpement["country"].unique())]
    blocs = blocs_geographiques(table_zones)
    bloc_ligne = developpement["GDAM_ID"].map(blocs)
    points = cartesiennes(table_zones["latitude"], table_zones["longitude"])
    resultat = []
    for bloc in range(NOMBRE_BLOCS):
        evaluation = bloc_ligne == bloc
        apprentissage = ~evaluation
        if schema == "S3":
            dans_bloc = (blocs == bloc).to_numpy()
            proximite = distances_km(points, points[dans_bloc]).min(axis=1)
            trop_proches = pd.Series(proximite < RAYON_TAMPON_KM, index=table_zones.index)
            apprentissage &= ~developpement["GDAM_ID"].map(trop_proches).to_numpy()
        resultat.append((apprentissage, evaluation))
    return resultat


def distance_a_l_entrainement(developpement, decoupes):
    """Retourne, pour chaque ligne évaluée, la distance en km de sa zone à la zone d'entraînement la plus proche."""
    table_zones = zones(developpement)
    points = pd.DataFrame(cartesiennes(table_zones["latitude"], table_zones["longitude"]), index=table_zones.index)
    distance = pd.Series(np.nan, index=developpement.index)
    for apprentissage, evaluation in decoupes:
        zones_evaluees = developpement.loc[evaluation, "GDAM_ID"].unique()
        zones_apprises = developpement.loc[apprentissage, "GDAM_ID"].unique()
        minimum = distances_km(points.loc[zones_evaluees].to_numpy(), points.loc[zones_apprises].to_numpy()).min(axis=1)
        distance[evaluation] = developpement.loc[evaluation, "GDAM_ID"].map(pd.Series(minimum, index=zones_evaluees))
    return distance


def _executer(schema, dossier):
    developpement = developpement_regional()
    categorielles, numeriques, parametres, iterations = configuration_retenue("regional", developpement)
    decoupes = decoupages(developpement, schema)
    predictions, _ = predictions_hors_echantillon(developpement, CIBLE, categorielles, numeriques, decoupes,
                                                  parametres, iterations, iterations)
    resultat = pd.DataFrame({
        "prediction": predictions[iterations],
        "reference": reference_hors_echantillon(developpement, CIBLE, NIVEAUX_REGIONAL, decoupes),
        "distance_km": distance_a_l_entrainement(developpement, decoupes),
    })
    resultat.to_csv(dossier / f"blocs_{schema}.csv.gz", index_label="index")
    return schema


def predictions_s0(developpement):
    """Retourne les prédictions hors pli de la validation croisée du protocole, déjà calculées."""
    _, _, _, iterations = configuration_retenue("regional", developpement)
    return pd.DataFrame({
        "prediction": lire_experience("regional", "croisee", "complet")[iterations],
        "reference": lire_experience("regional", "croisee", "reference"),
    }).reindex(developpement.index)


def lancer(dossier=DOSSIER_RECHERCHE, processus=2):
    """Calcule les schémas S1, S2 et S3 absents du dossier."""
    dossier.mkdir(parents=True, exist_ok=True)
    a_faire = [s for s in ["S1", "S2", "S3"] if not (dossier / f"blocs_{s}.csv.gz").exists()]
    with ProcessPoolExecutor(processus) as executeur:
        for fait in executeur.map(_executer, a_faire, [dossier] * len(a_faire)):
            print(f"schéma {fait} terminé", flush=True)


def lire_schema(schema, developpement, dossier=DOSSIER_RECHERCHE):
    """Relit les prédictions d'un schéma, alignées sur le développement."""
    if schema == "S0":
        return predictions_s0(developpement)
    return pd.read_csv(dossier / f"blocs_{schema}.csv.gz", index_col="index").reindex(developpement.index)


def erreurs(developpement, predictions):
    """Retourne l'erreur absolue sur le logarithme du modèle et de la référence."""
    log_reel = np.log(developpement[CIBLE])
    return (np.abs(np.log(predictions["prediction"]) - log_reel), np.abs(np.log(predictions["reference"]) - log_reel))


def bilan(developpement, dossier=DOSSIER_RECHERCHE):
    """Retourne l'erreur, la compétence et l'écart à S0 de chaque schéma, avec un intervalle bootstrap par pays."""
    from src.models.bilan import intervalle_bootstrap

    erreur_s0, _ = erreurs(developpement, lire_schema("S0", developpement, dossier))
    lignes = []
    for schema in SCHEMAS:
        modele, reference = erreurs(developpement, lire_schema(schema, developpement, dossier))
        bas, haut = intervalle_bootstrap(modele - erreur_s0, developpement["country"])
        lignes.append({"schema": schema, "lignes": int(modele.notna().sum()), "mae_log": modele.mean(),
                       "mae_log_reference": reference.mean(), "competence": 1 - modele.mean() / reference.mean(),
                       "ecart_a_S0": (modele - erreur_s0).mean(), "ic_bas": bas, "ic_haut": haut})
    return pd.DataFrame(lignes)


if __name__ == "__main__":
    lancer()
