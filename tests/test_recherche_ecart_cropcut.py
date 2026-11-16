import unittest

import numpy as np
import pandas as pd

from src.recherche.ecart_cropcut import (
    ajuster, appliquer, cellules_appariees, choisir, erreurs_croisees, intervalle_difference, intervalle_moyenne,
)


class TestEcartCropcut(unittest.TestCase):
    def test_cellules_appariees(self):
        survey = pd.DataFrame({
            "id_grappe": ["g", "g", "h"], "Crop": ["Maize"] * 3, "annee_recolte": [2014] * 3,
            "YieldUsingGPS_ton_ha_": [2.0, 8.0, 1.0], "GPSArea_ha_": [0.1, 0.4, 1.0],
        })
        cropcut = pd.DataFrame({
            "id_grappe": ["g", "k"], "Crop": ["Maize", "Maize"], "annee_recolte": [2014, 2014],
            "Yield_ton_ha_": [2.0, 3.0], "groupe": ["G", "K"],
        })
        cellules = cellules_appariees(survey, cropcut)
        # Seule la cellule g figure dans les deux jeux. La moyenne géométrique déclarée vaut 4, la mesure 2.
        self.assertEqual(len(cellules), 1)
        self.assertAlmostEqual(cellules.loc[0, "ecart"], np.log(4.0) - np.log(2.0))
        self.assertAlmostEqual(cellules.loc[0, "log_surface"], np.log(0.2))
        self.assertEqual(cellules.loc[0, "groupe"], "G")

    def test_intervalles_bootstrap(self):
        valeurs = np.array([1.0, 1.0, 3.0, 3.0])
        groupes = ["a", "a", "b", "b"]
        bas, haut = intervalle_moyenne(valeurs, groupes, tirages=200)
        self.assertTrue(1.0 <= bas <= haut <= 3.0)
        masque_a = np.array([True, False, True, False])
        bas, haut = intervalle_difference(np.array([2.0, 1.0, 2.0, 1.0]), masque_a, ~masque_a, groupes, tirages=200)
        self.assertAlmostEqual(bas, 1.0)
        self.assertAlmostEqual(haut, 1.0)

    def test_corrections(self):
        log_prediction = np.log(np.array([2.0, 2.0, 4.0, 4.0]))
        log_reel = log_prediction - 0.3
        cultures = np.array(["A", "A", "B", "B"])
        self.assertTrue(np.allclose(appliquer("C0", ajuster("C0", log_prediction, log_reel, cultures),
                                              log_prediction, cultures), log_prediction))
        for methode in ["C1", "C3"]:
            parametres = ajuster(methode, log_prediction, log_reel, cultures)
            self.assertTrue(np.allclose(appliquer(methode, parametres, log_prediction, cultures), log_reel))

    def test_decalage_par_culture_et_repli(self):
        log_prediction = np.zeros(5)
        log_reel = np.array([-1.0, -1.0, -1.0, 0.5, 0.5])
        cultures = np.array(["A", "A", "A", "B", "B"])
        import src.recherche.ecart_cropcut as module
        minimum = module.MINIMUM_CULTURE
        module.MINIMUM_CULTURE = 3
        try:
            parametres = ajuster("C2", log_prediction, log_reel, cultures)
        finally:
            module.MINIMUM_CULTURE = minimum
        corrige = appliquer("C2", parametres, np.zeros(3), np.array(["A", "B", "C"]))
        # A a assez de mesures et garde son décalage. B et C prennent la médiane globale, -1.
        self.assertTrue(np.allclose(corrige, [-1.0, -1.0, -1.0]))

    def test_erreurs_croisees_et_regle_de_choix(self):
        generateur = np.random.default_rng(0)
        prediction = np.exp(generateur.normal(0, 1, 500))
        calibration = pd.DataFrame({
            "Yield_ton_ha_": prediction * np.exp(-0.4 + generateur.normal(0, 0.1, 500)), "prediction": prediction,
            "Crop": "A", "pli": np.arange(500) % 5,
        })
        erreurs = erreurs_croisees(calibration, "prediction")
        self.assertLess(erreurs["C1"], erreurs["C0"])
        self.assertEqual(choisir(erreurs), "C1")
        # Une méthode plus complexe à moins de 0,005 de la meilleure ne l'emporte pas sur la plus simple.
        self.assertEqual(choisir(pd.Series({"C0": 0.5, "C1": 0.404, "C2": 0.4, "C3": 0.401})), "C1")
        self.assertEqual(choisir(pd.Series({"C0": 0.5, "C1": 0.41, "C2": 0.4, "C3": 0.401})), "C2")


if __name__ == "__main__":
    unittest.main()
