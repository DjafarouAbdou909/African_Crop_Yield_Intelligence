"""Fenêtres de saison de chaque ligne, à partir des mois de semis et de récolte.

Les mois proviennent par ordre de priorité de la ligne elle-même, du calendrier
HarvestStat de sa zone, de sa région de niveau 1 ou de son pays pour la même culture,
puis du calendrier GGCMI de phase 3 au centroïde de la zone. L'année de récolte sert
d'ancrage. L'année de semis de HarvestStat n'est pas utilisée, car elle contredit les
mois pour 17 045 lignes de regional_modelisation, alors que l'année de récolte
retrouve les sécheresses connues.
"""

import json

import numpy as np
import pandas as pd
import rasterio

from .acquisition import DOSSIER_EXTERNE, telecharger

URL_GGCMI = "https://zenodo.org/api/records/5062513"
DOSSIER_GGCMI = DOSSIER_EXTERNE / "ggcmi"
FICHIER_GGCMI = "{code}_rf_ggcmi_crop_calendar_phase3_v1.01.nc4"
VALEUR_ABSENTE_GGCMI = 1e19

# Culture GGCMI la plus proche par son cycle lorsque la culture n'y figure pas.
CULTURES_GGCMI = {
    "Maize": "mai", "Sorghum": "sor", "Groundnut": "nut", "Millet": "mil", "Rice": "ri1",
    "Cowpea": "bea", "Cassava": "cas", "Sweet potato": "cas", "Beans": "bea", "Soybean": "soy",
    "Sesame": "sor", "Cotton": "cot", "Yam": "cas", "Potato": "pot", "Wheat": "swh",
    "Okra": "mai", "Taro": "cas", "Pigeon pea": "bea", "Barley": "bar", "Sugar cane": "sgc",
    "Fonio": "mil", "Teff": "mil", "Chickpeas": "pea", "Tobacco": "mai", "Lentils": "pea",
    "Oats": "bar", "Pulses": "bea", "Sugar beet": "sgb", "Triticale": "swh",
}
NIVEAUX_CALENDRIER = ["ligne", "zone", "niveau_1", "pays", "ggcmi"]


def telecharger_ggcmi(dossier=DOSSIER_GGCMI):
    """Télécharge les calendriers pluviaux de GGCMI utiles au projet, vérifiés par leur MD5."""
    with open(telecharger(URL_GGCMI, dossier / "zenodo_5062513.json"), encoding="utf-8") as fichier:
        fichiers = {f["key"]: f for f in json.load(fichier)["files"]}
    for code in sorted(set(CULTURES_GGCMI.values())):
        f = fichiers[FICHIER_GGCMI.format(code=code)]
        telecharger(f["links"]["self"], dossier / f["key"], md5=f["checksum"].split(":")[1])


def mois_du_jour(jour):
    """Convertit un jour de l'année d'une année non bissextile en mois."""
    jour = np.asarray(jour, dtype=float)
    mois = pd.to_datetime(np.clip(np.nan_to_num(jour, nan=1), 1, 365) - 1, unit="D", origin="2001-01-01").month
    return np.where(np.isnan(jour), np.nan, mois)


def lire_ggcmi(culture, latitudes, longitudes, dossier=DOSSIER_GGCMI):
    """Retourne les mois de semis et de maturité GGCMI d'une culture en une série de points."""
    resultat = []
    for variable in ["planting_day", "maturity_day"]:
        chemin = f'netcdf:"{dossier / FICHIER_GGCMI.format(code=CULTURES_GGCMI[culture])}":{variable}'
        with rasterio.open(chemin) as source:
            grille = source.read(1)
            lignes, colonnes = rasterio.transform.rowcol(source.transform, np.asarray(longitudes), np.asarray(latitudes))
        valeurs = grille[np.clip(lignes, 0, grille.shape[0] - 1), np.clip(colonnes, 0, grille.shape[1] - 1)]
        resultat.append(mois_du_jour(np.where(valeurs > VALEUR_ABSENTE_GGCMI, np.nan, valeurs)))
    return resultat


def calendriers_harveststat(regional):
    """Retourne le calendrier principal HarvestStat par culture à trois niveaux géographiques.

    La saison principale d'un lieu et d'une culture est celle dont la surface récoltée
    cumulée est la plus grande, et ses mois sont les plus fréquents. Le résultat associe
    à chaque niveau, zone, niveau_1 ou pays, une table indexée par le lieu et la culture.
    """
    hs = regional.dropna(subset=["planting_month", "harvest_month"]).assign(
        surface=lambda x: x["areaHa"].fillna(0) + 1e-9
    )
    tables = {}
    for niveau, cle in [("zone", "GDAM_ID"), ("niveau_1", "L1_GID"), ("pays", "L0_GID")]:
        poids = hs.groupby([cle, "crop", "saison", "planting_month", "harvest_month"])["surface"].sum().reset_index()
        principale = poids.groupby([cle, "crop", "saison"])["surface"].transform("sum")
        poids = poids.assign(total_saison=principale).sort_values(
            ["total_saison", "surface"], ascending=False, kind="mergesort"
        )
        tables[niveau] = poids.drop_duplicates([cle, "crop"]).set_index([cle, "crop"])[["planting_month", "harvest_month"]]
    return tables


def attribuer_calendrier(df, tables, cles, colonne_culture, latitudes, longitudes, dossier=DOSSIER_GGCMI):
    """Attribue à chaque ligne des mois de semis et de récolte et le niveau qui les fournit.

    cles associe les niveaux zone, niveau_1 et pays aux colonnes de df qui les
    identifient. Les mois propres à la ligne sont repris s'ils figurent dans df.
    """
    semis = df["planting_month"].astype(float).to_numpy().copy() if "planting_month" in df else np.full(len(df), np.nan)
    recolte = df["harvest_month"].astype(float).to_numpy().copy() if "harvest_month" in df else np.full(len(df), np.nan)
    niveau = np.where(~np.isnan(semis) & ~np.isnan(recolte), "ligne", None).astype(object)
    culture = df[colonne_culture].to_numpy()
    for nom in ["zone", "niveau_1", "pays"]:
        manquant = pd.isna(niveau)
        table = tables[nom]
        index = pd.MultiIndex.from_arrays([df[cles[nom]].to_numpy()[manquant], culture[manquant]])
        trouve = table.reindex(index)
        disponible = trouve["planting_month"].notna().to_numpy()
        positions = np.flatnonzero(manquant)[disponible]
        semis[positions] = trouve["planting_month"].to_numpy()[disponible]
        recolte[positions] = trouve["harvest_month"].to_numpy()[disponible]
        niveau[positions] = nom
    latitudes, longitudes = np.asarray(latitudes, dtype=float), np.asarray(longitudes, dtype=float)
    for nom_culture in pd.unique(culture):
        if nom_culture not in CULTURES_GGCMI:
            continue
        cibles = np.flatnonzero(pd.isna(niveau) & (culture == nom_culture) & ~np.isnan(latitudes))
        if len(cibles) == 0:
            continue
        s, r = lire_ggcmi(nom_culture, latitudes[cibles], longitudes[cibles], dossier)
        valides = ~np.isnan(s) & ~np.isnan(r)
        semis[cibles[valides]], recolte[cibles[valides]] = s[valides], r[valides]
        niveau[cibles[valides]] = "ggcmi"
    return pd.DataFrame({"mois_semis": semis, "mois_recolte": recolte, "source_calendrier": niveau}, index=df.index)


def fenetre_saison(annee_recolte, mois_semis, mois_recolte):
    """Retourne le premier et le dernier jour de la saison qui s'achève l'année de récolte.

    La saison commence l'année précédente lorsque le mois de semis suit le mois de
    récolte. Un mois de semis égal au mois de récolte désigne un cycle de douze mois
    qui commence le mois suivant de l'année précédente.
    """
    annee = pd.Series(annee_recolte, dtype="Float64").astype(float).to_numpy()
    semis = np.asarray(mois_semis, dtype=float)
    recolte = np.asarray(mois_recolte, dtype=float)
    valides = ~np.isnan(annee) & ~np.isnan(semis) & ~np.isnan(recolte)
    duree = np.where(valides, (recolte - semis) % 12, 0)
    duree = np.where(duree == 0, 12, duree + 1)
    fin_mois = np.where(valides, annee * 12 + recolte - 1, 2000 * 12).astype(int)
    debut_mois = fin_mois - duree + 1
    debut = pd.to_datetime({"year": debut_mois // 12, "month": debut_mois % 12 + 1, "day": 1})
    fin = pd.to_datetime({"year": fin_mois // 12, "month": fin_mois % 12 + 1, "day": 1}) + pd.offsets.MonthEnd(0)
    return debut.where(valides).to_numpy(), fin.where(valides).to_numpy()

