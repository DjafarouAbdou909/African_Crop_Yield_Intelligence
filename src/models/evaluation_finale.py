"""Évaluation finale des modèles retenus sur les ensembles de test.

Chaque modèle retenu est entraîné une fois sur tout le développement, avec la
configuration figée dans src/models/selection.py, puis évalué sur les ensembles de
test du protocole. Le modèle de survey est aussi évalué sur cropcut, dont seules les
mesures des grappes tenues à l'écart constituent une validation indépendante. La
référence hiérarchique est entraînée sur le même développement.

Le modèle, ses modalités et ses prédictions sont écrits dans data/interim/modeles.

Exécution depuis la racine du projet avec la commande python -m src.models.evaluation_finale.
"""

import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.evaluation.metriques import metriques, metriques_par, moyenne_macro, score_competence
from src.evaluation.partitions import DEVELOPPEMENT, TEST_SPATIAL, TEST_SPATIO_TEMPOREL, TEST_TEMPOREL
from src.evaluation.references import NIVEAUX_SURVEY, reference_hierarchique

from .apprentissage import entrainer, matrice
from .donnees import CIBLE_CROPCUT, table_cropcut
from .experiences import DOSSIER_MODELES, JEUX, charger_table
from .selection import configuration_retenue

TESTS = [TEST_TEMPOREL, TEST_SPATIAL, TEST_SPATIO_TEMPOREL]
VALIDATION_EXTERNE = "cropcut_grappes_tenues_a_l_ecart"


def entrainer_retenu(jeu, table, dossier=DOSSIER_MODELES):
    """Entraîne le modèle retenu sur tout le développement et l'écrit avec ses modalités."""
    developpement = table[table["partition"] == DEVELOPPEMENT]
    categorielles, numeriques, parametres, iterations = configuration_retenue(jeu, developpement)
    x, categories = matrice(developpement, categorielles, numeriques)
    modele = entrainer(x, developpement[JEUX[jeu][0]], parametres, iterations)
    modele.save_model(str(dossier / f"{jeu}_modele.txt"))
    description = {"categorielles": categorielles, "numeriques": numeriques, "categories": categories,
                   "iterations": iterations, "parametres": parametres}
    (dossier / f"{jeu}_modele.json").write_text(json.dumps(description, ensure_ascii=False, indent=1))
    return modele, description


def charger_modele(jeu, dossier=DOSSIER_MODELES):
    """Relit un modèle retenu et sa description."""
    description = json.loads((dossier / f"{jeu}_modele.json").read_text())
    return lgb.Booster(model_file=str(dossier / f"{jeu}_modele.txt")), description


def predire(modele, description, table):
    """Prédit le rendement en tonnes par hectare."""
    x, _ = matrice(table, description["categorielles"], description["numeriques"], description["categories"])
    return pd.Series(np.exp(modele.predict(x)), index=table.index)


def evaluer(jeu, dossier=DOSSIER_MODELES):
    """Entraîne le modèle retenu, prédit les ensembles de test et écrit les prédictions.

    Retourne une table avec la partition, la cible, la prédiction du modèle et celle de
    la référence. Pour survey, les mesures de cropcut sont ajoutées, la partition
    distinguant les grappes tenues à l'écart. L'index reprend celui de la table
    d'origine, que la colonne origine désigne, car les index de survey et de cropcut
    se recouvrent.
    """
    cible, niveaux = JEUX[jeu][0], JEUX[jeu][1]
    table = charger_table(jeu)
    developpement = table[table["partition"] == DEVELOPPEMENT]
    modele, description = entrainer_retenu(jeu, table, dossier)
    tests = table[table["partition"].isin(TESTS)].copy()
    tests["prediction"] = predire(modele, description, tests)
    tests["reference"] = reference_hierarchique(developpement, tests, cible, niveaux)[0]
    tests["reel"] = tests[cible]
    tests["origine"] = jeu
    morceaux = [tests]
    if jeu == "survey":
        cropcut = table_cropcut(table)
        cropcut["prediction"] = predire(modele, description, cropcut)
        cropcut["reference"] = reference_hierarchique(developpement, cropcut, cible, NIVEAUX_SURVEY)[0]
        cropcut["reel"] = cropcut[CIBLE_CROPCUT]
        cropcut["partition"] = np.where(cropcut["grappe_tenue_a_l_ecart"], VALIDATION_EXTERNE, "cropcut_grappes_vues")
        cropcut["origine"] = "cropcut"
        morceaux.append(cropcut)
    resultat = pd.concat(morceaux, ignore_index=False)
    resultat.to_csv(dossier / f"{jeu}_evaluation.csv.gz", index_label="index")
    return resultat


def scores(evaluation, pays, partitions):
    """Retourne les métriques du modèle et de la référence par partition, avec la compétence."""
    lignes = {}
    for partition in partitions:
        sous = evaluation[evaluation["partition"] == partition]
        if sous.empty:
            continue
        modele = metriques(sous["reel"], sous["prediction"])
        reference = metriques(sous["reel"], sous["reference"])
        lignes[partition] = {
            "lignes": modele["n"], "mae_log": modele["mae_log"], "mae_log_reference": reference["mae_log"],
            "competence": score_competence(modele["mae_log"], reference["mae_log"]),
            "mae_log_macro_pays": moyenne_macro(metriques_par(sous, pays, "reel", "prediction")),
            "mae_log_macro_pays_reference": moyenne_macro(metriques_par(sous, pays, "reel", "reference")),
            "biais_log": modele["biais_log"], "biais_log_reference": reference["biais_log"], "r2": modele["r2"],
            "mae_t_ha": modele["mae"], "erreur_relative_typique": modele["erreur_relative_typique"],
        }
    return pd.DataFrame(lignes).T


def ventilation(evaluation, cle):
    """Retourne l'erreur du modèle et de la référence pour chaque modalité d'une clé, par partition."""
    resultat = evaluation.assign(
        erreur=np.abs(np.log(evaluation["prediction"]) - np.log(evaluation["reel"])),
        erreur_reference=np.abs(np.log(evaluation["reference"]) - np.log(evaluation["reel"])),
        biais=np.log(evaluation["prediction"]) - np.log(evaluation["reel"]),
    ).groupby(["partition", cle], dropna=False).agg(
        lignes=("erreur", "size"), mae_log=("erreur", "mean"), mae_log_reference=("erreur_reference", "mean"),
        biais_log=("biais", "mean"))
    resultat["competence"] = 1 - resultat["mae_log"] / resultat["mae_log_reference"]
    return resultat


if __name__ == "__main__":
    for jeu in JEUX:
        evaluation = evaluer(jeu)
        partitions = TESTS + ([VALIDATION_EXTERNE] if jeu == "survey" else [])
        print(jeu)
        print(scores(evaluation, JEUX[jeu][4], partitions).round(3).to_string())
