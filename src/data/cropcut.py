"""Préparation du fichier GROW-Africa_LSMS_cropcut.

Ces mesures directes de récolte servent de référence de validation pour l'Éthiopie.
"""

from .common import hors_bornes, identifiant_grappe, normaliser_textes

CIBLE = "Yield_ton_ha_"


def reconstruire_menage(df):
    """Reconstruit l'identifiant de ménage par division entière de holder_id par 100.

    holder_id se compose de l'identifiant du ménage suivi d'un rang à deux chiffres.
    Cette reconstruction n'est pas affectée par la troncature des identifiants de
    16 chiffres et remplace les valeurs de substitution de household_id.
    """
    resultat = df.copy()
    menage = (resultat["holder_id"] // 100).astype("Int64")
    resultat["id_menage"] = "ETH_" + menage.astype("string")
    return resultat


def signaler_mesures_incoherentes(df):
    """Signale un poids sec supérieur au poids frais ou un poids frais nul."""
    resultat = df.copy()
    resultat["flag_poids_incoherent"] = (
        (resultat["dryWeightKg"] > resultat["freshWeightKg"] + 1e-9)
        | (resultat["freshWeightKg"] == 0)
    )
    return resultat


def signaler_dates_invalides(df):
    """Signale les dates de mesure impossibles même dans le calendrier éthiopien.

    Ce calendrier compte douze mois de 30 jours et un treizième mois de 6 jours au plus.
    """
    resultat = df.copy()
    mois = resultat["cropCutMonth"]
    jour = resultat["cropCutDay"]
    resultat["flag_date_mesure_invalide"] = mois.notna() & (
        ~mois.between(1, 13) | ((mois == 13) & (jour > 6))
    )
    return resultat


def identifier_mesures(df):
    """Ajoute un identifiant unique de mesure formé de la source et de la position dans le fichier brut.

    La convention est celle d'id_ligne dans survey. Aucune combinaison des colonnes
    d'origine n'identifie une mesure, et la vague de 2018 n'a pas d'identifiant d'exploitant.
    """
    resultat = df.copy()
    resultat["id_mesure"] = resultat["Source"] + "_" + resultat.index.astype(str)
    return resultat


def preparer_cropcut(brut, bornes):
    """Applique l'ensemble des corrections au fichier cropcut brut."""
    df = normaliser_textes(brut)
    df = reconstruire_menage(df)
    df = signaler_mesures_incoherentes(df)
    df = signaler_dates_invalides(df)
    df["annee_recolte"] = df["Year"].astype("Int64")
    df = identifier_mesures(df)
    df["id_grappe"] = "Ethiopia_" + identifiant_grappe(df["GPS_lat"], df["GPS_lon"])
    df["flag_rendement_hors_bornes"] = hors_bornes(df[CIBLE], df["Crop"], bornes)
    return df


def jeu_validation_cropcut(df):
    """Extrait les mesures cohérentes et plausibles."""
    retenues = df[CIBLE].notna() & ~df["flag_poids_incoherent"] & ~df["flag_rendement_hors_bornes"]
    return df[retenues].copy()
