"""Entraînement et validation croisée des modèles de rendement.

Les modèles prédisent le logarithme népérien du rendement par gradient boosting sur
arbres de décision, avec LightGBM. Ce choix tient aux interactions attendues entre
culture, climat et sol, aux valeurs manquantes des précipitations avant 2001, que
LightGBM traite sans imputation, et aux variables catégorielles.

La validation croisée suit le protocole d'évaluation. Elle n'utilise que le
développement, réparti en cinq plis groupés, et enregistre les prédictions hors pli
pour plusieurs nombres d'arbres, ce qui permet de choisir ce nombre sans toucher aux
ensembles de test.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.evaluation.partitions import DEVELOPPEMENT, NOMBRE_PLIS
from src.evaluation.references import reference_hierarchique

GRAINE = 20261104
PARAMETRES = {
    "objective": "l1",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "cat_smooth": 10.0,
    "verbose": -1,
    "num_threads": 4,
    "deterministic": True,
    "seed": GRAINE,
}


def matrice(table, categorielles, numeriques, categories=None):
    """Retourne la matrice des variables explicatives et les modalités de chaque catégorielle.

    Les modalités sont fixées une fois pour toutes, afin qu'une même modalité reçoive le
    même code à l'entraînement et à la prédiction. Une modalité inconnue devient manquante.
    """
    if categories is None:
        categories = {c: sorted(table[c].dropna().astype(str).unique()) for c in categorielles}
    x = pd.DataFrame(index=table.index)
    for colonne in categorielles:
        x[colonne] = pd.Categorical(table[colonne].astype("string").astype(object), categories=categories[colonne])
    for colonne in numeriques:
        x[colonne] = pd.to_numeric(table[colonne], errors="coerce").astype(float)
    return x, categories


def entrainer(x, y, parametres=PARAMETRES, iterations=1000):
    """Entraîne un modèle sur le logarithme du rendement."""
    donnees = lgb.Dataset(x, label=np.log(np.asarray(y, dtype=float)), categorical_feature=list(
        x.select_dtypes("category").columns), free_raw_data=False)
    return lgb.train(parametres, donnees, num_boost_round=iterations)


def predictions_hors_echantillon(developpement, cible, categorielles, numeriques, decoupages, parametres=PARAMETRES,
                                 iterations=2000, pas=100):
    """Retourne les prédictions des lignes évaluées par chaque découpage, pour plusieurs nombres d'arbres.

    decoupages est une liste de couples de masques sur le développement, le premier
    désignant les lignes d'entraînement et le second les lignes évaluées. Une ligne
    évaluée par aucun découpage est absente du résultat, qui a une colonne par nombre
    d'arbres, en rendement.
    """
    x, categories = matrice(developpement, categorielles, numeriques)
    paliers = list(range(pas, iterations + 1, pas))
    predictions = pd.DataFrame(np.nan, index=developpement.index, columns=paliers)
    for apprentissage, evaluation in decoupages:
        modele = entrainer(x[apprentissage], developpement.loc[apprentissage, cible], parametres, iterations)
        for palier in paliers:
            predictions.loc[evaluation, palier] = np.exp(modele.predict(x[evaluation], num_iteration=palier))
    return predictions.dropna(how="all"), categories


def decoupages_plis(developpement, masque=None):
    """Retourne les découpages de la validation croisée à cinq plis groupés.

    masque restreint les lignes d'entraînement de chaque pli, sans changer les lignes évaluées.
    """
    decoupages = []
    for pli in range(NOMBRE_PLIS):
        evaluation = developpement["pli"] == pli
        apprentissage = ~evaluation if masque is None else ~evaluation & masque.reindex(developpement.index)
        decoupages.append((apprentissage, evaluation))
    return decoupages


def validation_croisee(table, cible, categorielles, numeriques, parametres=PARAMETRES, iterations=2000, pas=100,
                       masque=None):
    """Retourne les prédictions hors pli du développement pour plusieurs nombres d'arbres."""
    developpement = table[table["partition"] == DEVELOPPEMENT]
    return predictions_hors_echantillon(developpement, cible, categorielles, numeriques,
                                        decoupages_plis(developpement, masque), parametres, iterations, pas)


def erreur_par_palier(reel, predictions):
    """Retourne l'erreur absolue moyenne sur le logarithme pour chaque nombre d'arbres."""
    log_reel = np.log(np.asarray(reel, dtype=float))[:, None]
    return pd.Series(np.mean(np.abs(np.log(predictions.to_numpy()) - log_reel), axis=0), index=predictions.columns)


def reference_hors_echantillon(developpement, cible, niveaux, decoupages):
    """Retourne les prédictions de la référence hiérarchique pour chaque découpage."""
    prediction = pd.Series(np.nan, index=developpement.index)
    for apprentissage, evaluation in decoupages:
        prediction[evaluation] = reference_hierarchique(developpement[apprentissage], developpement[evaluation], cible,
                                                        niveaux)[0]
    return prediction.dropna()


def reference_croisee(table, cible, niveaux):
    """Retourne les prédictions hors pli de la référence hiérarchique sur le développement."""
    developpement = table[table["partition"] == DEVELOPPEMENT]
    return reference_hors_echantillon(developpement, cible, niveaux, decoupages_plis(developpement))
