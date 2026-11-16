"""Écart entre rendements déclarés et mesures par coupe, et correction des prédictions.

Ce module met en œuvre le plan préenregistré de docs/research_cropcut_gap.md. La
partie A compare, sur les grappes vues, les rendements déclarés du développement de
survey aux mesures par coupe des mêmes cellules, formées de la grappe, de la culture
et de l'année. La partie B apprend une correction des prédictions sur les mesures par
coupe des grappes vues, à partir de prédictions hors pli, et ne l'évalue qu'une fois
sur les grappes tenues à l'écart.

Exécution depuis la racine du projet avec la commande python -m src.recherche.ecart_cropcut,
suivie de calibration puis de finale.
"""

import sys

import numpy as np
import pandas as pd

from src.data.load import DOSSIER_INTERMEDIAIRE
from src.evaluation.partitions import DEVELOPPEMENT, NOMBRE_PLIS, SEL_PLI, seau
from src.evaluation.references import NIVEAUX_SURVEY, reference_hierarchique
from src.models.apprentissage import entrainer, matrice
from src.models.donnees import CIBLE_CROPCUT, CIBLE_SURVEY, table_cropcut
from src.models.evaluation_finale import VALIDATION_EXTERNE, predire
from src.models.experiences import DOSSIER_MODELES, charger_table
from src.models.selection import configuration_retenue

DOSSIER_RECHERCHE = DOSSIER_INTERMEDIAIRE / "recherche"
CLE_CELLULE = ["id_grappe", "Crop", "annee_recolte"]
METHODES = ["C0", "C1", "C2", "C3"]
MINIMUM_CULTURE = 100
MINIMUM_CELLULES_CULTURE = 100
TOLERANCE_CHOIX = 0.005
TIRAGES = 2000
GRAINE = 0

# Choix gelés avant l'évaluation finale, d'après la validation croisée sur la calibration.
METHODE_RETENUE = {"modele": None, "reference": None}


# Partie A, comparaison des deux mesures.

def cellules_appariees(survey, cropcut):
    """Retourne les cellules présentes dans les deux jeux, avec l'écart des logarithmes moyens.

    survey ne doit contenir que des lignes du développement, et cropcut que des mesures
    des grappes vues. L'écart est positif quand le rendement déclaré dépasse la mesure.
    """
    declare = survey.assign(log_declare=np.log(survey[CIBLE_SURVEY].astype(float)),
                            log_surface=np.log(survey["GPSArea_ha_"].astype(float)))
    declare = declare.groupby(CLE_CELLULE).agg(log_declare=("log_declare", "mean"),
                                               log_surface=("log_surface", "mean"),
                                               parcelles=("log_declare", "size"))
    mesure = cropcut.assign(log_mesure=np.log(cropcut[CIBLE_CROPCUT].astype(float)))
    mesure = mesure.groupby(CLE_CELLULE).agg(log_mesure=("log_mesure", "mean"), mesures=("log_mesure", "size"),
                                             groupe=("groupe", "first"))
    cellules = declare.join(mesure, how="inner").reset_index()
    cellules["ecart"] = cellules["log_declare"] - cellules["log_mesure"]
    return cellules


def classes_surface(log_surface):
    """Répartit les cellules en trois classes de même effectif selon la surface moyenne de leurs parcelles."""
    return pd.qcut(log_surface, 3, labels=["petites", "moyennes", "grandes"]).astype("string")


def _tirages(groupes, tirages, graine):
    codes, uniques = pd.factorize(pd.Series(groupes).astype(str))
    return codes, np.random.default_rng(graine).integers(0, len(uniques), (tirages, len(uniques))), len(uniques)


def intervalle_moyenne(valeurs, groupes, tirages=TIRAGES, graine=GRAINE):
    """Retourne l'intervalle à 95 % d'une moyenne, par bootstrap des groupes."""
    codes, tirage, nombre = _tirages(groupes, tirages, graine)
    sommes = np.bincount(codes, weights=np.asarray(valeurs, dtype=float), minlength=nombre)
    effectifs = np.bincount(codes, minlength=nombre)
    return tuple(np.percentile(sommes[tirage].sum(axis=1) / effectifs[tirage].sum(axis=1), [2.5, 97.5]))


def intervalle_difference(valeurs, masque_a, masque_b, groupes, tirages=TIRAGES, graine=GRAINE):
    """Retourne l'intervalle à 95 % de la moyenne sur a diminuée de la moyenne sur b, par bootstrap des groupes."""
    codes, tirage, nombre = _tirages(groupes, tirages, graine)
    valeurs = np.asarray(valeurs, dtype=float)
    moyennes = []
    for masque in (np.asarray(masque_a, dtype=bool), np.asarray(masque_b, dtype=bool)):
        sommes = np.bincount(codes[masque], weights=valeurs[masque], minlength=nombre)
        effectifs = np.bincount(codes[masque], minlength=nombre)
        moyennes.append(sommes[tirage].sum(axis=1) / effectifs[tirage].sum(axis=1))
    return tuple(np.percentile(moyennes[0] - moyennes[1], [2.5, 97.5]))


def bilan_mesures(cellules):
    """Retourne l'écart moyen global, par classe de surface et par culture, et la comparaison des classes extrêmes."""
    lignes = []

    def ajouter(nom, masque):
        sous = cellules[masque]
        bas, haut = intervalle_moyenne(sous["ecart"], sous["groupe"])
        lignes.append({"strate": nom, "cellules": len(sous), "ecart": sous["ecart"].mean(), "bas": bas, "haut": haut})

    ajouter("toutes", np.ones(len(cellules), dtype=bool))
    classes = classes_surface(cellules["log_surface"])
    for classe in ["petites", "moyennes", "grandes"]:
        ajouter(f"surface_{classe}", (classes == classe).fillna(False).to_numpy())
    effectifs = cellules["Crop"].value_counts()
    for culture in effectifs[effectifs >= MINIMUM_CELLULES_CULTURE].index:
        ajouter(f"culture_{culture}", (cellules["Crop"] == culture).to_numpy())
    petites = (classes == "petites").fillna(False).to_numpy()
    grandes = (classes == "grandes").fillna(False).to_numpy()
    bas, haut = intervalle_difference(cellules["ecart"], petites, grandes, cellules["groupe"])
    difference = cellules.loc[petites, "ecart"].mean() - cellules.loc[grandes, "ecart"].mean()
    lignes.append({"strate": "petites_moins_grandes", "cellules": int(petites.sum() + grandes.sum()),
                   "ecart": difference, "bas": bas, "haut": haut})
    return pd.DataFrame(lignes).set_index("strate")


# Partie B, correction des prédictions.

def pli_cropcut(cropcut):
    """Retourne le pli de chaque mesure, par la même empreinte du groupe que dans le protocole."""
    return seau(cropcut["groupe"], SEL_PLI, NOMBRE_PLIS)


def predictions_hors_pli(table, calibration):
    """Prédit chaque mesure de calibration par le modèle retenu et la référence privés du pli de son groupe."""
    developpement = table[table["partition"] == DEVELOPPEMENT]
    categorielles, numeriques, parametres, iterations = configuration_retenue("survey", developpement)
    plis = pli_cropcut(calibration)
    resultat = pd.DataFrame(np.nan, index=calibration.index, columns=["prediction", "reference"])
    for pli in range(NOMBRE_PLIS):
        apprentissage = developpement[developpement["pli"] != pli]
        evaluees = calibration[(plis == pli).fillna(False).to_numpy()]
        if evaluees.empty:
            continue
        x, categories = matrice(apprentissage, categorielles, numeriques)
        modele = entrainer(x, apprentissage[CIBLE_SURVEY], parametres, iterations)
        description = {"categorielles": categorielles, "numeriques": numeriques, "categories": categories}
        resultat.loc[evaluees.index, "prediction"] = predire(modele, description, evaluees)
        resultat.loc[evaluees.index, "reference"] = reference_hierarchique(apprentissage, evaluees, CIBLE_SURVEY,
                                                                           NIVEAUX_SURVEY)[0]
    return resultat.assign(pli=plis)


def ajuster(methode, log_prediction, log_reel, cultures):
    """Estime les paramètres d'une méthode de correction sur le logarithme des prédictions."""
    ecart = np.asarray(log_reel, dtype=float) - np.asarray(log_prediction, dtype=float)
    if methode == "C0":
        return {}
    global_ = float(np.median(ecart))
    if methode == "C1":
        return {"decalage": global_}
    if methode == "C2":
        serie = pd.Series(ecart, index=np.asarray(cultures))
        effectifs = serie.groupby(level=0).size()
        medianes = serie.groupby(level=0).median()
        return {"decalage": global_, "par_culture": medianes[effectifs >= MINIMUM_CULTURE].to_dict()}
    if methode == "C3":
        pente, ordonnee = np.polyfit(np.asarray(log_prediction, dtype=float), np.asarray(log_reel, dtype=float), 1)
        return {"pente": float(pente), "ordonnee": float(ordonnee)}
    raise ValueError(methode)


def appliquer(methode, parametres, log_prediction, cultures):
    """Applique une correction estimée au logarithme des prédictions."""
    log_prediction = np.asarray(log_prediction, dtype=float)
    if methode == "C0":
        return log_prediction
    if methode == "C1":
        return log_prediction + parametres["decalage"]
    if methode == "C2":
        decalages = pd.Series(np.asarray(cultures)).map(parametres["par_culture"]).fillna(parametres["decalage"])
        return log_prediction + decalages.to_numpy()
    if methode == "C3":
        return parametres["ordonnee"] + parametres["pente"] * log_prediction
    raise ValueError(methode)


def erreurs_croisees(calibration, colonne):
    """Retourne l'erreur mae_log de chaque méthode en validation croisée à cinq plis groupés sur la calibration."""
    log_reel = np.log(calibration[CIBLE_CROPCUT].astype(float)).to_numpy()
    log_prediction = np.log(calibration[colonne].astype(float)).to_numpy()
    cultures = calibration["Crop"].to_numpy()
    plis = calibration["pli"].to_numpy()
    erreurs = {}
    for methode in METHODES:
        corrige = np.full(len(calibration), np.nan)
        for pli in range(NOMBRE_PLIS):
            evaluees = plis == pli
            parametres = ajuster(methode, log_prediction[~evaluees], log_reel[~evaluees], cultures[~evaluees])
            corrige[evaluees] = appliquer(methode, parametres, log_prediction[evaluees], cultures[evaluees])
        erreurs[methode] = float(np.mean(np.abs(corrige - log_reel)))
    return pd.Series(erreurs)


def choisir(erreurs, tolerance=TOLERANCE_CHOIX):
    """Retient la méthode la plus simple dont l'erreur ne dépasse pas la meilleure de plus de la tolérance."""
    meilleure = erreurs.min()
    return next(m for m in METHODES if erreurs[m] <= meilleure + tolerance)


def donnees_etude():
    """Retourne le développement de survey et les mesures de cropcut avec leur groupe."""
    table = charger_table("survey")
    cropcut = table_cropcut(table)
    cropcut["Crop"] = cropcut["Crop"].str.strip()
    return table, cropcut


def calibration(dossier=DOSSIER_RECHERCHE):
    """Calcule la partie A et les prédictions hors pli, puis choisit les corrections sans lire la mesure finale."""
    dossier.mkdir(parents=True, exist_ok=True)
    table, cropcut = donnees_etude()
    # Une mesure sans coordonnées n'a ni grappe ni groupe, donc ni pli. Elle est écartée.
    vues = cropcut[~cropcut["grappe_tenue_a_l_ecart"] & cropcut["groupe"].notna()].copy()
    survey = table[(table["partition"] == DEVELOPPEMENT) & (table["Country"] == "Ethiopia")]
    cellules = cellules_appariees(survey, vues)
    cellules.to_csv(dossier / "cropcut_cellules.csv.gz", index=False)
    vues = vues.join(predictions_hors_pli(table, vues))
    colonnes = ["id_mesure", "id_grappe", "groupe", "Crop", "annee_recolte", CIBLE_CROPCUT, "pli", "prediction",
                "reference"]
    vues[colonnes].to_csv(dossier / "cropcut_calibration.csv.gz", index=False)
    choix = pd.DataFrame({"modele": erreurs_croisees(vues, "prediction"),
                          "reference": erreurs_croisees(vues, "reference")})
    choix.to_csv(dossier / "cropcut_choix.csv")
    return cellules, vues, choix


def lire_calibration(dossier=DOSSIER_RECHERCHE):
    """Relit les cellules appariées, les prédictions hors pli et les erreurs croisées des corrections."""
    return (pd.read_csv(dossier / "cropcut_cellules.csv.gz"), pd.read_csv(dossier / "cropcut_calibration.csv.gz"),
            pd.read_csv(dossier / "cropcut_choix.csv", index_col=0))


def oracle_declare(cellules, calibration_lue):
    """Compare, sur les mesures des cellules appariées, la moyenne déclarée de la cellule au modèle et à la référence."""
    lignes = calibration_lue.merge(cellules[CLE_CELLULE + ["log_declare"]], on=CLE_CELLULE, how="inner")
    log_reel = np.log(lignes[CIBLE_CROPCUT])
    return pd.Series({
        "mesures": len(lignes),
        "mae_log_declare_cellule": float(np.mean(np.abs(lignes["log_declare"] - log_reel))),
        "mae_log_modele_hors_pli": float(np.mean(np.abs(np.log(lignes["prediction"]) - log_reel))),
        "mae_log_reference_hors_pli": float(np.mean(np.abs(np.log(lignes["reference"]) - log_reel))),
    })


def finale(dossier=DOSSIER_RECHERCHE, modeles=DOSSIER_MODELES, retenue=None):
    """Applique les corrections gelées aux prédictions finales des grappes tenues à l'écart, une seule fois."""
    retenue = retenue or METHODE_RETENUE
    if None in retenue.values():
        raise RuntimeError("les corrections doivent être gelées avant l'évaluation finale")
    _, calib, _ = lire_calibration(dossier)
    evaluation = pd.read_csv(modeles / "survey_evaluation.csv.gz", low_memory=False)
    ecartees = evaluation[evaluation["partition"] == VALIDATION_EXTERNE].copy()
    ecartees["Crop"] = ecartees["Crop"].str.strip()
    log_reel = np.log(ecartees["reel"].astype(float)).to_numpy()
    resultat = pd.DataFrame(index=ecartees.index)
    for nom, colonne in [("modele", "prediction"), ("reference", "reference")]:
        methode = retenue[nom]
        parametres = ajuster(methode, np.log(calib[colonne]), np.log(calib[CIBLE_CROPCUT]), calib["Crop"])
        resultat[f"{nom}_brut"] = np.log(ecartees[colonne].astype(float)).to_numpy()
        resultat[f"{nom}_corrige"] = appliquer(methode, parametres, resultat[f"{nom}_brut"], ecartees["Crop"])
    resultat["log_reel"] = log_reel
    resultat["groupe"] = ecartees["groupe"].to_numpy()
    resultat["Crop"] = ecartees["Crop"].to_numpy()
    resultat.to_csv(dossier / "cropcut_finale.csv.gz", index=False)
    return resultat


def bilan_final(resultat):
    """Retourne l'erreur, le biais et la compétence avant et après correction, avec les intervalles des hypothèses."""
    erreurs = {c: np.abs(resultat[c] - resultat["log_reel"]) for c in
               ["modele_brut", "modele_corrige", "reference_brut", "reference_corrige"]}
    lignes = {}
    for etat in ["brut", "corrige"]:
        modele, reference = erreurs[f"modele_{etat}"], erreurs[f"reference_{etat}"]
        lignes[etat] = {"mesures": len(resultat), "mae_log": modele.mean(), "mae_log_reference": reference.mean(),
                        "competence": 1 - modele.mean() / reference.mean(),
                        "biais_log": float(np.mean(resultat[f"modele_{etat}"] - resultat["log_reel"]))}
    tableau = pd.DataFrame(lignes).T
    gain = erreurs["modele_brut"] - erreurs["modele_corrige"]
    avance = erreurs["reference_corrige"] - erreurs["modele_corrige"]
    hypotheses = pd.DataFrame({
        "H3_gain_correction": [gain.mean(), *intervalle_moyenne(gain, resultat["groupe"])],
        "H4_avance_sur_reference": [avance.mean(), *intervalle_moyenne(avance, resultat["groupe"])],
    }, index=["moyenne", "bas", "haut"]).T
    return tableau, hypotheses


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else "calibration"
    if etape == "calibration":
        cellules, vues, choix = calibration()
        print(bilan_mesures(cellules).round(3).to_string())
        print(choix.round(4).to_string())
        print({nom: choisir(choix[nom]) for nom in choix})
    else:
        tableau, hypotheses = bilan_final(finale())
        print(tableau.round(3).to_string())
        print(hypotheses.round(4).to_string())
