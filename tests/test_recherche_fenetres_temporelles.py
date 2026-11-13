import unittest

import pandas as pd

from src.recherche.fenetres_temporelles import decoupages, fenetre_de


class TestFenetresTemporelles(unittest.TestCase):
    def setUp(self):
        self.developpement = pd.DataFrame({"harvest_year": [2000, 2003, 2004, 2006, 2007, 2016, 2017]})
        self.fenetres = {"F1": (2004, 2006), "F2": (2007, 2016)}

    def test_entrainement_strictement_anterieur(self):
        decoupes = decoupages(self.developpement, self.fenetres)
        apprentissage, evaluation = decoupes["F1"]
        self.assertEqual(apprentissage.tolist(), [True, True, False, False, False, False, False])
        self.assertEqual(evaluation.tolist(), [False, False, True, True, False, False, False])
        apprentissage, evaluation = decoupes["F2"]
        self.assertEqual(apprentissage.tolist(), [True, True, True, True, False, False, False])
        self.assertEqual(evaluation.tolist(), [False, False, False, False, True, True, False])

    def test_fenetre_de_chaque_ligne(self):
        fenetres = fenetre_de(self.developpement, self.fenetres)
        self.assertEqual(fenetres.fillna("hors").tolist(), ["hors", "hors", "F1", "F1", "F2", "F2", "hors"])


if __name__ == "__main__":
    unittest.main()
