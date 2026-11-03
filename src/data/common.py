"""Fonctions de préparation partagées entre les fichiers GROW-Africa."""

import pandas as pd

BOM = "﻿"
JETONS_MANQUANTS = {"[]", "none"}


def normaliser_textes(df):
    """Nettoie les colonnes texte sans modifier les colonnes numériques.

    Le caractère invisible BOM et les espaces superflus sont supprimés. Les jetons
    qui dissimulent une valeur manquante, à savoir [] et none, deviennent des
    valeurs manquantes.
    """
    resultat = df.copy()
    for colonne in resultat.columns:
        serie = resultat[colonne]
        if (
            pd.api.types.is_numeric_dtype(serie)
            or pd.api.types.is_bool_dtype(serie)
            or pd.api.types.is_datetime64_any_dtype(serie)
        ):
            continue
        texte = serie.str.replace(BOM, "", regex=False).str.strip()
        resultat[colonne] = texte.mask(texte.isin(JETONS_MANQUANTS))
    return resultat


def bornes_filtre_auteurs(rendements, cultures):
    """Calcule les bornes de plausibilité par culture selon le filtre des auteurs.

    L'article GROW-Africa juge aberrant un rendement inférieur à 10 % de la médiane
    ou supérieur à 200 % du 98e percentile de la distribution régionale de la
    culture. Seuls les rendements strictement positifs entrent dans le calcul.
    """
    positifs = rendements.where(rendements > 0)
    statistiques = positifs.groupby(cultures).agg(
        mediane="median",
        p98=lambda serie: serie.quantile(0.98),
    )
    return pd.DataFrame({
        "borne_basse": 0.10 * statistiques["mediane"],
        "borne_haute": 2.00 * statistiques["p98"],
    })


def hors_bornes(rendements, cultures, bornes):
    """Indique les rendements situés hors des bornes de leur culture.

    Un rendement nul ou négatif est toujours signalé, y compris pour une culture
    dépourvue de bornes faute de rendement positif. Un rendement manquant n'est
    jamais signalé.
    """
    seuils = bornes.reindex(cultures.to_numpy())
    trop_bas = (rendements.to_numpy() <= 0) | (rendements.to_numpy() < seuils["borne_basse"].to_numpy())
    trop_haut = rendements.to_numpy() > seuils["borne_haute"].to_numpy()
    return pd.Series(trop_bas | trop_haut, index=rendements.index)


def identifiant_grappe(latitudes, longitudes):
    """Construit un identifiant de grappe spatiale à partir de coordonnées identiques.

    Les observations LSMS d'une même grappe d'enquête partagent les mêmes
    coordonnées déplacées. L'identifiant est manquant si une coordonnée l'est.
    """
    presentes = latitudes.notna() & longitudes.notna()
    identifiant = latitudes.astype(str) + "_" + longitudes.astype(str)
    return identifiant.where(presentes)


def signaler_hierarchie_incoherente(df):
    """Signale les lignes dont un identifiant GADM est rattaché à plusieurs parents.

    Un identifiant de niveau 2 doit appartenir à un seul niveau 1, et ainsi de suite.
    Le contrôle s'applique après normalisation des textes.
    """
    resultat = df.copy()
    incoherente = pd.Series(False, index=resultat.index)
    for enfant, parent in [("L1_GID", "L0_GID"), ("L2_GID", "L1_GID"), ("L3_GID", "L2_GID")]:
        nb_parents = resultat.groupby(enfant)[parent].transform("nunique")
        incoherente |= nb_parents.gt(1)
    resultat["flag_hierarchie_gid_incoherente"] = incoherente
    return resultat
