"""Exporte les ressources de l'application Streamlit dans app/ressources.

L'application ne relit ni les données brutes ni les sources géospatiales. Elle a
besoin du modèle retenu de regional, de sa description, des demi-largeurs de ses
intervalles, d'une table des variables de chaque ligne de regional et des scores de
test des deux modèles. Ces fichiers sont produits par la chaîne du projet, selon
docs/deployment.md, puis réunis ici.

Exécution depuis la racine du projet avec la commande python -m app.preparer.
"""

import json
import shutil
from pathlib import Path

import pandas as pd

from src.models.evaluation_finale import TESTS, VALIDATION_EXTERNE, scores
from src.models.experiences import DOSSIER_MODELES, charger_table
from src.models.incertitude import couverture
from src.models.prediction import largeurs_intervalles

DOSSIER_RESSOURCES = Path(__file__).parent / "ressources"
COLONNES_DESCRIPTIVES = ["GDAM_ID", "country", "admin_1", "admin_2", "level", "crop", "saison", "harvest_year",
                         "Source", "partition", "yieldTonHa"]


def exporter(dossier=DOSSIER_RESSOURCES):
    """Écrit le modèle, ses intervalles, la table des variables et les scores de test."""
    dossier.mkdir(parents=True, exist_ok=True)
    for nom in ["regional_modele.txt", "regional_modele.json"]:
        shutil.copy(DOSSIER_MODELES / nom, dossier / nom)
    largeurs_intervalles("regional").to_csv(dossier / "regional_intervalles.csv")

    description = json.loads((DOSSIER_MODELES / "regional_modele.json").read_text())
    variables = description["categorielles"] + description["numeriques"]
    table = charger_table("regional")
    colonnes = COLONNES_DESCRIPTIVES + [v for v in variables if v not in COLONNES_DESCRIPTIVES]
    exportee = table[colonnes].copy()
    exportee["admin_2"] = exportee["admin_2"].astype("string")
    exportee.reset_index(drop=True).to_parquet(dossier / "regional_variables.parquet", index=False)

    lignes = []
    for jeu, pays in [("regional", "country"), ("survey", "Country")]:
        evaluation = pd.read_csv(DOSSIER_MODELES / f"{jeu}_evaluation.csv.gz", low_memory=False)
        partitions = TESTS + ([VALIDATION_EXTERNE] if jeu == "survey" else [])
        tableau = scores(evaluation, pays, partitions)
        culture = "crop" if jeu == "regional" else "Crop"
        couvertures = couverture(evaluation, evaluation[culture], largeurs_intervalles(jeu))
        lignes.append(tableau.join(couvertures.drop(columns="lignes")).assign(modele=jeu))
    pd.concat(lignes).rename_axis("ensemble").reset_index().to_csv(dossier / "performance.csv", index=False)
    return {f.name: f.stat().st_size for f in sorted(dossier.iterdir())}


if __name__ == "__main__":
    for nom, octets in exporter().items():
        print(f"{nom:<28} {octets / 1e6:6.2f} Mo")
    print("Total", round(sum(f.stat().st_size for f in DOSSIER_RESSOURCES.iterdir()) / 1e6, 1), "Mo")
