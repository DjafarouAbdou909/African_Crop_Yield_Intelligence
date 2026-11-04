import unittest

import numpy as np

from src.features.indicateurs import (
    evapotranspiration_reference,
    indicateurs_saison,
    pression_saturante,
    rayonnement_extraterrestre,
    sequence_seche_maximale,
)


class TestFAO56(unittest.TestCase):
    def test_rayonnement_extraterrestre_exemple_8(self):
        self.assertAlmostEqual(rayonnement_extraterrestre(-20.0, 246), 32.2, delta=0.1)

    def test_evapotranspiration_exemple_18(self):
        tdew = 237.3 * np.log(1.409 / 0.6108) / (17.27 - np.log(1.409 / 0.6108))
        self.assertAlmostEqual(pression_saturante(tdew), 1.409, places=4)
        et0 = evapotranspiration_reference(21.5, 12.3, tdew, 22.07, 2.078, 50.8, 100, 187)
        self.assertAlmostEqual(et0, 3.9, delta=0.05)


class TestIndicateurs(unittest.TestCase):
    def test_sequence_seche_bornee_par_la_fenetre(self):
        pluie = np.array([0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 2.0])
        resultat = sequence_seche_maximale(pluie, np.array([0, 0, 3, 4]), np.array([6, 1, 4, 6]))

        self.assertEqual(resultat.tolist(), [3, 2, 2, 2])

    def test_indicateurs_et_jour_manquant(self):
        n = 6
        series = {
            "pluie": np.array([0.0, 3.0, 0.5, 10.0, np.nan, 0.0]),
            "tmax": np.array([32.0, 36.0, 28.0, 30.0, 30.0, 30.0]),
            "tmin": np.array([18.0, 24.0, 12.0, 20.0, 20.0, 20.0]),
            "tdew": np.full(n, 10.0),
            "rayonnement": np.full(n, 20.0),
            "et0": np.full(n, 4.0),
        }
        resultat = indicateurs_saison(series, [0, 0], [3, 5])

        self.assertEqual(resultat["pluie_cumul"][0], 13.5)
        self.assertEqual(resultat["pluie_jours"][0], 2)
        self.assertEqual(resultat["sequence_seche_max"][0], 1)
        self.assertEqual(resultat["degres_jours"][0], 15.0 + 20.0 + 10.0 + 15.0)
        self.assertEqual(resultat["degres_jours_30"][0], 2.0 + 6.0)
        self.assertEqual(resultat["degres_jours_35"][0], 1.0)
        self.assertEqual(resultat["bilan_hydrique"][0], 13.5 - 16.0)
        self.assertTrue(np.isnan(resultat["pluie_cumul"][1]))
        self.assertTrue(np.isnan(resultat["sequence_seche_max"][1]))
        self.assertEqual(resultat["tmax_moyenne"][1], 31.0)


if __name__ == "__main__":
    unittest.main()
