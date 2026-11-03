import gzip
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from src.features.climat import centre_maille, grille_mailles, lire_power, nom_maille, poids_mailles


class TestMailles(unittest.TestCase):
    def test_centre_et_nom_de_maille(self):
        lat, lon = centre_maille(6.9, 2.35)
        self.assertEqual((float(lat), float(lon)), (7.0, 2.5))
        lat, lon = centre_maille(-0.1, -0.2)
        self.assertEqual(nom_maille(lat, lon), "+000.0_+000.000")

    def test_grille_limitee_aux_mailles_recoupees(self):
        geometries = gpd.GeoSeries([box(0.1, 0.1, 0.2, 0.2), box(1.3, 0.1, 1.4, 0.2)], crs="EPSG:4326")
        mailles = grille_mailles(geometries)

        self.assertEqual(mailles["maille"].tolist(), ["+000.0_+000.000", "+000.0_+001.250"])

    def test_poids_proportionnels_a_la_surface(self):
        zones = gpd.GeoDataFrame({"zone": ["Z"], "geometry": [box(0.0, -0.2, 0.625, 0.2)]}, crs="EPSG:4326")
        mailles = grille_mailles(zones.geometry)
        poids = poids_mailles(zones, mailles).set_index("maille")["poids"]

        self.assertAlmostEqual(poids.sum(), 1.0)
        self.assertAlmostEqual(poids["+000.0_+000.000"], 0.5, places=3)
        self.assertAlmostEqual(poids["+000.0_+000.625"], 0.5, places=3)


class TestLecturePower(unittest.TestCase):
    def test_valeurs_manquantes_et_dates(self):
        texte = "-BEGIN HEADER-\nentete\n-END HEADER-\nYEAR,DOY,T2M_MAX,ALLSKY_SFC_SW_DWN\n1981,1,30.5,-999.0\n1984,60,31.0,17.2\n"
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "maille.csv.gz"
            with gzip.open(chemin, "wt", encoding="utf-8") as fichier:
                fichier.write(texte)
            serie = lire_power(chemin)

        self.assertEqual([str(d.date()) for d in serie.index], ["1981-01-01", "1984-02-29"])
        self.assertTrue(np.isnan(serie.iloc[0]["ALLSKY_SFC_SW_DWN"]))
        self.assertEqual(serie.iloc[1]["T2M_MAX"], 31.0)


if __name__ == "__main__":
    unittest.main()
