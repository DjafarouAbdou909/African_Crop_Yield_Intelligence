import math
import unittest

import pandas as pd

from src.evaluation.metriques import metriques, metriques_par, moyenne_macro, score_competence


class TestMetriques(unittest.TestCase):
    def test_prediction_parfaite(self):
        resultat = metriques([1.0, 2.0, 4.0], [1.0, 2.0, 4.0])

        self.assertEqual(resultat["n"], 3)
        self.assertEqual(resultat["mae_log"], 0.0)
        self.assertEqual(resultat["r2"], 1.0)

    def test_erreur_relative_symetrique(self):
        resultat = metriques([1.0, 1.0], [2.0, 0.5])

        self.assertAlmostEqual(resultat["mae_log"], math.log(2))
        self.assertAlmostEqual(resultat["erreur_relative_typique"], 1.0)
        self.assertAlmostEqual(resultat["biais_log"], 0.0)
        self.assertAlmostEqual(resultat["biais"], 0.25)

    def test_ventilation_et_moyenne_macro(self):
        df = pd.DataFrame({
            "pays": ["A", "A", "A", "B"],
            "reel": [1.0, 1.0, 1.0, 1.0],
            "predit": [1.0, 1.0, 1.0, math.e],
        })
        table = metriques_par(df, "pays", "reel", "predit")

        self.assertEqual(table.loc["A", "n"], 3)
        self.assertAlmostEqual(table.loc["B", "mae_log"], 1.0)
        self.assertAlmostEqual(moyenne_macro(table), 0.5)

    def test_score_competence(self):
        self.assertAlmostEqual(score_competence(0.3, 0.4), 0.25)
        self.assertLess(score_competence(0.5, 0.4), 0)


if __name__ == "__main__":
    unittest.main()
