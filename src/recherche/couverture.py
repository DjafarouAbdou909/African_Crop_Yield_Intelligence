"""Couverture des intervalles conformes sous changement de distribution.

Ce module met en œuvre le plan préenregistré de docs/research_conformal_shift.md. Il
construit le banc d'essai interne au développement, les cinq méthodes M0 à M4 et
leurs métriques. Aucune fonction ne lit les ensembles de test, à l'exception de
l'évaluation finale, réservée à la section 9 du plan.
"""

import hashlib
from functools import lru_cache

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.evaluation.partitions import DEVELOPPEMENT
from src.models.apprentissage import matrice
from src.models.experiences import JEUX, charger_table, lire_experience, recent_interne
from src.models.selection import VARIANTES_RETENUES, configuration_retenue

NIVEAUX = [0.8, 0.9]
MINIMUM = 200
METHODES = ["M0", "M1", "M2", "M3", "M4"]
CONDITIONS = ["spatiale", "temporelle", "spatio_temporelle"]
PARAMETRES_DIFFICULTE = {
    "objective": "l2", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 100, "feature_fraction": 0.8,
    "bagging_fraction": 0.8, "bagging_freq": 1, "verbose": -1, "num_threads": 4, "deterministic": True, "seed": 7,
}
ITERATIONS_DIFFICULTE = 300
PLANCHER_DIFFICULTE = 0.05


def colonnes(jeu):
    """Retourne les noms des colonnes de culture et de pays d'un jeu."""
    return ("crop", "country") if jeu == "regional" else ("Crop", "Country")


def quantile_conforme(valeurs, niveau):
    """Retourne le quantile conforme, de rang plafond de n plus un fois le niveau."""
    valeurs = np.sort(np.asarray(valeurs, dtype=float))
    rang = int(np.ceil((len(valeurs) + 1) * niveau)) - 1
    return valeurs[min(rang, len(valeurs) - 1)] if len(valeurs) else np.nan


def moitie(groupes):
    """Répartit les groupes en deux moitiés stables, selon l'empreinte de leur identifiant."""
    return pd.Series(groupes).astype(str).map(
        lambda g: int(hashlib.sha256(f"moitie|{g}".encode()).hexdigest()[:8], 16) % 2 == 0).to_numpy()


@lru_cache(maxsize=2)
def _table_et_configuration(jeu):
    """Charge une seule fois la table d'un jeu et la configuration de son modèle retenu."""
    table = charger_table(jeu)
    return table, configuration_retenue(jeu, table[table["partition"] == DEVELOPPEMENT])


def erreurs_banc(jeu):
    """Retourne les lignes du banc d'essai interne avec leur erreur, leur rôle et leurs variables.

    La colonne role vaut calibration, ou le nom de la condition évaluée. Une ligne
    ancienne apparaît deux fois, comme calibration de toutes les conditions et comme
    ligne de la condition spatiale si son pli vaut 3 ou 4.
    """
    cible = JEUX[jeu][0]
    table, (_, _, _, palier) = _table_et_configuration(jeu)
    developpement = table[table["partition"] == DEVELOPPEMENT]
    recent = recent_interne(jeu, developpement)
    morceaux = []
    for schema in ["croisee", "temporelle", "spatio_temporelle"]:
        prediction = lire_experience(jeu, schema, VARIANTES_RETENUES[jeu])[palier]
        lignes = developpement.loc[prediction.index].assign(
            prediction=prediction, erreur=np.abs(np.log(prediction) - np.log(developpement.loc[prediction.index, cible])))
        if schema == "croisee":
            anciennes = lignes[~recent.reindex(lignes.index).to_numpy()]
            morceaux.append(anciennes.assign(role="calibration"))
            morceaux.append(anciennes[anciennes["pli"].isin([3, 4])].assign(role="spatiale"))
        else:
            morceaux.append(lignes[recent.reindex(lignes.index).to_numpy()].assign(role=schema))
    return pd.concat(morceaux)


def _mondrian(calibration, evaluation, cles, niveau, minimum=MINIMUM):
    """Demi-largeur hiérarchique, du niveau de clés le plus fin qui compte assez d'erreurs.

    cles va du niveau le plus grossier au plus fin, et chaque niveau remplace le précédent
    là où il compte au moins minimum erreurs. L'ensemble sert de repli.
    """
    demi = pd.Series(quantile_conforme(calibration["erreur"], niveau), index=evaluation.index)
    for cle in cles:
        comptes = calibration.groupby(cle)["erreur"].size()
        quantiles = calibration.groupby(cle)["erreur"].apply(lambda e: quantile_conforme(e, niveau))
        quantiles = quantiles[comptes >= minimum]
        valeurs = evaluation.set_index(cle).index.map(quantiles)
        valeurs = pd.Series(np.asarray(valeurs, dtype=float), index=evaluation.index)
        demi = valeurs.fillna(demi)
    return demi


def demi_largeurs(jeu, methode, calibration, evaluation, niveau):
    """Retourne la demi-largeur sur le logarithme de chaque ligne évaluée, pour une méthode."""
    culture, pays = colonnes(jeu)
    if methode == "M0":
        return _mondrian(calibration, evaluation, [[culture]], niveau)
    if methode == "M1":
        return pd.Series(quantile_conforme(calibration["erreur"], niveau), index=evaluation.index)
    if methode == "M2":
        return _mondrian(calibration, evaluation, [[pays]], niveau)
    if methode == "M3":
        return _mondrian(calibration, evaluation, [[pays], [pays, culture]], niveau)
    if methode == "M4":
        return _normalisee(jeu, calibration, evaluation, [niveau])[niveau]
    raise ValueError(f"Méthode inconnue {methode}")


def _normalisee(jeu, calibration, evaluation, niveaux):
    """Conformité normalisée par une difficulté estimée sur une moitié des groupes de calibration.

    Le modèle de difficulté ne dépend pas du niveau. Il est entraîné une fois, et le
    quantile des erreurs normalisées est calculé pour chaque niveau.
    """
    _, (categorielles, numeriques, _, _) = _table_et_configuration(jeu)
    apprentissage = moitie(calibration["groupe"])
    x, categories = matrice(calibration, categorielles, numeriques)
    donnees = lgb.Dataset(x[apprentissage], label=calibration.loc[apprentissage, "erreur"].to_numpy(),
                          categorical_feature=categorielles)
    modele = lgb.train(PARAMETRES_DIFFICULTE, donnees, num_boost_round=ITERATIONS_DIFFICULTE)
    difficulte_calibration = np.maximum(modele.predict(x[~apprentissage]), PLANCHER_DIFFICULTE)
    normalisees = calibration.loc[~apprentissage, "erreur"].to_numpy() / difficulte_calibration
    x_evaluation, _ = matrice(evaluation, categorielles, numeriques, categories)
    difficulte = np.maximum(modele.predict(x_evaluation), PLANCHER_DIFFICULTE)
    return {n: pd.Series(quantile_conforme(normalisees, n) * difficulte, index=evaluation.index) for n in niveaux}


def metriques_couverture(jeu, evaluation, demi, niveau, minimum=MINIMUM):
    """Retourne la couverture marginale, celle du pire pays, l'écart moyen par pays et la largeur médiane."""
    _, pays = colonnes(jeu)
    dedans = pd.Series(evaluation["erreur"].to_numpy() <= demi.to_numpy(), index=evaluation.index)
    par_pays = dedans.groupby(evaluation[pays]).agg(["mean", "size"])
    par_pays = par_pays[par_pays["size"] >= minimum]
    return {
        "couverture": dedans.mean(), "pire_pays": par_pays["mean"].min(),
        "pire_pays_nom": par_pays["mean"].idxmin(), "ecart_moyen_pays": (par_pays["mean"] - niveau).abs().mean(),
        "largeur_mediane": float(np.median(np.exp(2 * demi))), "pays_evalues": len(par_pays),
    }


def couverture_par_ligne(evaluation, demi):
    """Indique, pour chaque ligne évaluée, si son erreur tombe dans son intervalle."""
    return (evaluation["erreur"].to_numpy() <= demi.to_numpy()).astype(float)


def evaluer_banc(jeu, banc=None):
    """Évalue les cinq méthodes dans les trois conditions du banc d'essai interne, à chaque niveau.

    Retourne le tableau des métriques et les couvertures ligne par ligne, utiles au bootstrap.
    """
    banc = erreurs_banc(jeu) if banc is None else banc
    calibration_complete = banc[banc["role"] == "calibration"]
    lignes, detail = [], {}
    for condition in CONDITIONS:
        evaluation = banc[banc["role"] == condition]
        calibration = (calibration_complete[calibration_complete["pli"].isin([0, 1, 2])] if condition == "spatiale"
                       else calibration_complete)
        normalisees = _normalisee(jeu, calibration, evaluation, NIVEAUX)
        for methode in METHODES:
            for niveau in NIVEAUX:
                demi = (normalisees[niveau] if methode == "M4"
                        else demi_largeurs(jeu, methode, calibration, evaluation, niveau))
                lignes.append({"jeu": jeu, "condition": condition, "methode": methode, "niveau": niveau,
                               "lignes": len(evaluation), **metriques_couverture(jeu, evaluation, demi, niveau)})
                detail[(condition, methode, niveau)] = couverture_par_ligne(evaluation, demi)
    return pd.DataFrame(lignes), detail, banc


def decider(resultats, niveau=0.8, tolerance=0.01, egalite=0.01):
    """Applique la règle de décision de la section 8 du plan à un jeu."""
    sous = resultats[resultats["niveau"] == niveau]
    marge = sous.groupby("methode")["couverture"].min() >= niveau - tolerance
    ecart = sous.groupby("methode")["ecart_moyen_pays"].mean()
    largeur = sous.groupby("methode")["largeur_mediane"].mean()
    admissibles = marge[marge].index
    if len(admissibles) == 0:
        return sous.groupby("methode")["couverture"].min().idxmax(), False
    candidats = ecart[admissibles]
    proches = candidats[candidats <= candidats.min() + egalite].index
    return largeur[proches].idxmin(), True


# Choix issus de la règle de décision de la section 8 du plan, appliquée au banc d'essai
# interne et figés avant l'évaluation finale. Pour regional, aucune méthode n'atteint la
# couverture marginale requise dans les trois conditions. La règle de repli retient la
# méthode dont la couverture marginale minimale est la plus élevée, et l'échec est rapporté.
METHODES_RETENUES = {"regional": "M0", "survey": "M4"}
CRITERE_REMPLI = {"regional": False, "survey": True}


def calibration_finale(jeu):
    """Retourne les erreurs hors échantillon des trois validations internes, avec les variables des lignes."""
    cible = JEUX[jeu][0]
    table, (_, _, _, palier) = _table_et_configuration(jeu)
    developpement = table[table["partition"] == DEVELOPPEMENT]
    morceaux = []
    for schema in ["croisee", "temporelle", "spatio_temporelle"]:
        prediction = lire_experience(jeu, schema, VARIANTES_RETENUES[jeu])[palier]
        lignes = developpement.loc[prediction.index]
        morceaux.append(lignes.assign(schema=schema, erreur=np.abs(np.log(prediction) - np.log(lignes[cible]))))
    return pd.concat(morceaux)


def evaluation_finale(jeu, dossier=None):
    """Évalue une seule fois les cinq méthodes sur les ensembles de test, selon la section 9 du plan.

    Les erreurs de test sont celles des modèles retenus, écrites par
    src/models/evaluation_finale.py. Pour survey, les grappes de cropcut tenues à l'écart
    sont ajoutées.
    """
    from src.models.evaluation_finale import TESTS, VALIDATION_EXTERNE
    from src.models.experiences import DOSSIER_MODELES

    dossier = DOSSIER_MODELES if dossier is None else dossier
    evaluation = pd.read_csv(dossier / f"{jeu}_evaluation.csv.gz", low_memory=False)
    partitions = TESTS + ([VALIDATION_EXTERNE] if jeu == "survey" else [])
    evaluation = evaluation[evaluation["partition"].isin(partitions)].reset_index(drop=True)
    evaluation["erreur"] = np.abs(np.log(evaluation["prediction"]) - np.log(evaluation["reel"]))
    calibration = calibration_finale(jeu)
    lignes = []
    normalisees = _normalisee(jeu, calibration, evaluation, NIVEAUX)
    for methode in METHODES:
        for niveau in NIVEAUX:
            demi = (normalisees[niveau] if methode == "M4"
                    else demi_largeurs(jeu, methode, calibration, evaluation, niveau))
            for partition in partitions:
                masque = (evaluation["partition"] == partition).to_numpy()
                lignes.append({"jeu": jeu, "partition": partition, "methode": methode, "niveau": niveau,
                               "lignes": int(masque.sum()),
                               **metriques_couverture(jeu, evaluation[masque], demi[masque], niveau)})
    return pd.DataFrame(lignes)
