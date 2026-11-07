"""Figures de l'étude sur la couverture conforme sous changement de distribution.

Exécution depuis la racine du projet avec la commande python -m src.recherche.figures,
qui écrit les figures dans reports/figures.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .couverture import _mondrian, erreurs_banc  # noqa: E402

DOSSIER_FIGURES = Path(__file__).resolve().parents[2] / "reports" / "figures"
NIVEAU = 0.8
ANNEE_RUPTURE = 2012
CULTURES_FR = {"Sesame": "Sésame", "Millet": "Mil", "Sorghum": "Sorgho", "Groundnut": "Arachide", "Maize": "Maïs",
               "Wheat": "Blé", "Cotton": "Coton", "Rice": "Riz"}


def series_soudan(banc):
    """Retourne les lignes du Soudan avec leur prédiction, leur biais et leur demi-largeur M0 à 80 %.

    Les années antérieures à 2012 portent les prédictions de la validation croisée, et les
    années suivantes celles de la validation temporelle, issues d'un modèle qui n'a vu
    aucune récolte postérieure à 2011.
    """
    calibration = banc[banc["role"] == "calibration"]
    soudan = banc[(banc["country"] == "Sudan") & banc["role"].isin(["calibration", "temporelle"])].copy()
    soudan["demi"] = _mondrian(calibration, soudan, [["crop"]], NIVEAU)
    soudan["biais"] = np.log(soudan["prediction"]) - np.log(soudan["yieldTonHa"])
    soudan["serie"] = soudan[["GDAM_ID", "crop", "saison"]].astype(str).agg("|".join, axis=1)
    return soudan


def serie_representative(soudan, avant_minimum=15, apres_minimum=4):
    """Choisit la série dont le biais médian après 2011 est le plus proche de celui de tout le Soudan."""
    apres = soudan["harvest_year"] >= ANNEE_RUPTURE
    comptes = pd.DataFrame({"avant": (~apres).groupby(soudan["serie"]).sum(), "apres": apres.groupby(soudan["serie"]).sum()})
    eligibles = comptes[(comptes["avant"] >= avant_minimum) & (comptes["apres"] >= apres_minimum)].index
    biais_apres = soudan[apres & soudan["serie"].isin(eligibles)].groupby("serie")["biais"].median()
    cible = soudan.loc[apres, "biais"].median()
    return (biais_apres - cible).abs().idxmin(), cible, len(eligibles)


def figure_soudan(chemin=None):
    """Trace la série représentative du Soudan et le biais annuel de toutes ses séries."""
    soudan = series_soudan(erreurs_banc("regional"))
    serie, biais_cible, eligibles = serie_representative(soudan)
    exemple = soudan[soudan["serie"] == serie].sort_values("harvest_year")
    region = exemple["admin_1"].iloc[0]
    culture = CULTURES_FR.get(exemple["crop"].iloc[0], exemple["crop"].iloc[0])

    plt.rcParams.update({"font.size": 13})
    figure, (gauche, droite) = plt.subplots(1, 2, figsize=(17, 6.8), gridspec_kw={"width_ratios": [1.15, 1]})
    annees = exemple["harvest_year"]
    gauche.fill_between(annees, exemple["prediction"] * np.exp(-exemple["demi"]),
                        exemple["prediction"] * np.exp(exemple["demi"]), color="#9ecae1", alpha=0.6,
                        label="Intervalle annoncé à 80 %")
    gauche.plot(annees, exemple["prediction"], color="#2171b5", lw=2.2, label="Prédiction du modèle")
    dedans = (exemple["erreur"] <= exemple["demi"]).to_numpy()
    gauche.scatter(annees[dedans], exemple["yieldTonHa"][dedans], color="black", zorder=3, s=36,
                   label="Rendement observé, dans l'intervalle")
    gauche.scatter(annees[~dedans], exemple["yieldTonHa"][~dedans], color="#d62728", zorder=3, s=60, marker="X",
                   label="Rendement observé, hors de l'intervalle")
    gauche.axvline(ANNEE_RUPTURE - 0.5, color="grey", ls="--", lw=1)
    bas = gauche.get_ylim()[0]
    gauche.text(ANNEE_RUPTURE - 0.3, bas + 0.01 * (gauche.get_ylim()[1] - bas), "années jamais vues\npar le modèle",
                va="bottom", fontsize=11, color="grey")
    gauche.set_title(f"a) {culture}, {region}, Soudan", loc="left", fontweight="bold")
    gauche.set_xlabel("Année de récolte")
    gauche.set_ylabel("Rendement, t/ha")
    gauche.legend(loc="upper left", fontsize=10.5, frameon=False)

    par_annee = soudan.groupby("harvest_year").agg(biais=("biais", "median"), demi=("demi", "median"))
    droite.fill_between(par_annee.index, -par_annee["demi"], par_annee["demi"], color="#9ecae1", alpha=0.6,
                        label="Demi-largeur médiane de l'intervalle à 80 %")
    couleurs = np.where(par_annee["biais"].abs() > par_annee["demi"], "#d62728", "#2171b5")
    droite.bar(par_annee.index, par_annee["biais"], color=couleurs, width=0.7, label="Biais médian du modèle")
    droite.axhline(0, color="black", lw=0.8)
    droite.axvline(ANNEE_RUPTURE - 0.5, color="grey", ls="--", lw=1)
    droite.set_title("b) Biais du modèle, toutes séries du Soudan", loc="left", fontweight="bold")
    droite.set_xlabel("Année de récolte")
    droite.set_ylabel("Log(prédiction) − log(observé)")
    droite.legend(loc="lower left", fontsize=10.5, frameon=False)

    figure.suptitle("Le centre de l'intervalle est faux, pas sa largeur", fontsize=17, fontweight="bold", x=0.01,
                    ha="left")
    figure.text(0.01, -0.02, (
        f"Modèle LightGBM de rendements régionaux GROW-Africa. Avant 2012, prédictions de validation croisée spatiale. "
        f"À partir de 2012, prédictions d'un modèle entraîné jusqu'en 2011. La série du panneau a été choisie parmi les "
        f"{eligibles} séries éligibles du Soudan, comme la plus proche du biais médian du pays après 2011, soit {biais_cible:.2f}."),
        fontsize=10, color="dimgrey", wrap=True)
    figure.tight_layout()
    chemin = DOSSIER_FIGURES / "soudan_couverture.png" if chemin is None else chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(chemin, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return chemin, serie


if __name__ == "__main__":
    chemin, serie = figure_soudan()
    print(chemin, serie)
