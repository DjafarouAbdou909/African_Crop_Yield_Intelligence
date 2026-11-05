"""Prédictions des modèles retenus, avec leurs intervalles.

Ce module livre, pour chaque ligne d'une table de modélisation, le rendement prédit
et ses intervalles de prédiction à 80 et 90 %. Les modèles sont ceux qu'écrit
src/models/evaluation_finale.py, entraînés sur tout le développement. Les
demi-largeurs des intervalles sont calibrées une fois sur le développement, puis
écrites dans data/interim/modeles.

Une ligne nouvelle doit porter les mêmes variables que les tables de modélisation.
Pour une année postérieure à 2023, les séries climatiques doivent d'abord être
étendues, selon docs/deployment.md.

Exécution depuis la racine du projet avec la commande python -m src.models.prediction
regional, survey ou cropcut.
"""

import sys

import numpy as np
import pandas as pd

from src.data.load import DOSSIER_TRAITE

from .donnees import table_cropcut
from .evaluation_finale import charger_modele, predire
from .experiences import DOSSIER_MODELES, charger_table
from .incertitude import NIVEAUX, demi_largeurs, erreurs_calibration, intervalles

CLES = {
    "regional": ["GDAM_ID", "crop", "saison", "harvest_year", "country"],
    "survey": ["id_ligne", "Crop", "Country", "annee_recolte"],
    "cropcut": ["id_mesure", "Crop", "Country", "annee_recolte"],
}


def largeurs_intervalles(jeu, dossier=DOSSIER_MODELES):
    """Retourne les demi-largeurs des intervalles d'un jeu, en les calibrant à la première demande."""
    chemin = dossier / f"{jeu}_intervalles.csv"
    if not chemin.exists():
        table = charger_table(jeu)
        demi_largeurs(erreurs_calibration(jeu, table[table["partition"] == "developpement"])).to_csv(chemin)
    largeurs = pd.read_csv(chemin, index_col=0)
    largeurs.columns = [float(c) for c in largeurs.columns]
    return largeurs


def predire_avec_intervalles(jeu_modele, table, colonne_culture, dossier=DOSSIER_MODELES):
    """Retourne la prédiction et les bornes des intervalles pour chaque ligne d'une table."""
    modele, description = charger_modele(jeu_modele, dossier)
    largeurs = largeurs_intervalles(jeu_modele, dossier)
    prediction = predire(modele, description, table)
    resultat = pd.DataFrame({"rendement_predit_t_ha": prediction}, index=table.index)
    for niveau in NIVEAUX:
        bas, haut = intervalles(prediction, table[colonne_culture], largeurs, niveau)
        resultat[f"borne_basse_{niveau:.0%}"] = bas
        resultat[f"borne_haute_{niveau:.0%}"] = haut
    return resultat


def ecrire_predictions(jeu, dossier=DOSSIER_TRAITE):
    """Prédit toutes les lignes d'un jeu et écrit le résultat dans data/processed."""
    if jeu == "cropcut":
        table, jeu_modele, cible = table_cropcut(charger_table("survey")), "survey", "Yield_ton_ha_"
        partition = np.where(table["grappe_tenue_a_l_ecart"], "grappe_tenue_a_l_ecart", "grappe_vue")
    else:
        table, jeu_modele = charger_table(jeu), jeu
        cible = "yieldTonHa" if jeu == "regional" else "YieldUsingGPS_ton_ha_"
        partition = table["partition"]
    culture = "crop" if jeu == "regional" else "Crop"
    resultat = table[CLES[jeu]].assign(partition=partition, rendement_observe_t_ha=table[cible]).join(
        predire_avec_intervalles(jeu_modele, table, culture))
    resultat.to_csv(dossier / f"predictions_{jeu}.csv.gz", index=False)
    return resultat


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CLES:
        raise SystemExit("Usage python -m src.models.prediction regional|survey|cropcut")
    sortie = ecrire_predictions(sys.argv[1])
    print(f"predictions_{sys.argv[1]}.csv.gz : {len(sortie)} lignes")
