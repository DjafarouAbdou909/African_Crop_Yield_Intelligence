import unittest

import numpy as np
import pandas as pd

from src.recherche.couverture import _mondrian, decider, metriques_couverture, moitie, quantile_conforme


class TestCouvertureConforme(unittest.TestCase):
    def test_quantile_conforme(self):
        self.assertEqual(quantile_conforme(np.arange(1, 10), 0.8), 8)
        self.assertTrue(np.isnan(quantile_conforme([], 0.8)))

    def test_hierarchie_du_plus_fin_au_repli(self):
        calibration = pd.DataFrame({
            "country": ["A"] * 4 + ["B"] * 2,
            "crop": ["Maize", "Maize", "Teff", "Teff", "Maize", "Maize"],
            "erreur": [1.0, 1.0, 5.0, 5.0, 9.0, 9.0],
        })
        evaluation = pd.DataFrame({"country": ["A", "A", "B", "C"], "crop": ["Maize", "Rice", "Maize", "Maize"]})
        demi = _mondrian(calibration, evaluation, [["country"], ["country", "crop"]], 0.5, minimum=2)
        # Le couple A et Maize compte deux erreurs, A et Rice se replie sur A, C se replie sur l'ensemble.
        self.assertEqual(demi.tolist(), [1.0, 5.0, 9.0, quantile_conforme(calibration["erreur"], 0.5)])
        demi_pays = _mondrian(calibration, evaluation, [["country"]], 0.5, minimum=3)
        self.assertEqual(demi_pays.iloc[2], quantile_conforme(calibration["erreur"], 0.5))

    def test_metriques_et_pire_pays(self):
        evaluation = pd.DataFrame({"country": ["A", "A", "B", "B"], "erreur": [0.1, 0.1, 0.1, 2.0]})
        resultat = metriques_couverture("regional", evaluation, pd.Series([1.0] * 4), 0.8, minimum=2)
        self.assertEqual(resultat["couverture"], 0.75)
        self.assertEqual(resultat["pire_pays"], 0.5)
        self.assertEqual(resultat["pire_pays_nom"], "B")
        self.assertAlmostEqual(resultat["ecart_moyen_pays"], (0.2 + 0.3) / 2)
        self.assertAlmostEqual(resultat["largeur_mediane"], np.exp(2.0))

    def test_regle_de_decision(self):
        resultats = pd.DataFrame({
            "niveau": [0.8] * 6, "methode": ["M0", "M0", "M2", "M2", "M3", "M3"],
            "couverture": [0.80, 0.79, 0.81, 0.80, 0.75, 0.80],
            "ecart_moyen_pays": [0.08, 0.08, 0.03, 0.03, 0.01, 0.01],
            "largeur_mediane": [3.0, 3.0, 3.5, 3.5, 3.2, 3.2],
        })
        # M3 est exclue par sa couverture marginale de 75 %, M2 a le plus faible écart parmi les admissibles.
        self.assertEqual(decider(resultats), ("M2", True))

    def test_moities_stables(self):
        groupes = [f"g{i}" for i in range(200)]
        self.assertTrue((moitie(groupes) == moitie(groupes)).all())
        self.assertTrue(0.35 < moitie(groupes).mean() < 0.65)


if __name__ == "__main__":
    unittest.main()
