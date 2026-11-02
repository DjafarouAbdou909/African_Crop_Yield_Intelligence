"""Chargement des fichiers bruts GROW-Africa avec un cache local.

La lecture des fichiers Excel prend une dizaine de minutes. Le cache est un fichier
pickle stocké dans data/interim et nommé d'après l'empreinte SHA-256 du fichier
source, si bien qu'une modification du fichier brut invalide automatiquement le cache.
Les fichiers bruts ne sont jamais modifiés.
"""

import hashlib
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_BRUT = RACINE / "data" / "raw"
DOSSIER_INTERMEDIAIRE = RACINE / "data" / "interim"
DOSSIER_TRAITE = RACINE / "data" / "processed"

FICHIERS_BRUTS = {
    "cropcut": "GROW-Africa_LSMS_cropcut.xlsx",
    "survey": "GROW-Africa_LSMS_survey.xlsx",
    "point": "GROW-Africa_Point.xlsx",
    "regional": "GROW-Africa_Regional.xlsx",
}


def empreinte_sha256(chemin):
    """Retourne l'empreinte SHA-256 d'un fichier."""
    empreinte = hashlib.sha256()
    with open(chemin, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1 << 20), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def charger_brut(nom, utiliser_cache=True):
    """Charge un fichier brut par son nom court, cropcut, survey, point ou regional."""
    chemin = DOSSIER_BRUT / FICHIERS_BRUTS[nom]
    cache = DOSSIER_INTERMEDIAIRE / f"{nom}_{empreinte_sha256(chemin)[:16]}.pkl"

    if utiliser_cache and cache.exists():
        return pd.read_pickle(cache)

    df = pd.read_excel(chemin)
    if utiliser_cache:
        DOSSIER_INTERMEDIAIRE.mkdir(parents=True, exist_ok=True)
        df.to_pickle(cache)
    return df
