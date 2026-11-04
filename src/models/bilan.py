"""Bilan des expériences de sélection.

Les erreurs sont mesurées en mae_log sur les lignes évaluées par chaque schéma. Les
écarts entre deux variantes sont accompagnés d'un intervalle de confiance obtenu
par bootstrap des groupes du protocole, puisque les lignes d'un même groupe ne sont
pas indépendantes.
"""

import numpy as np
import pandas as pd

from .apprentissage import erreur_par_palier
from .experiences import DOSSIER_MODELES, lire_experience

TIRAGES = 1000
GRAINE_BOOTSTRAP = 0


def erreurs_absolues(reel, prediction):
    """Retourne l'erreur absolue sur le logarithme de chaque ligne."""
    return np.abs(np.log(np.asarray(prediction, dtype=float)) - np.log(np.asarray(reel, dtype=float)))


def intervalle_bootstrap(ecarts, groupes, tirages=TIRAGES, graine=GRAINE_BOOTSTRAP):
    """Retourne l'intervalle de confiance à 95 % d'un écart moyen, par bootstrap des groupes."""
    codes, uniques = pd.factorize(pd.Series(groupes).astype(str))
    sommes = np.bincount(codes, weights=np.asarray(ecarts, dtype=float))
    effectifs = np.bincount(codes)
    generateur = np.random.default_rng(graine)
    tirage = generateur.integers(0, len(uniques), (tirages, len(uniques)))
    moyennes = sommes[tirage].sum(axis=1) / effectifs[tirage].sum(axis=1)
    return tuple(np.percentile(moyennes, [2.5, 97.5]))


def bilan_schema(jeu, schema, developpement, cible, noms, dossier=DOSSIER_MODELES):
    """Retourne, pour chaque variante d'un schéma, son erreur et son écart au modèle complet.

    Chaque variante est prise à son meilleur nombre d'arbres dans ce schéma. L'écart
    positif signifie que la variante fait moins bien que le modèle complet.
    """
    reference = lire_experience(jeu, schema, "reference", dossier)
    lignes = reference.index
    reel = developpement.loc[lignes, cible]
    groupes = developpement.loc[lignes, "groupe"]
    erreur_reference = erreurs_absolues(reel, reference)
    complet = None
    resultat = {}
    for nom in ["complet"] + [n for n in noms if n != "complet"]:
        predictions = lire_experience(jeu, schema, nom, dossier).reindex(lignes)
        courbe = erreur_par_palier(reel, predictions)
        erreur = erreurs_absolues(reel, predictions[courbe.idxmin()])
        if complet is None:
            complet = erreur
        bas, haut = intervalle_bootstrap(erreur - complet, groupes)
        resultat[nom] = {
            "lignes": len(lignes), "meilleur_palier": int(courbe.idxmin()), "mae_log": erreur.mean(),
            "competence": 1 - erreur.mean() / erreur_reference.mean(), "ecart_au_complet": (erreur - complet).mean(),
            "ic_bas": bas, "ic_haut": haut,
        }
    tableau = pd.DataFrame(resultat).T
    tableau.loc["reference"] = {"lignes": len(lignes), "mae_log": erreur_reference.mean(), "competence": 0.0}
    return tableau


def courbe_paliers(jeu, schema, developpement, cible, nom="complet", dossier=DOSSIER_MODELES):
    """Retourne l'erreur d'une variante pour chaque nombre d'arbres dans un schéma."""
    predictions = lire_experience(jeu, schema, nom, dossier)
    return erreur_par_palier(developpement.loc[predictions.index, cible], predictions)
