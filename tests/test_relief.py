import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from rasterio.windows import Window
from shapely.geometry import box

from src.features.relief import RAYON_TERRE, agreger_grille, nom_tuile, pente_horn, traiter_tuile, tuiles_a_couvrir


class TestRelief(unittest.TestCase):
    def test_nom_des_tuiles(self):
        self.assertEqual(nom_tuile(9, 38), "Copernicus_DSM_COG_30_N09_00_E038_00_DEM")
        self.assertEqual(nom_tuile(-14, -5), "Copernicus_DSM_COG_30_S14_00_W005_00_DEM")

    def test_tuiles_recoupant_un_lieu(self):
        lieux = gpd.GeoDataFrame(geometry=[box(2.2, 9.5, 3.4, 9.8)], crs="EPSG:4326")
        existantes = {nom_tuile(9, 2), nom_tuile(9, 3)}
        self.assertEqual(tuiles_a_couvrir(lieux, existantes), [nom_tuile(9, 2), nom_tuile(9, 3)])
        self.assertEqual(tuiles_a_couvrir(lieux, {nom_tuile(9, 3)}), [nom_tuile(9, 3)])

    def test_pente_d_un_plan_incline(self):
        pas = 3 / 3600
        metres = RAYON_TERRE * np.radians(pas)
        # Plan montant de 1 m par mètre vers le sud, soit une pente de 45 degrés.
        altitude = np.arange(6)[:, None] * metres * np.ones((1, 5))
        pente = pente_horn(altitude, np.zeros(6), pas)
        np.testing.assert_allclose(pente[1:-1, 1:-1], 45.0)
        # À 60 degrés de latitude, le pas est-ouest est deux fois plus court.
        altitude = np.ones((5, 1)) * np.arange(6)[None, :] * metres * 0.5
        np.testing.assert_allclose(pente_horn(altitude, np.full(5, 60.0), pas)[1:-1, 1:-1], 45.0)
        self.assertTrue(np.all(pente_horn(np.full((4, 4), 300.0), np.zeros(4), pas) == 0))

    def test_agregation_ponderee_sur_la_grille(self):
        transformation = Affine(1000.0, 0.0, 0.0, 0.0, -1000.0, 0.0)
        fenetre = Window(0, 0, 3, 3)
        # Deux points dans le premier pixel, un dans le pixel central, un hors de la fenêtre.
        longitudes = np.array([0.001, 0.002, 0.0135, 1.0])
        latitudes = np.array([-0.001, -0.002, -0.0135, -1.0])
        pixels, sommes = agreger_grille(longitudes, latitudes, [np.array([10.0, 20.0, 5.0, 99.0])],
                                        np.array([1.0, 3.0, 2.0, 1.0]), transformation, fenetre)
        self.assertEqual(pixels.tolist(), [0, 4])
        np.testing.assert_allclose(sommes[0], [4.0, 2.0])
        np.testing.assert_allclose(sommes[1] / sommes[0], [17.5, 5.0])

    def test_tuile_masque_les_eaux(self):
        dossier = Path(tempfile.mkdtemp())
        transformation = Affine(3 / 3600, 0, 20.0, 0, -3 / 3600, 1.0)
        profil = {"driver": "GTiff", "height": 12, "width": 12, "count": 1, "crs": "EPSG:4326",
                  "transform": transformation}
        with rasterio.open(dossier / "dem.tif", "w", dtype="float32", **profil) as raster:
            raster.write(np.full((1, 12, 12), 500.0, dtype=np.float32))
        eau = np.zeros((1, 12, 12), dtype=np.uint8)
        eau[0, :, 6:] = 2
        with rasterio.open(dossier / "wbm.tif", "w", dtype="uint8", **profil) as raster:
            raster.write(eau)
        pixels, sommes, terre = traiter_tuile(dossier / "dem.tif", dossier / "wbm.tif")
        self.assertEqual(terre, 72)
        np.testing.assert_allclose(sommes[1] / sommes[0], 500.0)
        np.testing.assert_allclose(sommes[2], 0.0)


if __name__ == "__main__":
    unittest.main()
