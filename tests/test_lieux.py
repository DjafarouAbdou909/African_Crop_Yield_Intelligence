import unittest

import numpy as np
import pandas as pd

from src.features.lieux import geometries_mailles, lieu_survey


class TestLieux(unittest.TestCase):
    def test_lieu_grappe_puis_zone(self):
        survey = pd.DataFrame({
            "id_grappe": ["Mali_12.5_-8.0", None, None],
            "GPS_lat": [12.5, np.nan, np.nan],
            "GPS_lon": [-8.0, np.nan, np.nan],
            "L2_GID": ["L2MLI1", "L2MLI2", None],
            "L1_GID": ["L1MLI1", "L1MLI1", None],
        })
        lieu, nature = lieu_survey(survey)

        self.assertEqual(lieu.tolist()[:2], ["grappe:Mali_12.5_-8.0", "zone:L2MLI2"])
        self.assertTrue(pd.isna(lieu.iloc[2]))
        self.assertEqual(nature.tolist()[:2], ["grappe", "zone"])

    def test_contour_des_mailles(self):
        contour = geometries_mailles(pd.DataFrame({"maille": ["m"], "latitude": [0.5], "longitude": [0.625]}))
        self.assertEqual(contour.geometry.iloc[0].bounds, (0.3125, 0.25, 0.9375, 0.75))


if __name__ == "__main__":
    unittest.main()
