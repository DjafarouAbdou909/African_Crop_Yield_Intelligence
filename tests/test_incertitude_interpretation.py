import unittest

import numpy as np
import pandas as pd

from src.models.apprentissage import PARAMETRES, entrainer, matrice
from src.models.incertitude import couverture, demi_largeurs, intervalles, quantile_conforme
from src.models.interpretation import contributions, dependance, importance_shapley


class TestIncertitude(unittest.TestCase):
    def test_quantile_conforme(self):
        erreurs = np.arange(1, 10, dtype=float)
        # Avec neuf erreurs, la couverture de 80 % exige le rang de plafond de 10 fois 0,8, soit la huitième.
        self.assertEqual(quantile_conforme(erreurs, 0.8), 8.0)
        self.assertEqual(quantile_conforme(erreurs, 0.99), 9.0)

    def test_intervalles_par_culture_et_repli(self):
        erreurs = pd.DataFrame({"culture": ["A"] * 3 + ["B"], "erreur": [0.1, 0.2, 0.3, 2.0]})
        largeurs = demi_largeurs(erreurs, niveaux=[0.5], minimum=3)
        self.assertEqual(list(largeurs.index), ["ensemble", "A"])
        bas, haut = intervalles([1.0, 1.0], ["A", "B"], largeurs, 0.5)
        self.assertAlmostEqual(haut[0], np.exp(0.2))
        self.assertAlmostEqual(haut[1], np.exp(largeurs.loc["ensemble", 0.5]))
        self.assertAlmostEqual(bas[0] * haut[0], 1.0)

    def test_couverture(self):
        largeurs = pd.DataFrame({0.8: [np.log(2)]}, index=["ensemble"])
        evaluation = pd.DataFrame({"prediction": [1.0, 1.0], "reel": [1.5, 3.0], "partition": ["t", "t"]})
        resultat = couverture(evaluation, ["X", "X"], largeurs, niveaux=[0.8])
        self.assertEqual(resultat.loc["t", "couverture_80%"], 0.5)
        self.assertAlmostEqual(resultat.loc["t", "rapport_haut_bas_median_80%"], 4.0)


class TestInterpretation(unittest.TestCase):
    def test_contributions_somment_a_la_prediction(self):
        generateur = np.random.default_rng(1)
        table = pd.DataFrame({"crop": generateur.choice(["Maize", "Teff"], 300), "x": generateur.normal(size=300)})
        table["rendement"] = np.exp(table["x"] + (table["crop"] == "Teff"))
        x, categories = matrice(table, ["crop"], ["x"])
        modele = entrainer(x, table["rendement"], {**PARAMETRES, "min_data_in_leaf": 5, "num_threads": 1}, 30)
        description = {"categorielles": ["crop"], "numeriques": ["x"], "categories": categories}
        contribs, base = contributions(modele, description, table)
        np.testing.assert_allclose(contribs.sum(axis=1) + base, modele.predict(x), atol=1e-9)
        variables, familles = importance_shapley(contribs)
        self.assertEqual(set(variables.index), {"crop", "x"})
        self.assertIn("culture", familles.index)
        courbe = dependance(contribs, table, "x", 4)
        self.assertTrue(courbe["contribution_mediane"].is_monotonic_increasing)


if __name__ == "__main__":
    unittest.main()
