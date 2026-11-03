"""Modèles de référence que tout modèle de rendement devra battre.

La référence prédit la moyenne géométrique des rendements d'entraînement au niveau
le plus fin disponible, puis se replie sur des niveaux plus larges lorsque la
combinaison n'a jamais été observée. Elle ne mobilise aucune variable explicative.
"""

import numpy as np
import pandas as pd

MODALITE_MANQUANTE = "non renseigné"
COLONNES_A_MODALITE_MANQUANTE = {"saison"}

NIVEAUX_REGIONAL = [
    ["crop", "saison", "zone"],
    ["crop", "saison", "L1_GID"],
    ["crop", "L0_GID"],
    ["crop"],
]
NIVEAUX_SURVEY = [
    ["Crop", "id_grappe"],
    ["Crop", "L2_GID"],
    ["Crop", "L1_GID"],
    ["Crop", "Country"],
    ["Crop"],
]


def _cle(df, colonnes):
    """Concatène les colonnes en une clé texte unique.

    Une saison manquante forme une modalité, car elle désigne une culture à saison
    unique. Toute autre valeur manquante rend la clé manquante, afin que des lignes
    sans localisation ne soient pas regroupées comme si elles partageaient un lieu.
    """
    cle = pd.Series("", index=df.index, dtype="string")
    for colonne in colonnes:
        valeurs = df[colonne].astype("string")
        if colonne in COLONNES_A_MODALITE_MANQUANTE:
            valeurs = valeurs.fillna(MODALITE_MANQUANTE)
        cle = cle + "|" + valeurs
    return cle


def reference_hierarchique(entrainement, a_predire, cible, niveaux):
    """Prédit la moyenne géométrique de la cible au niveau le plus fin observé.

    Retourne la prédiction et le rang du niveau utilisé, zéro désignant le plus fin.
    Une ligne dont aucun niveau n'a été observé reçoit la moyenne géométrique globale
    et le rang égal au nombre de niveaux.
    """
    log_cible = np.log(entrainement[cible].astype(float))
    prediction = pd.Series(np.nan, index=a_predire.index)
    niveau_utilise = pd.Series(len(niveaux), index=a_predire.index, dtype="Int64")

    for rang, colonnes in enumerate(niveaux):
        moyennes = log_cible.groupby(_cle(entrainement, colonnes)).mean()
        valeurs = _cle(a_predire, colonnes).map(moyennes).astype(float)
        a_remplir = prediction.isna() & valeurs.notna()
        prediction[a_remplir] = valeurs[a_remplir]
        niveau_utilise[a_remplir] = rang

    prediction = prediction.fillna(log_cible.mean())
    return np.exp(prediction), niveau_utilise
