import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from src.features.acquisition import consigner, empreinte_md5, telecharger
from src.features.geographie import (
    contours_zones,
    decomposer_zone,
    descripteurs_geographiques,
    signaler_surface_superieure_zone,
    table_zones,
    verifier_correspondance,
)


class TestDecomposerZone(unittest.TestCase):
    def test_identifiant_simple_et_compose(self):
        self.assertEqual(decomposer_zone("L2GHA15195"), ["L2GHA15195"])
        self.assertEqual(decomposer_zone("[L2GHA15195,L2GHA15196]"), ["L2GHA15195", "L2GHA15196"])
        self.assertEqual(decomposer_zone("[L2GHA15235,L2GHA15235]"), ["L2GHA15235"])
        self.assertEqual(decomposer_zone(float("nan")), [])


class TestContoursZones(unittest.TestCase):
    def setUp(self):
        self.correspondance = pd.DataFrame({
            "GID": ["L1AAA1", "L2AAA1", "L2AAA2", "L2AAA3"],
            "gid_gadm": ["AAA.1_1", "AAA.1.1_1", "AAA.1.2_1", None],
        })
        self.contours = gpd.GeoDataFrame({
            "gid_gadm": ["AAA.1_1", "AAA.1.1_1", "AAA.1.2_1"],
            "geometry": [box(0, 0, 2, 1), box(0, 0, 1, 1), box(1, 0, 2, 1)],
        }, crs="EPSG:4326")

    def test_union_des_unites_et_repli_sur_la_region(self):
        df = pd.DataFrame({
            "zone": ["[L2AAA1,L2AAA2]", "L2AAA3", "L2AAA1", None],
            "L1_GID": ["L1AAA1", "L1AAA1", "L1AAA1", "L1AAA1"],
        })
        zones = table_zones(df, "zone")
        resultat = contours_zones(zones, self.correspondance, self.contours).set_index("zone")

        self.assertEqual(len(resultat), 3)
        self.assertEqual(resultat.loc["[L2AAA1,L2AAA2]", "gid_gadm"], "AAA.1.1_1+AAA.1.2_1")
        self.assertAlmostEqual(resultat.loc["[L2AAA1,L2AAA2]", "geometry"].area, 2.0)
        self.assertFalse(resultat.loc["[L2AAA1,L2AAA2]", "repli_niveau_1"])
        self.assertEqual(resultat.loc["L2AAA3", "gid_gadm"], "AAA.1_1")
        self.assertTrue(resultat.loc["L2AAA3", "repli_niveau_1"])

    def test_verification_limitee_aux_pays_acquis(self):
        correspondance = pd.DataFrame({
            "niveau": [1, 2, 2, 1],
            "pays": ["AAA", "AAA", "AAA", "BBB"],
            "gid_gadm": ["AAA.1_1", "AAA.1.1_1", "AAA.1.2_1", "BBB.1_1"],
            "nom_gadm": ["Nord", "Est", "Autre nom", "Sud"],
        })
        contours = self.contours.assign(nom_gadm=["Nord", "Est", "Ouest"])
        resultat = verifier_correspondance(correspondance, contours)

        self.assertEqual(resultat.loc[1, "codes"], 1)
        self.assertEqual(resultat.loc[1, "part_presents"], 1.0)
        self.assertEqual(resultat.loc[2, "part_meme_nom"], 0.5)

    def test_descripteurs_geographiques(self):
        contours = gpd.GeoDataFrame({"zone": ["Z"], "geometry": [box(0, -1, 2, 1)]}, crs="EPSG:4326")
        resultat = descripteurs_geographiques(contours).iloc[0]

        self.assertAlmostEqual(resultat["latitude"], 0.0, places=6)
        self.assertAlmostEqual(resultat["longitude"], 1.0, places=6)
        self.assertAlmostEqual(resultat["surface_km2"] / (2 * 111.32 * 2 * 110.57), 1.0, delta=0.01)

    def test_surface_superieure_zone(self):
        regional = pd.DataFrame({"GDAM_ID": ["Z", "Z", "Z", "Y"], "areaHa": [50.0, 150.0, None, 500.0]})
        geographie = pd.DataFrame({"zone": ["Z"], "surface_km2": [1.0]})

        self.assertEqual(signaler_surface_superieure_zone(regional, geographie).tolist(), [False, True, False, False])


class TestAcquisition(unittest.TestCase):
    def test_fichier_existant_verifie_par_son_empreinte(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "donnees.bin"
            chemin.write_bytes(b"grow-africa")
            md5 = empreinte_md5(chemin)

            self.assertEqual(telecharger("http://adresse.invalide", chemin, md5=md5), chemin)
            with self.assertRaises(ValueError):
                telecharger("http://adresse.invalide", chemin, md5="0" * 32)
            self.assertFalse(chemin.exists())

    def test_registre(self):
        with tempfile.TemporaryDirectory() as dossier:
            registre = Path(dossier) / "registre.csv"
            chemin = Path(dossier) / "sous" / "donnees.bin"
            chemin.parent.mkdir()
            chemin.write_bytes(b"grow-africa")
            consigner(chemin, "https://exemple.org/donnees.bin", registre)
            consigner(chemin, "https://exemple.org/donnees.bin", registre)
            table = pd.read_csv(registre)

            self.assertEqual(len(table), 2)
            self.assertEqual(table.loc[0, "fichier"], "sous/donnees.bin")
            self.assertEqual(table.loc[0, "octets"], 11)


if __name__ == "__main__":
    unittest.main()
