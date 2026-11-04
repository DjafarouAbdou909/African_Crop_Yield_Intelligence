"""Expériences de sélection des modèles, sur le seul développement.

Chaque expérience modifie un élément du modèle complet, la fonction de perte, une
famille de variables, les lignes d'entraînement ou la complexité des arbres. Les
ensembles de test ne sont jamais utilisés.

Trois schémas de validation sont employés.

- La validation croisée à cinq plis groupés du protocole mesure la prédiction de
  lieux jamais observés. Les années de ces lieux restent présentes ailleurs dans
  l'entraînement, ce qui permet au modèle d'apprendre le choc d'une année dans un
  pays à partir des autres régions du même pays.
- La validation temporelle interne entraîne sur les années anciennes du
  développement et évalue sur ses années récentes, sans information contemporaine.
  Pour regional, la coupure est 2012. Pour survey, la dernière vague de
  développement des pays qui en comptent au moins deux est évaluée.
- La validation spatio-temporelle interne croise les deux, pli par pli.

Les prédictions de chaque expérience sont écrites dans data/interim/modeles, une
colonne par nombre d'arbres, ce qui permet aux notebooks de les relire.

Exécution depuis la racine du projet avec la commande python -m src.models.experiences
regional ou survey.
"""

import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from src.data.load import DOSSIER_INTERMEDIAIRE
from src.evaluation.partitions import DEVELOPPEMENT, NOMBRE_PLIS
from src.evaluation.references import NIVEAUX_REGIONAL, NIVEAUX_SURVEY

from .apprentissage import PARAMETRES, decoupages_plis, predictions_hors_echantillon, reference_hors_echantillon
from .donnees import (
    CATEGORIELLES_REGIONAL,
    CATEGORIELLES_SURVEY,
    CIBLE_REGIONAL,
    CIBLE_SURVEY,
    NUMERIQUES_REGIONAL,
    NUMERIQUES_SURVEY,
    VARIABLES_CLIMAT,
    VARIABLES_RELIEF,
    VARIABLES_SOLS,
    table_regional,
    table_survey,
)

DOSSIER_MODELES = DOSSIER_INTERMEDIAIRE / "modeles"
ITERATIONS = 2000
PAS = 100
ANNEE_COUPURE_INTERNE_REGIONAL = 2012
SCHEMAS = ["croisee", "temporelle", "spatio_temporelle"]
VARIANTES_TEMPORELLES = ["complet", "sans_climat", "sans_sols_relief", "sans_pays", "sans_annee", "sans_source"]


def _sans(liste, retirees):
    return [v for v in liste if v not in retirees]


def experiences_regional():
    """Retourne les expériences de regional, chacune décrite par ses variables, paramètres et lignes."""
    cat, num = CATEGORIELLES_REGIONAL, NUMERIQUES_REGIONAL
    return {
        "complet": dict(categorielles=cat, numeriques=num),
        "perte_l2": dict(categorielles=cat, numeriques=num, parametres={"objective": "l2"}),
        "sans_climat": dict(categorielles=cat, numeriques=_sans(num, VARIABLES_CLIMAT)),
        "sans_sols_relief": dict(categorielles=cat, numeriques=_sans(num, VARIABLES_SOLS + VARIABLES_RELIEF)),
        "sans_source": dict(categorielles=_sans(cat, ["Source"]), numeriques=num),
        "sans_pays": dict(categorielles=_sans(cat, ["country"]), numeriques=num),
        "sans_annee": dict(categorielles=cat, numeriques=_sans(num, ["harvest_year"])),
        "entrainement_depuis_2001": dict(categorielles=cat, numeriques=num, depuis=2001),
        "feuilles_31": dict(categorielles=cat, numeriques=num, parametres={"num_leaves": 31}),
        "feuilles_127": dict(categorielles=cat, numeriques=num, parametres={"num_leaves": 127}),
        "feuilles_min_200": dict(categorielles=cat, numeriques=num, parametres={"min_data_in_leaf": 200}),
    }


def experiences_survey():
    """Retourne les expériences de survey."""
    cat, num = CATEGORIELLES_SURVEY, NUMERIQUES_SURVEY
    return {
        "complet": dict(categorielles=cat, numeriques=num),
        "perte_l2": dict(categorielles=cat, numeriques=num, parametres={"objective": "l2"}),
        "sans_climat": dict(categorielles=cat, numeriques=_sans(num, VARIABLES_CLIMAT)),
        "sans_sols_relief": dict(categorielles=cat, numeriques=_sans(num, VARIABLES_SOLS + VARIABLES_RELIEF)),
        "sans_pays": dict(categorielles=_sans(cat, ["Country"]), numeriques=num),
        "sans_annee": dict(categorielles=cat, numeriques=_sans(num, ["annee_recolte"])),
        "feuilles_31": dict(categorielles=cat, numeriques=num, parametres={"num_leaves": 31}),
        "feuilles_min_200": dict(categorielles=cat, numeriques=num, parametres={"min_data_in_leaf": 200}),
    }


JEUX = {
    "regional": (CIBLE_REGIONAL, NIVEAUX_REGIONAL, experiences_regional, "harvest_year", "country"),
    "survey": (CIBLE_SURVEY, NIVEAUX_SURVEY, experiences_survey, "annee_recolte", "Country"),
}


def charger_table(jeu):
    """Retourne la table de modélisation d'un jeu, restreinte aux lignes retenues."""
    if jeu == "regional":
        table, retenue = table_regional()
        return table[retenue]
    return table_survey()


def recent_interne(jeu, developpement):
    """Désigne les lignes récentes du développement, évaluées par la validation temporelle interne."""
    _, _, _, annee, pays = JEUX[jeu]
    if jeu == "regional":
        return developpement[annee] >= ANNEE_COUPURE_INTERNE_REGIONAL
    annees = developpement.groupby(pays)[annee]
    return (annees.transform("nunique") >= 2) & (developpement[annee] == annees.transform("max"))


def decoupages(jeu, schema, developpement, masque=None):
    """Retourne les découpages d'un schéma de validation sur le développement.

    masque restreint les lignes d'entraînement, sans changer les lignes évaluées.
    """
    if schema == "croisee":
        return decoupages_plis(developpement, masque)
    recent = recent_interne(jeu, developpement)
    ancien = ~recent if masque is None else ~recent & masque.reindex(developpement.index)
    if schema == "temporelle":
        return [(ancien, recent)]
    return [(ancien & (developpement["pli"] != pli), recent & (developpement["pli"] == pli)) for pli in range(NOMBRE_PLIS)]


def _executer(jeu, schema, nom, definition, dossier):
    cible, _, _, annee, _ = JEUX[jeu]
    table = charger_table(jeu)
    developpement = table[table["partition"] == DEVELOPPEMENT]
    masque = developpement[annee] >= definition["depuis"] if "depuis" in definition else None
    parametres = {**PARAMETRES, **definition.get("parametres", {})}
    predictions, _ = predictions_hors_echantillon(developpement, cible, definition["categorielles"],
                                                  definition["numeriques"], decoupages(jeu, schema, developpement, masque),
                                                  parametres, ITERATIONS, PAS)
    predictions.columns = [str(c) for c in predictions.columns]
    predictions.to_csv(dossier / f"{jeu}_{schema}_{nom}.csv.gz", index_label="index")
    return f"{schema} {nom}"


def lancer(jeu, dossier=DOSSIER_MODELES, processus=2):
    """Exécute les expériences absentes du dossier pour les trois schémas, avec leur référence.

    Les schémas temporels ne reprennent que les variantes de VARIANTES_TEMPORELLES.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    cible, niveaux, experiences, _, _ = JEUX[jeu]
    table = charger_table(jeu)
    developpement = table[table["partition"] == DEVELOPPEMENT]
    taches = []
    for schema in SCHEMAS:
        reference = reference_hors_echantillon(developpement, cible, niveaux, decoupages(jeu, schema, developpement))
        reference.rename("reference").to_csv(dossier / f"{jeu}_{schema}_reference.csv.gz", index_label="index")
        for nom, definition in experiences().items():
            retenue = schema == "croisee" or nom in VARIANTES_TEMPORELLES
            if retenue and not (dossier / f"{jeu}_{schema}_{nom}.csv.gz").exists():
                taches.append((schema, nom, definition))
    with ProcessPoolExecutor(processus) as executeur:
        for fait in executeur.map(_executer, [jeu] * len(taches), *zip(*taches), [dossier] * len(taches)):
            print(f"{jeu} {fait} terminé", flush=True)


def lire_experience(jeu, schema, nom, dossier=DOSSIER_MODELES):
    """Relit les prédictions d'une expérience, une colonne par nombre d'arbres, ou la référence."""
    predictions = pd.read_csv(dossier / f"{jeu}_{schema}_{nom}.csv.gz", index_col="index")
    if nom == "reference":
        return predictions["reference"]
    predictions.columns = [int(c) for c in predictions.columns]
    return predictions


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in JEUX:
        raise SystemExit("Usage python -m src.models.experiences regional|survey")
    lancer(sys.argv[1])
