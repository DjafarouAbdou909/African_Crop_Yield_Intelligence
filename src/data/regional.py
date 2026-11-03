"""Préparation du fichier GROW-Africa_Regional.

Chaque fonction retourne une copie corrigée et ajoute, lorsque c'est utile, une
colonne d'indicateur préfixée par flag_ afin de conserver la traçabilité des lignes
modifiées ou écartées.
"""

import numpy as np
import pandas as pd

from .common import (
    bornes_filtre_auteurs,
    hors_bornes,
    normaliser_textes,
    signaler_hierarchie_incoherente,
)

CODES_SPECIAUX = [-999, -99]
COLONNES_MESURES = ["areaHa", "productionTon", "yieldTonHa"]
L0_GID_GHANA = "L0GHA086"
LIBELLES_PAYS = {
    "DRC": "Democratic Republic of the Congo",
    "Tanzania, United Republic of": "Tanzania",
}
SYSTEMES_GLOBAUX = {"All (PS)"}
SOURCE_PRIORITAIRE = "HarvestStat"
SAISONS_EQUIVALENTES = {"Meher": "Main"}
NIVEAUX_MODELISATION = [1, 2]


def remplacer_codes_speciaux(df):
    """Remplace les codes -999 et -99 par des valeurs manquantes.

    Ces codes ont été repris dans le calcul du rendement par les auteurs. Tout
    rendement négatif qui en résulte est donc également invalidé.
    """
    resultat = df.copy()
    for colonne in COLONNES_MESURES:
        resultat[colonne] = resultat[colonne].mask(resultat[colonne].isin(CODES_SPECIAUX))
    resultat["yieldTonHa"] = resultat["yieldTonHa"].mask(resultat["yieldTonHa"] < 0)
    return resultat


def corriger_inversion_surface_production(df, tolerance=1e-3):
    """Permute surface et production lorsque le rendement vaut leur rapport inverse.

    Sur ces lignes, le rendement publié est plausible et ce sont les colonnes
    areaHa et productionTon qui sont inversées. Les lignes qui ne vérifient aucune
    des deux relations sont signalées sans être modifiées.
    """
    resultat = df.copy()
    surface = resultat["areaHa"]
    production = resultat["productionTon"]
    rendement = resultat["yieldTonHa"]

    testables = (surface > 0) & (production > 0) & (rendement > 0)
    conformes = testables & np.isclose(rendement, production / surface, rtol=tolerance)
    inversees = testables & ~conformes & np.isclose(rendement, surface / production, rtol=tolerance)

    resultat.loc[inversees, ["areaHa", "productionTon"]] = (
        resultat.loc[inversees, ["productionTon", "areaHa"]].to_numpy()
    )
    resultat["flag_surface_production_permutees"] = inversees
    resultat["flag_relation_rendement_inexpliquee"] = testables & ~conformes & ~inversees
    return resultat


def corriger_identifiants_ghana(df):
    """Ramène les 25 codes pays du Ghana au code unique utilisé par les autres fichiers."""
    resultat = df.copy()
    for colonne in ["L0_GID", "GDAM_ID"]:
        ghana = resultat[colonne].str.startswith("L0GHA", na=False)
        resultat.loc[ghana, colonne] = L0_GID_GHANA
    return resultat


def harmoniser_pays(df):
    """Unifie les libellés d'un même pays afin qu'un L0_GID porte un seul nom."""
    resultat = df.copy()
    resultat["country"] = resultat["country"].replace(LIBELLES_PAYS)
    return resultat


def reconstruire_niveau(df):
    """Déduit le niveau administratif manquant de la profondeur des identifiants GADM.

    Un nom de niveau 2 renseigné porte le niveau à au moins 2, car il désigne une
    unité de niveau 2 même lorsque seul l'identifiant de sa région est fourni. Une
    ligne qui ne dispose que de L0_GID reste ambiguë, car elle peut désigner une
    unité infranationale non rattachée. Une ligne dont le niveau dépasse la profondeur
    de ses identifiants est signalée comme incomplète.
    """
    resultat = df.copy()
    profondeur = resultat[["L1_GID", "L2_GID", "L3_GID"]].notna().sum(axis=1)
    manquant = resultat["level"].isna()
    deductible = manquant & (profondeur > 0)
    niveau_nomme = np.where(resultat["admin_2"].notna(), 2, 0)

    resultat.loc[deductible, "level"] = np.maximum(profondeur, niveau_nomme)[deductible]
    resultat["level"] = resultat["level"].astype("Int64")
    resultat["flag_niveau_ambigu"] = manquant & (profondeur == 0)
    resultat["flag_gid_incomplet"] = (resultat["level"] > profondeur).fillna(False).astype(bool)
    return resultat


def harmoniser_saisons(df):
    """Ajoute une colonne saison qui unifie les libellés désignant la même saison.

    En Éthiopie, HarvestStat nomme Meher la saison principale que FAO_subnational et
    RCeA nomment Main pour les mêmes zones et les mêmes années. Les autres libellés
    sont conservés tels quels, faute de preuve de leur équivalence.
    """
    resultat = df.copy()
    resultat["saison"] = resultat["season_name"].replace(SAISONS_EQUIVALENTES)
    return resultat


def zone_geographique(df):
    """Retourne l'identifiant GADM le plus fin disponible pour chaque ligne."""
    return (
        df["GDAM_ID"]
        .fillna(df["L3_GID"])
        .fillna(df["L2_GID"])
        .fillna(df["L1_GID"])
        .fillna(df["L0_GID"])
    )


def signaler_unites_hors_gadm(df):
    """Signale les lignes dont l'unité administrative n'a pas d'identifiant GADM propre.

    Ces lignes n'ont pas de GDAM_ID. Elles décrivent des unités de niveau 2 créées
    après la carte GADM, comme les départements nigériens issus du découpage de 2011,
    et portent l'identifiant de l'unité qui les contenait. Leur zone ne peut donc pas
    être distinguée de celle de l'unité mère, ni recevoir un contour.
    """
    resultat = df.copy()
    resultat["flag_unite_hors_gadm"] = resultat["GDAM_ID"].isna()
    return resultat


def selectionner_ligne_par_cellule(df):
    """Retient une seule ligne par zone, culture, saison harmonisée et année de récolte.

    L'ordre de priorité est le suivant. Une ligne dotée d'un rendement passe avant
    une ligne sans rendement. Le système de production global, ou non précisé, passe
    avant un système détaillé. La source HarvestStat passe avant les autres sources.
    À égalité, la ligne de plus grande surface est retenue. Les autres lignes sont
    signalées par flag_doublon_cellule et ne sont pas supprimées. Les unités hors
    GADM ne participent pas à la sélection, car leur zone est celle de l'unité mère.
    """
    resultat = df.copy()
    candidates = ~resultat["flag_unite_hors_gadm"]
    systeme = resultat["crop_production_system"]
    tri = pd.DataFrame({
        "zone": zone_geographique(resultat),
        "culture": resultat["crop"],
        "saison": resultat["saison"],
        "annee": resultat["harvest_year"],
        "rang_rendement": resultat["yieldTonHa"].isna().astype(int),
        "rang_systeme": (~(systeme.isna() | systeme.isin(SYSTEMES_GLOBAUX))).astype(int),
        "rang_source": (resultat["Source"] != SOURCE_PRIORITAIRE).astype(int),
        "surface": resultat["areaHa"],
    }, index=resultat.index)[candidates]

    tri = tri.sort_values(
        ["rang_rendement", "rang_systeme", "rang_source", "surface"],
        ascending=[True, True, True, False],
        na_position="last",
        kind="mergesort",
    )
    ecartees = tri.duplicated(subset=["zone", "culture", "saison", "annee"], keep="first")
    resultat["flag_doublon_cellule"] = ecartees.reindex(resultat.index, fill_value=False)
    return resultat


def preparer_regional(brut):
    """Applique l'ensemble des corrections au fichier regional brut.

    Retourne le tableau corrigé avec ses indicateurs et les bornes de plausibilité
    par culture, qui servent aussi aux fichiers survey et cropcut.
    """
    df = normaliser_textes(brut)
    df = remplacer_codes_speciaux(df)
    df = corriger_inversion_surface_production(df)
    df = corriger_identifiants_ghana(df)
    df = harmoniser_pays(df)
    df = harmoniser_saisons(df)
    df = reconstruire_niveau(df)
    df = signaler_unites_hors_gadm(df)
    df = signaler_hierarchie_incoherente(df)

    bornes = bornes_filtre_auteurs(df["yieldTonHa"], df["crop"])
    df["flag_rendement_hors_bornes"] = hors_bornes(df["yieldTonHa"], df["crop"], bornes)
    df = selectionner_ligne_par_cellule(df)
    return df, bornes


def jeu_modelisation_regional(df):
    """Extrait les lignes utilisables comme cible, aux niveaux administratifs 1 et 2.

    Sont exclues les lignes sans rendement, les unités hors GADM, les doublons de
    cellule et les rendements hors des bornes de plausibilité de leur culture.
    """
    retenues = (
        df["level"].isin(NIVEAUX_MODELISATION)
        & df["yieldTonHa"].notna()
        & ~df["flag_unite_hors_gadm"]
        & ~df["flag_doublon_cellule"]
        & ~df["flag_rendement_hors_bornes"]
    )
    return df[retenues].copy()
