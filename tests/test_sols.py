import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from rasterio.windows import Window
from shapely.geometry import box

from src.features.sols import (
    CRS_SOILGRIDS,
    PROFONDEURS,
    chemin_couche,
    couche_0_30,
    decouper,
    moyennes_lieux,
    pixels_lieux,
    url_source,
    verifier_fenetre,
)

TRANSFORMATION = Affine(1000.0, 0.0, 0.0, 0.0, -1000.0, 10000.0)


def ecrire(chemin, valeurs, transformation=TRANSFORMATION, crs=CRS_SOILGRIDS):
    profil = {"driver": "GTiff", "height": valeurs.shape[0], "width": valeurs.shape[1], "count": 1,
              "dtype": "int16", "nodata": -32768}
    if crs is not None:
        profil.update(crs=crs, transform=transformation)
    with rasterio.open(chemin, "w", **profil) as raster:
        raster.write(valeurs.astype(np.int16), 1)


class TestSols(unittest.TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp())

    def test_url_du_ph_dans_l_apercu_a_250_m(self):
        self.assertTrue(url_source("phh2o", "0-5cm").endswith("data/phh2o/phh2o_0-5cm_mean.vrt.ovr"))
        self.assertTrue(url_source("clay", "5-15cm").endswith("1000m/clay/clay_5-15cm_mean_1000.tif"))

    def test_decoupage_d_une_source_non_georeferencee(self):
        valeurs = np.arange(200).reshape(10, 20)
        ecrire(self.dossier / "source.tif", valeurs, crs=None)
        decouper(self.dossier / "source.tif", self.dossier / "decoupe.tif", Window(5, 2, 4, 3), (10, 20),
                 TRANSFORMATION)
        with rasterio.open(self.dossier / "decoupe.tif") as raster:
            np.testing.assert_array_equal(raster.read(1), valeurs[2:5, 5:9])
            self.assertEqual(raster.transform, Affine(1000.0, 0.0, 5000.0, 0.0, -1000.0, 8000.0))
            self.assertEqual(raster.nodata, -32768)

    def test_decoupage_refuse_une_grille_inattendue(self):
        ecrire(self.dossier / "source.tif", np.zeros((10, 20)), transformation=Affine(250.0, 0, 0, 0, -250.0, 0))
        with self.assertRaises(ValueError):
            decouper(self.dossier / "source.tif", self.dossier / "decoupe.tif", Window(0, 0, 2, 2), (10, 20),
                     TRANSFORMATION)
        with self.assertRaises(ValueError):
            decouper(self.dossier / "source.tif", self.dossier / "decoupe.tif", Window(0, 0, 2, 2), (11, 20),
                     TRANSFORMATION)

    def test_moyenne_0_30_ponderee_par_epaisseur(self):
        for profondeur, valeur in zip(PROFONDEURS, [100, 200, 400]):
            valeurs = np.full((2, 2), valeur)
            if profondeur == "15-30cm":
                valeurs[1, 1] = -32768
            ecrire(chemin_couche("clay", profondeur, self.dossier), valeurs)
        couche = couche_0_30("clay", self.dossier)
        self.assertAlmostEqual(couche[0, 0], (5 * 100 + 10 * 200 + 15 * 400) / 30 / 10, places=5)
        self.assertTrue(np.isnan(couche[1, 1]))

    def test_pixels_par_centre_puis_par_contact(self):
        lieux = gpd.GeoDataFrame({"zone": ["carre", "minuscule", "dehors"]}, geometry=[
            box(1000, 6000, 3000, 8000), box(5100, 5100, 5300, 5300), box(50000, 0, 51000, 1000),
        ], crs=CRS_SOILGRIDS)
        pixels = pixels_lieux(lieux, TRANSFORMATION, (10, 20))
        # Le carré couvre les colonnes 1 et 2 des lignes 2 et 3.
        self.assertEqual(sorted(pixels["carre"].tolist()), [41, 42, 61, 62])
        self.assertEqual(pixels["minuscule"].tolist(), [4 * 20 + 5])
        self.assertEqual(len(pixels["dehors"]), 0)

    def test_moyenne_des_pixels_valides(self):
        couche = np.array([[1.0, 3.0], [np.nan, 5.0]], dtype=np.float32)
        moyennes, parts = moyennes_lieux({"a": np.array([0, 1, 2]), "b": np.array([2]), "c": np.array([], int)},
                                         couche)
        self.assertAlmostEqual(moyennes["a"], 2.0)
        self.assertAlmostEqual(parts["a"], 2 / 3)
        self.assertTrue(np.isnan(moyennes["b"]))
        self.assertEqual(parts["b"], 0.0)
        self.assertTrue(np.isnan(moyennes["c"]) and np.isnan(parts["c"]))

    def test_lieu_hors_de_la_fenetre(self):
        dedans = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10)], crs="EPSG:4326")
        verifier_fenetre(dedans)
        with self.assertRaises(ValueError):
            verifier_fenetre(gpd.GeoDataFrame(geometry=[box(-80, 0, -70, 10)], crs="EPSG:4326"))


if __name__ == "__main__":
    unittest.main()
