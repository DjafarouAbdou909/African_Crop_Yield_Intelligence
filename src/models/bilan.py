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


def part_expliquee_climat(developpement, variables, cible="yieldTonHa", serie=("GDAM_ID", "crop", "saison"),
                          annee="harvest_year", depuis=2001, annees_minimum=10, strates=None):
    """Mesure la part de la variance annuelle du rendement qu'expliquent les variables climatiques.

    Le logarithme du rendement et chaque variable sont débarrassés, série par série, de
    leur moyenne et de leur tendance linéaire. La part expliquée est le coefficient de
    détermination d'une régression linéaire des écarts du rendement sur les écarts des
    variables et sur leurs carrés. Calculée sur les données ajustées, elle majore la
    part réellement prévisible. strates associe un nom à un masque des lignes.
    """
    donnees = developpement[developpement[annee] >= depuis].dropna(subset=list(variables)).copy()
    donnees["serie"] = donnees[list(serie)].astype(str).agg("|".join, axis=1)
    donnees = donnees[donnees["serie"].map(donnees["serie"].value_counts()) >= annees_minimum]
    colonnes = {"rendement": np.log(donnees[cible])}
    for variable in variables:
        colonnes[variable] = np.log1p(donnees[variable]) if variable == "pluie_cumul" else donnees[variable]
    valeurs = pd.DataFrame(colonnes)
    temps = donnees[annee] - donnees.groupby("serie")[annee].transform("mean")
    pente = (valeurs.mul(temps, axis=0).groupby(donnees["serie"]).transform("sum")
             .div((temps ** 2).groupby(donnees["serie"]).transform("sum").replace(0, np.nan), axis=0).fillna(0))
    residus = valeurs - valeurs.groupby(donnees["serie"]).transform("mean") - pente.mul(temps, axis=0)
    explicatives = residus[list(variables)].to_numpy()
    explicatives = np.column_stack([np.ones(len(residus)), explicatives, explicatives ** 2])
    expliquee = residus["rendement"].to_numpy()
    strates = {"ensemble": np.ones(len(donnees), bool)} if strates is None else {
        nom: np.asarray(masque(donnees)) for nom, masque in strates.items()}
    lignes = {}
    for nom, masque in strates.items():
        if masque.sum() < 200:
            continue
        coefficients, *_ = np.linalg.lstsq(explicatives[masque], expliquee[masque], rcond=None)
        ajuste = explicatives[masque] @ coefficients
        lignes[nom] = {"lignes": int(masque.sum()), "series": donnees.loc[masque, "serie"].nunique(),
                       "part_expliquee": 1 - np.var(expliquee[masque] - ajuste) / np.var(expliquee[masque]),
                       "ecart_type_anomalie": np.std(expliquee[masque])}
    return pd.DataFrame(lignes).T
