"""Orchestration de la préparation des fichiers regional, survey et cropcut.

Exécution depuis la racine du projet avec la commande python -m src.data.prepare.
Le fichier point est exclu du périmètre, car il ne porte aucune des cibles retenues.
"""

from .cropcut import jeu_validation_cropcut, preparer_cropcut
from .load import DOSSIER_TRAITE, charger_brut
from .regional import jeu_modelisation_regional, preparer_regional
from .survey import jeu_modelisation_survey, preparer_survey


def preparer_tout(bruts=None):
    """Prépare les trois fichiers et retourne les tableaux produits par nom.

    Les tableaux bruts peuvent être fournis, sinon ils sont chargés. Ils ne sont
    jamais modifiés, chaque fonction travaillant sur une copie.
    """
    if bruts is None:
        bruts = {nom: charger_brut(nom) for nom in ["regional", "survey", "cropcut"]}

    regional, bornes = preparer_regional(bruts["regional"])
    survey = preparer_survey(bruts["survey"], bornes)
    cropcut = preparer_cropcut(bruts["cropcut"], bornes)

    return {
        "bornes_plausibilite": bornes,
        "regional_prepare": regional,
        "regional_modelisation": jeu_modelisation_regional(regional),
        "survey_prepare": survey,
        "survey_modelisation": jeu_modelisation_survey(survey),
        "cropcut_prepare": cropcut,
        "cropcut_validation": jeu_validation_cropcut(cropcut),
    }


def exporter(tableaux, dossier=DOSSIER_TRAITE):
    """Écrit chaque tableau au format CSV compressé dans le dossier des données traitées."""
    dossier.mkdir(parents=True, exist_ok=True)
    for nom, tableau in tableaux.items():
        avec_index = nom == "bornes_plausibilite"
        tableau.to_csv(dossier / f"{nom}.csv.gz", index=avec_index)


if __name__ == "__main__":
    tableaux = preparer_tout()
    exporter(tableaux)
    for nom, tableau in tableaux.items():
        print(f"{nom:<24} {tableau.shape[0]:>7} lignes")
