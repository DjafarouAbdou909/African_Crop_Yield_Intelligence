"""Contrôles des séries climatiques, des calendriers et de l'alignement des années.

Ces fonctions produisent les constats du notebook 06_climate_variables. Elles ne
modifient aucune donnée.
"""

from multiprocessing import Pool

import numpy as np
import pandas as pd

from .agregation import moyenne_ponderee
from .calendrier import fenetre_saison
from .climat import DOSSIER_MAGASIN, DOSSIER_POWER, PARAMETRES_POWER, lire_power, ouvrir_magasin

SEUIL_CUMUL_ABERRANT = 200.0
DEBUT_RAYONNEMENT = "1984-01-01"


def _resumer_power(chemin):
    serie = lire_power(chemin)
    apres = serie.loc[DEBUT_RAYONNEMENT:]
    pluie = serie["PRECTOTCORR"]
    resume = {
        "maille": chemin.name[6:-7],
        "jours": len(serie),
        "colonnes_conformes": list(serie.columns) == PARAMETRES_POWER,
        "debut": serie.index[0],
        "fin": serie.index[-1],
        "dates_uniques": serie.index.is_unique,
        "rayonnement_manquant_apres_1984": apres["ALLSKY_SFC_SW_DWN"].isna().mean(),
    }
    for variable in PARAMETRES_POWER:
        resume[f"{variable}_manquant"] = serie[variable].isna().mean()
        resume[f"{variable}_min"] = serie[variable].min()
        resume[f"{variable}_max"] = serie[variable].max()
    annuel = pluie.groupby(pluie.index.year)
    resume["pluie_annuelle"] = annuel.sum().to_dict()
    resume["jours_aberrants"] = (pluie > SEUIL_CUMUL_ABERRANT).groupby(pluie.index.year).sum().to_dict()
    resume["gwetroot_annuel"] = serie["GWETROOT"].groupby(serie.index.year).mean().to_dict()
    return resume


def resumer_power(dossier=DOSSIER_POWER, processus=6):
    """Retourne un résumé par maille des fichiers POWER, avec les cumuls annuels de PRECTOTCORR."""
    with Pool(processus) as pool:
        return pd.DataFrame(pool.map(_resumer_power, sorted(dossier.glob("power_*.csv.gz")), chunksize=50))


def comparer_precipitations(resume_power, magasin=DOSSIER_MAGASIN):
    """Compare par année le cumul moyen des mailles de PRECTOTCORR et d'IMERG.

    Les cumuls annuels sont peu sensibles à la différence entre temps solaire local et
    temps universel. Seules les années complètes d'IMERG, de 2001 à 2023, sont comparées.
    """
    mailles, dates, tableaux = ouvrir_magasin("imerg", magasin)
    imerg = pd.DataFrame(np.asarray(tableaux["IMERG_PRECTOT"]).T, index=dates, columns=mailles["maille"])
    imerg = imerg.groupby(imerg.index.year).sum().loc[2001:]
    power = pd.DataFrame(list(resume_power["pluie_annuelle"]), index=resume_power["maille"]).T.loc[2001:2023]
    communes = imerg.columns.intersection(power.columns)
    jours = pd.DataFrame(list(resume_power["jours_aberrants"]), index=resume_power["maille"]).T
    return pd.DataFrame({
        "prectotcorr_mm": power[communes].mean(axis=1),
        "imerg_mm": imerg[communes].mean(axis=1),
        "rapport": power[communes].mean(axis=1) / imerg[communes].mean(axis=1),
        "jours_prectotcorr_au_dela_de_200_mm": jours.sum(axis=1).reindex(range(2001, 2024)),
        "jours_imerg_au_dela_de_200_mm": pd.Series(
            (np.asarray(tableaux["IMERG_PRECTOT"]) > SEUIL_CUMUL_ABERRANT).sum(axis=0), index=dates
        ).groupby(dates.year).sum().loc[2001:],
    })


def incoherences_annee_semis(regional):
    """Compare l'année de semis publiée à celle que déduisent les mois et l'année de récolte."""
    hs = regional.dropna(subset=["planting_month", "harvest_month", "planting_year"])
    deduite = hs["harvest_year"] - (hs["planting_month"] > hs["harvest_month"]).astype(int)
    ecart = hs["planting_year"] - deduite
    return pd.DataFrame({
        "lignes": hs.groupby("country").size(),
        "semis_publie_trop_tot": (ecart < 0).groupby(hs["country"]).sum(),
        "semis_publie_trop_tard": (ecart > 0).groupby(hs["country"]).sum(),
    }).query("semis_publie_trop_tot > 0 or semis_publie_trop_tard > 0")


def anomalies_rendement(regional, pays, culture, annees, saison=None):
    """Retourne la médiane par année de récolte de l'écart du log rendement à la moyenne de sa zone."""
    choix = regional[(regional["country"] == pays) & (regional["crop"] == culture) & (regional["Source"] == "HarvestStat")]
    if saison is not None:
        choix = choix[choix["saison"] == saison]
    log = np.log(choix["yieldTonHa"])
    ecart = log - log.groupby(choix["GDAM_ID"]).transform("mean")
    return ecart.groupby(choix["harvest_year"]).median().reindex(annees)


def cumuls_par_lieu(poids, produit, variable, magasin=DOSSIER_MAGASIN):
    """Retourne, pour chaque lieu, le cumul journalier de la série pondérée d'une variable.

    Les cumuls sont ramenés sur le calendrier de POWER, et les jours sans valeur
    comptent pour zéro. Une fenêtre sans aucune valeur est écartée par l'appelant.
    """
    mailles, dates, tableaux = ouvrir_magasin(produit, magasin)
    dates_power = ouvrir_magasin("power", magasin)[1]
    decalage = (dates[0] - dates_power[0]).days
    index = pd.Series(np.arange(len(mailles)), index=mailles["maille"])
    cumuls = {}
    for lieu, groupe in poids.groupby("lieu"):
        presentes = groupe["maille"].isin(index.index).to_numpy()
        serie = moyenne_ponderee(tableaux[variable], index[groupe["maille"][presentes]].to_numpy(),
                                 groupe["poids"].to_numpy()[presentes])
        cumuls[lieu] = np.concatenate([[0.0], np.zeros(decalage), np.cumsum(np.nan_to_num(serie))])
    return cumuls, dates_power, decalage


def valeur_fenetres(cumuls, dates, lieux, annees, mois_semis, mois_recolte, premier_jour=0, moyenne=True):
    """Retourne la moyenne ou le cumul d'une variable sur la fenêtre de chaque ligne.

    Une fenêtre qui commence avant premier_jour ou s'achève après la fin des séries
    reçoit une valeur manquante.
    """
    debut, fin = fenetre_saison(annees, mois_semis, mois_recolte)
    valides = ~pd.isna(debut)
    d = np.where(valides, (pd.DatetimeIndex(debut) - dates[0]).days, -1)
    f = np.where(valides, (pd.DatetimeIndex(fin) - dates[0]).days, -1)
    resultat = np.full(len(d), np.nan)
    for rang, (lieu, a, b) in enumerate(zip(lieux, d, f)):
        if lieu in cumuls and a >= premier_jour and b < len(dates):
            total = cumuls[lieu][b + 1] - cumuls[lieu][a]
            resultat[rang] = total / (b - a + 1) if moyenne else total
    return resultat


def alignement_regional(regional, valeurs, transformation=None):
    """Corrèle les différences annuelles du log rendement et d'une variable climatique.

    valeurs associe chaque décalage d'année à la variable de chaque ligne. Les
    différences sont prises entre années consécutives d'une même zone, culture et
    saison, ce qui retire les écarts entre zones et les tendances lentes.
    """
    morceaux = []
    for decalage, valeur in valeurs.items():
        x = regional.assign(v=valeur if transformation is None else transformation(valeur), decalage=decalage)
        morceaux.append(x.dropna(subset=["v"]))
    x = pd.concat(morceaux).sort_values("harvest_year")
    cle = ["decalage", "GDAM_ID", "crop", "saison"]
    x = x.assign(dly=x.groupby(cle)["yieldTonHa"].transform(lambda s: np.log(s).diff()),
                 dv=x.groupby(cle)["v"].diff(), suite=x.groupby(cle)["harvest_year"].diff() == 1)
    x = x[x["suite"]].dropna(subset=["dly", "dv"])
    table = x.groupby(["country", "decalage"])[["dly", "dv"]].apply(lambda g: g["dly"].corr(g["dv"])).unstack()
    table["paires"] = x[x["decalage"] == 0].groupby("country").size()
    return table


def alignement_survey(cellules, valeurs, transformation=None):
    """Corrèle les anomalies du log rendement moyen et d'une variable climatique dans survey.

    cellules contient une ligne par pays, zone, culture et vague, avec le log rendement
    moyen ly. Les effets fixes de la zone et de la vague sont retirés, ce qui ne garde
    que la variation propre à une zone et à une vague.
    """
    resultats = {}
    for hypothese, valeur in valeurs.items():
        x = cellules.assign(v=valeur if transformation is None else transformation(valeur)).dropna(subset=["v"])
        for colonne in ["ly", "v"]:
            x[colonne + "_a"] = (
                x[colonne]
                - x.groupby(["zone", "crop"])[colonne].transform("mean")
                - x.groupby(["Country", "crop", "AgYearStart"])[colonne].transform("mean")
                + x.groupby(["Country", "crop"])[colonne].transform("mean")
            )
        x = x[x.groupby(["zone", "crop"])["ly"].transform("size") >= 2]
        resultats[hypothese] = x.groupby("Country")[["ly_a", "v_a"]].apply(lambda g: g["ly_a"].corr(g["v_a"]))
        resultats[f"cellules {hypothese}"] = x.groupby("Country").size()
    return pd.DataFrame(resultats)


def ecart_mois(a, b):
    """Retourne l'écart circulaire en mois entre deux mois de l'année."""
    ecart = np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)) % 12
    return np.minimum(ecart, 12 - ecart)

