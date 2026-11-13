"""Stabilité temporelle du modèle retenu de regional sur des fenêtres successives.

Ce module met en œuvre le plan préenregistré de docs/research_rolling_windows.md.
Pour chaque fenêtre, le modèle retenu, sa variante privée des variables climatiques et
la référence n'apprennent que sur les récoltes antérieures au début de la fenêtre.
Seul le développement est utilisé, et le modèle retenu n'est pas réajusté.

Exécution depuis la racine du projet avec la commande python -m src.recherche.fenetres_temporelles.
"""

import numpy as np
import pandas as pd

from src.data.load import DOSSIER_INTERMEDIAIRE
from src.evaluation.partitions import DEVELOPPEMENT
from src.evaluation.references import NIVEAUX_REGIONAL
from src.models.apprentissage import PARAMETRES, predictions_hors_echantillon, reference_hors_echantillon
from src.models.experiences import charger_table, experiences_regional
from src.models.selection import configuration_retenue

CIBLE = "yieldTonHa"
FENETRES = {"F1": (2004, 2006), "F2": (2007, 2009), "F3": (2010, 2012), "F4": (2013, 2016)}
VARIANTES = ["complet", "sans_climat"]
DOSSIER_RECHERCHE = DOSSIER_INTERMEDIAIRE / "recherche"


def developpement_regional():
    """Retourne les lignes du développement de regional retenues pour la modélisation."""
    table = charger_table("regional")
    return table[table["partition"] == DEVELOPPEMENT]


def decoupages(developpement, fenetres=FENETRES):
    """Retourne, pour chaque fenêtre, l'entraînement sur les années antérieures et l'évaluation de la fenêtre."""
    annee = developpement["harvest_year"]
    return {nom: (annee < debut, (annee >= debut) & (annee <= fin)) for nom, (debut, fin) in fenetres.items()}


def fenetre_de(developpement, fenetres=FENETRES):
    """Retourne le nom de la fenêtre de chaque ligne, ou une valeur manquante hors des fenêtres."""
    resultat = pd.Series(pd.NA, index=developpement.index, dtype="string")
    for nom, (debut, fin) in fenetres.items():
        resultat[(developpement["harvest_year"] >= debut) & (developpement["harvest_year"] <= fin)] = nom
    return resultat


def calculer(dossier=DOSSIER_RECHERCHE):
    """Calcule les prédictions des deux variantes et de la référence dans chaque fenêtre."""
    dossier.mkdir(parents=True, exist_ok=True)
    developpement = developpement_regional()
    _, _, parametres_retenus, iterations = configuration_retenue("regional", developpement)
    decoupes = list(decoupages(developpement).values())
    definitions = experiences_regional()
    colonnes = {}
    for variante in VARIANTES:
        definition = definitions[variante]
        parametres = {**PARAMETRES, **definition.get("parametres", {}), **{"num_threads": parametres_retenus["num_threads"]}}
        predictions, _ = predictions_hors_echantillon(developpement, CIBLE, definition["categorielles"],
                                                      definition["numeriques"], decoupes, parametres, iterations,
                                                      iterations)
        colonnes[variante] = predictions[iterations]
        print(f"variante {variante} terminée", flush=True)
    colonnes["reference"] = reference_hors_echantillon(developpement, CIBLE, NIVEAUX_REGIONAL, decoupes)
    resultat = pd.DataFrame(colonnes)
    resultat.to_csv(dossier / "fenetres.csv.gz", index_label="index")
    return resultat


def lire(developpement, dossier=DOSSIER_RECHERCHE):
    """Relit les prédictions de l'étude, restreintes aux lignes des fenêtres."""
    predictions = pd.read_csv(dossier / "fenetres.csv.gz", index_col="index")
    return predictions.join(developpement[[CIBLE, "groupe", "country", "harvest_year"]], how="left")


def bilan(predictions):
    """Retourne, par fenêtre, l'erreur, la compétence, le biais, le gain sur la référence et l'apport du climat.

    Les intervalles de confiance à 95 % sont obtenus par bootstrap des groupes du protocole.
    """
    from src.models.bilan import intervalle_bootstrap

    log_reel = np.log(predictions[CIBLE])
    erreur = {c: np.abs(np.log(predictions[c]) - log_reel) for c in VARIANTES + ["reference"]}
    biais = {c: np.log(predictions[c]) - log_reel for c in ["complet", "reference"]}
    fenetre = fenetre_de(predictions)
    lignes = []
    for nom in FENETRES:
        masque = (fenetre == nom).to_numpy()
        groupes = predictions.loc[masque, "groupe"]
        gain = (erreur["reference"] - erreur["complet"])[masque]
        apport = (erreur["sans_climat"] - erreur["complet"])[masque]
        gain_bas, gain_haut = intervalle_bootstrap(gain, groupes)
        apport_bas, apport_haut = intervalle_bootstrap(apport, groupes)
        lignes.append({
            "fenetre": nom, "annees": f"{FENETRES[nom][0]} à {FENETRES[nom][1]}", "lignes": int(masque.sum()),
            "pays": predictions.loc[masque, "country"].nunique(),
            "mae_log": erreur["complet"][masque].mean(), "mae_log_reference": erreur["reference"][masque].mean(),
            "competence": 1 - erreur["complet"][masque].mean() / erreur["reference"][masque].mean(),
            "gain": gain.mean(), "gain_bas": gain_bas, "gain_haut": gain_haut,
            "apport_climat": apport.mean(), "apport_bas": apport_bas, "apport_haut": apport_haut,
            "biais_log": biais["complet"][masque].mean(), "biais_log_reference": biais["reference"][masque].mean(),
        })
    return pd.DataFrame(lignes)


if __name__ == "__main__":
    calculer()
