"""Prix de l'anticipation du modèle retenu de regional selon l'horizon de prévision.

Ce module met en œuvre le plan préenregistré de docs/research_forecast_horizons.md.
Les indicateurs climatiques sont recalculés sur la partie de la saison observée à
chaque date de prévision, puis le modèle retenu est réentraîné sur ces indicateurs dans
les fenêtres successives de docs/research_rolling_windows.md. L'horizon du semis
reprend la variante sans climat et celui de la fin de saison le modèle retenu, déjà
calculés par src/recherche/fenetres_temporelles.py.

Exécution depuis la racine du projet, dans l'ordre, avec les commandes
python -m src.recherche.horizons_prevision variables puis
python -m src.recherche.horizons_prevision calculer.
"""

import sys

import numpy as np
import pandas as pd

from src.data.load import DOSSIER_TRAITE
from src.features.agregation import indicateurs_lieux
from src.features.climat import DOSSIER_MAGASIN
from src.features.variables import CLE_REGIONAL
from src.models.apprentissage import predictions_hors_echantillon
from src.models.donnees import VARIABLES_CLIMAT
from src.models.selection import configuration_retenue

from .fenetres_temporelles import CIBLE, DOSSIER_RECHERCHE, FENETRES, decoupages, developpement_regional, fenetre_de

HORIZONS = ["semis", "mi_saison", "un_mois_avant", "fin_saison"]
HORIZONS_TRONQUES = ["mi_saison", "un_mois_avant"]
COLONNES_FENETRES = {"semis": "sans_climat", "fin_saison": "complet"}
BORNE_PRIX_FAIBLE = 0.01
CLASSES_SECHES = ["aride", "semi_aride"]


def fin_observee(debut, fin, horizon):
    """Retourne le dernier jour observé de chaque saison à la date de prévision d'un horizon.

    À mi-saison, la première moitié de la fenêtre est observée, arrondie au jour
    inférieur. Un mois avant la récolte, la saison est observée jusqu'au dernier jour du
    mois qui précède le mois de récolte. Le résultat précède debut lorsqu'aucun jour
    n'est observé.
    """
    debut, fin = pd.DatetimeIndex(debut), pd.DatetimeIndex(fin)
    if horizon == "mi_saison":
        jours = (fin - debut).days + 1
        return debut + pd.to_timedelta(jours // 2 - 1, unit="D")
    if horizon == "un_mois_avant":
        return fin.to_period("M").to_timestamp() - pd.Timedelta(days=1)
    if horizon == "fin_saison":
        return fin
    raise ValueError(f"Horizon sans fenêtre tronquée {horizon}")


def fenetres_tronquees(climat, horizon):
    """Retourne la clé, le lieu et la fenêtre observée de chaque ligne, manquante si elle est vide."""
    fenetres = climat[CLE_REGIONAL + ["lieu", "debut", "fin"]].copy()
    fenetres["debut"] = pd.to_datetime(fenetres["debut"])
    fenetres["fin"] = fin_observee(fenetres["debut"], pd.to_datetime(fenetres["fin"]), horizon)
    vide = fenetres["fin"] < fenetres["debut"]
    fenetres.loc[vide, ["debut", "fin"]] = pd.NaT
    return fenetres


def variables_horizon(climat, poids, horizon, magasin=DOSSIER_MAGASIN):
    """Retourne les douze indicateurs climatiques de chaque ligne, calculés sur sa fenêtre observée."""
    fenetres = fenetres_tronquees(climat, horizon)
    distinctes = fenetres.dropna(subset=["lieu", "debut", "fin"]).drop_duplicates(["lieu", "debut", "fin"])
    indicateurs = indicateurs_lieux(poids, distinctes[["lieu", "debut", "fin"]], magasin)
    resultat = fenetres.merge(indicateurs, on=["lieu", "debut", "fin"], how="left")
    return resultat[CLE_REGIONAL + VARIABLES_CLIMAT]


def construire_variables(dossier=DOSSIER_RECHERCHE, magasin=DOSSIER_MAGASIN):
    """Écrit les variables climatiques des horizons tronqués et contrôle le calcul en fin de saison.

    Le contrôle recalcule les indicateurs de la saison entière d'un échantillon de lieux
    et vérifie qu'ils coïncident avec climat_regional.csv.gz.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    climat = pd.read_csv(DOSSIER_TRAITE / "climat_regional.csv.gz")
    poids = pd.read_csv(magasin / "poids_regional.csv")

    lieux = pd.Series(climat["lieu"].dropna().unique()).sample(50, random_state=0)
    echantillon = climat[climat["lieu"].isin(lieux)]
    recalcul = variables_horizon(echantillon, poids, "fin_saison", magasin)
    ecart = np.nanmax(np.abs(recalcul[VARIABLES_CLIMAT].to_numpy() - echantillon[VARIABLES_CLIMAT].to_numpy()))
    manquants = (recalcul[VARIABLES_CLIMAT].isna().to_numpy() != echantillon[VARIABLES_CLIMAT].isna().to_numpy()).sum()
    if ecart > 1e-6 or manquants:
        raise AssertionError(f"Le recalcul de la saison entière diffère de climat_regional, écart {ecart}")
    print(f"contrôle fin de saison sur {len(echantillon)} lignes, écart maximal {ecart:.2e}", flush=True)

    for horizon in HORIZONS_TRONQUES:
        variables = variables_horizon(climat, poids, horizon, magasin)
        variables.to_csv(dossier / f"horizon_{horizon}.csv.gz", index=False)
        print(f"horizon {horizon} {len(variables)} lignes", flush=True)


def developpement_horizon(developpement, variables):
    """Remplace les variables climatiques du développement par celles d'un horizon, sans changer l'index."""
    remplacees = developpement[CLE_REGIONAL].merge(variables, on=CLE_REGIONAL, how="left", validate="many_to_one")
    resultat = developpement.copy()
    resultat[VARIABLES_CLIMAT] = remplacees[VARIABLES_CLIMAT].to_numpy()
    return resultat


def calculer(dossier=DOSSIER_RECHERCHE):
    """Calcule les prédictions du modèle retenu aux horizons tronqués dans chaque fenêtre."""
    developpement = developpement_regional()
    categorielles, numeriques, parametres, iterations = configuration_retenue("regional", developpement)
    decoupes = list(decoupages(developpement).values())
    colonnes = {}
    for horizon in HORIZONS_TRONQUES:
        variables = pd.read_csv(dossier / f"horizon_{horizon}.csv.gz")
        table = developpement_horizon(developpement, variables)
        predictions, _ = predictions_hors_echantillon(table, CIBLE, categorielles, numeriques, decoupes,
                                                      parametres, iterations, iterations)
        colonnes[horizon] = predictions[iterations]
        print(f"horizon {horizon} terminé", flush=True)
    resultat = pd.DataFrame(colonnes)
    resultat.to_csv(dossier / "horizons.csv.gz", index_label="index")
    return resultat


def lire(developpement, dossier=DOSSIER_RECHERCHE):
    """Réunit les prédictions des quatre horizons et de la référence sur les lignes des fenêtres."""
    fenetres = pd.read_csv(dossier / "fenetres.csv.gz", index_col="index")
    horizons = pd.read_csv(dossier / "horizons.csv.gz", index_col="index")
    predictions = pd.DataFrame({h: fenetres[c] for h, c in COLONNES_FENETRES.items()})
    predictions = predictions.join(horizons, how="left").join(fenetres["reference"])
    predictions = predictions[HORIZONS + ["reference"]]
    predictions = predictions.join(developpement[[CIBLE, "groupe", "country", "harvest_year", "GDAM_ID"]], how="left")
    return predictions[fenetre_de(predictions).notna().to_numpy()]


def _resume(predictions, masque):
    """Retourne l'erreur, la compétence, le biais, le gain et le prix de l'anticipation de chaque horizon."""
    from src.models.bilan import intervalle_bootstrap

    lignes = predictions[masque]
    log_reel = np.log(lignes[CIBLE])
    erreur = {c: np.abs(np.log(lignes[c]) - log_reel) for c in HORIZONS + ["reference"]}
    resultat = []
    for horizon in HORIZONS:
        gain = erreur["reference"] - erreur[horizon]
        prix = erreur[horizon] - erreur["fin_saison"]
        gain_bas, gain_haut = intervalle_bootstrap(gain, lignes["groupe"])
        prix_bas, prix_haut = (0.0, 0.0) if horizon == "fin_saison" else intervalle_bootstrap(prix, lignes["groupe"])
        resultat.append({
            "horizon": horizon, "lignes": len(lignes), "mae_log": erreur[horizon].mean(),
            "mae_log_reference": erreur["reference"].mean(),
            "competence": 1 - erreur[horizon].mean() / erreur["reference"].mean(),
            "biais_log": (np.log(lignes[horizon]) - log_reel).mean(),
            "gain": gain.mean(), "gain_bas": gain_bas, "gain_haut": gain_haut,
            "prix": prix.mean(), "prix_bas": prix_bas, "prix_haut": prix_haut,
        })
    return pd.DataFrame(resultat)


def bilan(predictions):
    """Retourne le résumé de chaque horizon par fenêtre, puis sur l'ensemble des quatre fenêtres."""
    fenetre = fenetre_de(predictions)
    tableaux = [_resume(predictions, (fenetre == nom).to_numpy()).assign(fenetre=nom) for nom in FENETRES]
    tableaux.append(_resume(predictions, fenetre.notna().to_numpy()).assign(fenetre="ensemble"))
    return pd.concat(tableaux, ignore_index=True)


def bilan_aridite(predictions, aridite, minimum=1000):
    """Retourne le résumé de chaque horizon par classe d'aridité et pour les zones sèches réunies."""
    classe = predictions["GDAM_ID"].map(aridite["classe_aridite"])
    tableaux = []
    for modalite in classe.dropna().unique():
        masque = (classe == modalite).to_numpy()
        if masque.sum() >= minimum:
            tableaux.append(_resume(predictions, masque).assign(strate=modalite))
    tableaux.append(_resume(predictions, classe.isin(CLASSES_SECHES).to_numpy()).assign(strate="aride_et_semi_aride"))
    return pd.concat(tableaux, ignore_index=True)


def ecart_seches(predictions, aridite):
    """Retourne l'écart d'erreur entre le semis et un mois avant la récolte en zones sèches, avec son intervalle."""
    from src.models.bilan import intervalle_bootstrap

    lignes = predictions[predictions["GDAM_ID"].map(aridite["classe_aridite"]).isin(CLASSES_SECHES).to_numpy()]
    log_reel = np.log(lignes[CIBLE])
    ecart = np.abs(np.log(lignes["semis"]) - log_reel) - np.abs(np.log(lignes["un_mois_avant"]) - log_reel)
    bas, haut = intervalle_bootstrap(ecart, lignes["groupe"])
    return {"lignes": len(lignes), "ecart": ecart.mean(), "ecart_bas": bas, "ecart_haut": haut}


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else ""
    if etape == "variables":
        construire_variables()
    elif etape == "calculer":
        calculer()
    else:
        raise SystemExit("Usage python -m src.recherche.horizons_prevision variables|calculer")
