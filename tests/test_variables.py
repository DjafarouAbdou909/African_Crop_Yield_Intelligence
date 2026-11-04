import unittest

import numpy as np
import pandas as pd

from src.features.variables import annee_recolte_survey


class TestVariables(unittest.TestCase):
    def test_annee_recolte_survey(self):
        resultat = annee_recolte_survey([2015, 2015, 2015], [11, 6, np.nan], [5, 11, np.nan])

        self.assertEqual(resultat[0], 2016)
        self.assertEqual(resultat[1], 2015)
        self.assertTrue(pd.isna(resultat[2]))

    def test_recolte_l_annee_de_debut_en_tanzanie(self):
        resultat = annee_recolte_survey([2015, 2015], [9, 9], [7, 7], ["Tanzania", "Malawi"])

        self.assertEqual(list(resultat), [2015, 2016])


if __name__ == "__main__":
    unittest.main()
