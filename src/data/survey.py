"""Préparation du fichier GROW-Africa_LSMS_survey.

La cible retenue est YieldUsingGPS_ton_ha_, fondée sur une surface mesurée par GPS.
"""

from .common import hors_bornes, identifiant_grappe, normaliser_textes, signaler_hierarchie_incoherente

CIBLE = "YieldUsingGPS_ton_ha_"
LIBELLES_PAYS = {"Cote dIvoire": "Côte dIvoire"}
SEUIL_SURFACE_ABERRANTE_HA = 1000


def supprimer_doublons_exacts(df):
    """Supprime les copies exactes d'une ligne précédente.

    Aucune clé ne permet de distinguer ces lignes d'un doublon d'enregistrement.
    Les conserver exposerait la même observation à l'entraînement et au test.
    """
    return df[~df.duplicated()].copy()


def harmoniser_pays(df):
    """Aligne le libellé de la Côte d'Ivoire sur celui du fichier regional."""
    resultat = df.copy()
    resultat["Country"] = resultat["Country"].replace(LIBELLES_PAYS)
    return resultat


def harmoniser_annee(df):
    """Construit l'année de récolte à partir de la fin de campagne agricole.

    AgYearEnd vaut toujours AgYearStart augmenté d'un an. Sa valeur manquante est
    donc déduite de AgYearStart.
    """
    resultat = df.copy()
    resultat["AgYearEnd"] = resultat["AgYearEnd"].fillna(resultat["AgYearStart"] + 1)
    resultat["annee_recolte"] = resultat["AgYearEnd"].astype("Int64")
    return resultat


def signaler_valeurs_impossibles(df):
    """Signale les parts de culture supérieures à 100 et les surfaces aberrantes."""
    resultat = df.copy()
    resultat["flag_prccrop_invalide"] = resultat["prcCrop"] > 100
    resultat["flag_surface_aberrante"] = (
        (resultat["ReportedArea_ha_"] > SEUIL_SURFACE_ABERRANTE_HA)
        | (resultat["GPSArea_ha_"] > SEUIL_SURFACE_ABERRANTE_HA)
    )
    return resultat


def construire_identifiants(df):
    """Crée un identifiant de ligne, de ménage et de grappe spatiale.

    L'identifiant de ligne reprend la position de la ligne dans le fichier brut.
    L'identifiant de ménage est laissé manquant lorsque hhid est absent ou tronqué
    par la notation scientifique, ce qui impose un regroupement par grappe.
    """
    resultat = df.copy()
    hhid = resultat["hhid"]
    tronque = hhid.str.contains("e+", regex=False).fillna(False).astype(bool)

    resultat["id_ligne"] = resultat["Source"] + "_" + resultat.index.astype(str)
    resultat["flag_hhid_tronque"] = tronque
    resultat["id_menage"] = (resultat["Country"] + "_" + hhid).where(hhid.notna() & ~tronque)
    resultat["id_grappe"] = resultat["Country"] + "_" + identifiant_grappe(resultat["GPS_lat"], resultat["GPS_lon"])
    return resultat


def preparer_survey(brut, bornes):
    """Applique l'ensemble des corrections au fichier survey brut.

    Les bornes de plausibilité par culture proviennent du fichier regional.
    """
    df = normaliser_textes(brut)
    df = supprimer_doublons_exacts(df)
    df = harmoniser_pays(df)
    df = harmoniser_annee(df)
    df = signaler_valeurs_impossibles(df)
    df = construire_identifiants(df)
    df = signaler_hierarchie_incoherente(df)
    df["flag_rendement_hors_bornes"] = hors_bornes(df[CIBLE], df["Crop"], bornes)
    return df


def jeu_modelisation_survey(df):
    """Extrait les lignes dont la cible est renseignée et plausible."""
    retenues = (
        df[CIBLE].notna()
        & ~df["flag_rendement_hors_bornes"]
        & ~df["flag_prccrop_invalide"]
        & ~df["flag_surface_aberrante"]
    )
    return df[retenues].copy()
