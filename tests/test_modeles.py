import unittest

import numpy as np
import pandas as pd

from src.models.apprentissage import PARAMETRES, erreur_par_palier, matrice, validation_croisee
from src.models.donnees import duree_saison
from src.models.experiences import decoupages


class TestModeles(unittest.TestCase):
    def test_duree_de_saison(self):
        self.assertEqual(duree_saison([5, 11, 3, np.nan], [9, 2, 3, 4]).tolist()[:3], [5, 4, 12])
        self.assertTrue(np.isnan(duree_saison([np.nan], [4])[0]))

    def test_modalites_fixees_et_inconnues(self):
        entrainement = pd.DataFrame({"crop": ["Maize", "Teff"], "x": [1, 2]})
        x, categories = matrice(entrainement, ["crop"], ["x"])
        autre, _ = matrice(pd.DataFrame({"crop": ["Teff", "Rice"], "x": [3, 4]}), ["crop"], ["x"], categories)
        self.assertEqual(autre["crop"].cat.codes.tolist(), [1, -1])
        self.assertEqual(list(x.columns), ["crop", "x"])

    def test_erreur_par_palier(self):
        predictions = pd.DataFrame({100: [1.0, np.e], 200: [np.e, np.e]})
        erreurs = erreur_par_palier([1.0, np.e], predictions)
        self.assertAlmostEqual(erreurs[100], 0.0)
        self.assertAlmostEqual(erreurs[200], 0.5)

    def test_validation_croisee_hors_pli(self):
        generateur = np.random.default_rng(0)
        n = 400
        table = pd.DataFrame({
            "partition": ["developpement"] * (n - 40) + ["test_temporel"] * 40,
            "pli": list(np.arange(n - 40) % 5) + [np.nan] * 40,
            "crop": generateur.choice(["Maize", "Teff"], n),
            "x": generateur.normal(size=n),
        })
        table["rendement"] = np.exp(0.5 * table["x"] + (table["crop"] == "Teff"))
        parametres = {**PARAMETRES, "min_data_in_leaf": 5, "num_threads": 1}
        predictions, _ = validation_croisee(table, "rendement", ["crop"], ["x"], parametres, iterations=50, pas=25)
        self.assertEqual(len(predictions), n - 40)
        self.assertFalse(predictions.isna().any().any())
        erreurs = erreur_par_palier(table.loc[predictions.index, "rendement"], predictions)
        self.assertLess(erreurs[50], np.mean(np.abs(np.log(table["rendement"]) - np.log(table["rendement"]).mean())))

    def test_decoupages_temporels_internes(self):
        developpement = pd.DataFrame({
            "Country": ["A", "A", "A", "B", "B"],
            "annee_recolte": [2010, 2012, 2012, 2018, 2018],
            "pli": [0, 1, 2, 0, 1],
        })
        (ancien, recent), = decoupages("survey", "temporelle", developpement)
        self.assertEqual(recent.tolist(), [False, True, True, False, False])
        self.assertEqual(ancien.tolist(), [True, False, False, True, True])
        spatio = decoupages("survey", "spatio_temporelle", developpement)
        self.assertEqual(len(spatio), 5)
        self.assertEqual(spatio[1][1].tolist(), [False, True, False, False, False])
        self.assertEqual(spatio[1][0].tolist(), [True, False, False, True, False])
        regional = pd.DataFrame({"harvest_year": [2011, 2012], "pli": [0, 0]})
        (ancien, recent), = decoupages("regional", "temporelle", regional)
        self.assertEqual(recent.tolist(), [False, True])


if __name__ == "__main__":
    unittest.main()
