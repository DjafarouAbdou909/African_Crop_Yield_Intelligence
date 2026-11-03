"""Raccordement des zones GROW-Africa aux contours administratifs GADM.

Les identifiants L1_GID et L2_GID sont propres à GROW-Africa. La version 2.0 de
l'archive Zenodo fournit des tables qui les relient aux identifiants GADM, et les
contours sont ceux de GADM 4.1, téléchargés pays par pays. Une zone de regional peut
réunir plusieurs unités GADM, lorsque son identifiant énumère plusieurs codes entre
crochets. Une unité de niveau 2 sans correspondance GADM reçoit le contour de sa
région de niveau 1, et ce repli est signalé.
"""

import re
import zipfile

import geopandas as gpd
import pandas as pd
import pyogrio

from .acquisition import DOSSIER_EXTERNE, telecharger

VERSION_GADM = "4.1"
URL_GADM = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{pays}.gpkg"
URL_CORRESPONDANCE = "https://zenodo.org/api/records/16544448/files/GADM-Look-Up-Tables.zip/content"
MD5_CORRESPONDANCE = "22f28f4b7edbec4365a260a57367a09e"
DOSSIER_GADM = DOSSIER_EXTERNE / "gadm"
PROJECTION_EQUIVALENTE = "EPSG:6933"

_CODE_GROW = re.compile(r"L\d[A-Z]{3}\d+")


def charger_correspondance(dossier=DOSSIER_GADM):
    """Retourne la table qui relie chaque identifiant GROW-Africa de niveau 1 ou 2 à GADM.

    Les colonnes sont GID, niveau, pays, gid_gadm et nom_gadm. Les lignes répétées à
    l'identique sur le couple GID et gid_gadm sont fusionnées, et un identifiant
    GROW-Africa associé à deux unités GADM distinctes provoque une erreur.
    """
    archive = telecharger(URL_CORRESPONDANCE, dossier / "GADM-Look-Up-Tables.zip", md5=MD5_CORRESPONDANCE)
    tables = []
    with zipfile.ZipFile(archive) as zf:
        for niveau in [1, 2]:
            nom = next(n for n in zf.namelist() if n.endswith(f"gadm_level{niveau}_ecg.xlsx"))
            table = pd.read_excel(zf.open(nom))
            tables.append(pd.DataFrame({
                "GID": table["GID"],
                "niveau": niveau,
                "pays": table["GID_0"],
                "gid_gadm": table[f"GID_{niveau}"],
                "nom_gadm": table[f"NAME_{niveau}"],
            }))
    correspondance = pd.concat(tables, ignore_index=True).drop_duplicates(["GID", "gid_gadm"])
    if correspondance["GID"].duplicated().any():
        raise ValueError("Un identifiant GROW-Africa correspond à plusieurs unités GADM")
    return correspondance.reset_index(drop=True)


def decomposer_zone(identifiant):
    """Retourne la liste des codes GROW-Africa contenus dans un identifiant de zone.

    Un identifiant simple donne une liste d'un élément, un identifiant entre crochets
    donne ses codes sans doublon, dans leur ordre d'apparition.
    """
    if pd.isna(identifiant):
        return []
    return list(dict.fromkeys(_CODE_GROW.findall(identifiant)))


def telecharger_gadm(pays, dossier=DOSSIER_GADM):
    """Télécharge le fichier GADM 4.1 d'un pays désigné par son code ISO à trois lettres."""
    return telecharger(URL_GADM.format(pays=pays), dossier / f"gadm41_{pays}.gpkg")


def charger_contours(pays, niveau, dossier=DOSSIER_GADM):
    """Retourne les contours GADM d'un niveau pour une liste de pays, avec gid_gadm et nom_gadm.

    Un pays dont le fichier GADM ne descend pas jusqu'au niveau demandé est ignoré,
    comme le Lesotho au niveau 2.
    """
    morceaux = []
    for code in sorted(set(pays)):
        chemin = telecharger_gadm(code, dossier)
        if f"ADM_ADM_{niveau}" not in pyogrio.list_layers(chemin)[:, 0]:
            continue
        couche = gpd.read_file(chemin, layer=f"ADM_ADM_{niveau}")
        morceaux.append(couche[[f"GID_{niveau}", f"NAME_{niveau}", "geometry"]].rename(
            columns={f"GID_{niveau}": "gid_gadm", f"NAME_{niveau}": "nom_gadm"}
        ))
    return gpd.GeoDataFrame(pd.concat(morceaux, ignore_index=True), crs=morceaux[0].crs)


def table_zones(df, colonne_zone, colonne_parent="L1_GID"):
    """Associe à chaque zone ses codes GROW-Africa et le code de sa région de niveau 1.

    Retourne une ligne par couple de zone et de code, avec les colonnes zone, GID et
    parent. Le parent sert de repli lorsque le code n'a pas de contour GADM.
    """
    zones = df[[colonne_zone, colonne_parent]].dropna(subset=[colonne_zone]).drop_duplicates(colonne_zone)
    zones = zones.rename(columns={colonne_zone: "zone", colonne_parent: "parent"})
    zones["GID"] = zones["zone"].map(decomposer_zone)
    return zones.explode("GID")[["zone", "GID", "parent"]].reset_index(drop=True)


def contours_zones(zones, correspondance, contours):
    """Construit le contour de chaque zone par union des unités GADM qui la composent.

    zones provient de table_zones, contours réunit les niveaux 1 et 2 de GADM. Le
    résultat contient zone, gid_gadm, les codes GADM réunis séparés par un signe plus,
    repli_niveau_1, vrai lorsqu'au moins un code a reçu le contour de sa région, et
    geometry. Une zone dont aucun code ne trouve de contour est absente du résultat.
    """
    gadm = correspondance.dropna(subset=["gid_gadm"]).set_index("GID")["gid_gadm"]
    lien = zones.assign(gid_gadm=zones["GID"].map(gadm))
    sans_contour = lien["gid_gadm"].isna()
    lien.loc[sans_contour, "gid_gadm"] = lien.loc[sans_contour, "parent"].map(gadm)
    lien["repli_niveau_1"] = sans_contour & lien["gid_gadm"].notna()

    lien = lien.dropna(subset=["gid_gadm"]).merge(contours[["gid_gadm", "geometry"]], on="gid_gadm")
    lien = gpd.GeoDataFrame(lien, geometry="geometry", crs=contours.crs)
    resultat = lien.dissolve(
        by="zone",
        aggfunc={"gid_gadm": lambda codes: "+".join(sorted(set(codes))), "repli_niveau_1": "any"},
    )
    return resultat.reset_index()


def descripteurs_geographiques(contours):
    """Retourne la surface en kilomètres carrés et les coordonnées du centroïde de chaque zone.

    La surface est calculée dans une projection à surfaces équivalentes, et le
    centroïde y est calculé avant d'être ramené en latitude et longitude.
    """
    projete = contours.to_crs(PROJECTION_EQUIVALENTE)
    centroides = gpd.GeoSeries(projete.geometry.centroid, crs=PROJECTION_EQUIVALENTE).to_crs("EPSG:4326")
    return pd.DataFrame({
        "zone": contours["zone"].to_numpy(),
        "surface_km2": (projete.geometry.area / 1e6).to_numpy(),
        "latitude": centroides.y.to_numpy(),
        "longitude": centroides.x.to_numpy(),
    })


def verifier_correspondance(correspondance, contours):
    """Mesure l'accord entre la table de correspondance et les contours GADM acquis.

    Seuls les pays dont les contours ont été acquis sont examinés. Retourne, par
    niveau, le nombre de codes GADM de la table, la part présente dans les contours et
    la part dont le nom coïncide. Un accord complet confirme que la table vise la
    version de GADM téléchargée.
    """
    table = correspondance.dropna(subset=["gid_gadm"]).drop_duplicates("gid_gadm")
    table = table[table["pays"].isin(contours["gid_gadm"].str[:3])]
    noms = contours.drop_duplicates("gid_gadm").set_index("gid_gadm")["nom_gadm"]
    present = table["gid_gadm"].isin(noms.index)
    meme_nom = table["nom_gadm"].eq(table["gid_gadm"].map(noms))
    return pd.DataFrame({
        "codes": table.groupby("niveau").size(),
        "part_presents": present.groupby(table["niveau"]).mean(),
        "part_meme_nom": meme_nom.groupby(table["niveau"]).mean(),
    })


def zone_survey(df):
    """Retourne la zone administrative de repli d'une parcelle, son L2_GID ou à défaut son L1_GID."""
    return df["L2_GID"].fillna(df["L1_GID"])


def construire(regional, survey, dossier=DOSSIER_GADM):
    """Construit les contours des zones de regional et de survey.

    Retourne les contours de regional, ceux des zones de repli de survey et la table
    de correspondance. Les fichiers GADM manquants sont téléchargés.
    """
    correspondance = charger_correspondance(dossier)
    pays = correspondance.loc[correspondance["GID"].isin(regional["L1_GID"]), "pays"].unique()
    contours = pd.concat([charger_contours(pays, niveau, dossier) for niveau in [1, 2]], ignore_index=True)
    contours = gpd.GeoDataFrame(contours, geometry="geometry", crs="EPSG:4326")

    zones_regional = table_zones(regional, "GDAM_ID")
    zones_survey = table_zones(survey.assign(zone=zone_survey(survey)), "zone")
    return (
        contours_zones(zones_regional, correspondance, contours),
        contours_zones(zones_survey, correspondance, contours),
        correspondance,
        contours,
    )


def signaler_surface_superieure_zone(regional, geographie):
    """Signale les lignes dont la surface récoltée dépasse la surface de leur zone.

    Une culture ne peut occuper plus que la totalité de sa zone au cours d'une saison.
    Un tel dépassement révèle une surface ou une localisation erronée, par exemple une
    valeur nationale attribuée à une seule région. Les lignes sans surface ou sans
    contour ne sont pas signalées.
    """
    surface = regional["GDAM_ID"].map(geographie.set_index("zone")["surface_km2"])
    return (regional["areaHa"] > surface * 100).rename("flag_surface_superieure_zone")
