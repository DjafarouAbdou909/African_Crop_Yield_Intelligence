import math
import unittest

import numpy as np
import pandas as pd

from src.evaluation.references import reference_hierarchique

NIVEAUX = [["culture", "zone"], ["culture"]]


class TestReferenceHierarchique(unittest.TestCase):
    def setUp(self):
        self.entrainement = pd.DataFrame({
            "culture": ["Maize", "Maize", "Maize", "Sorghum"],
            "zone": ["Z1", "Z1", "Z2", "Z1"],
            "rendement": [1.0, 4.0, 8.0, 2.0],
        })

    def test_moyenne_geometrique_au_niveau_le_plus_fin(self):
        a_predire = pd.DataFrame({"culture": ["Maize"], "zone": ["Z1"]})
        prediction, niveau = reference_hierarchique(self.entrainement, a_predire, "rendement", NIVEAUX)

        self.assertAlmostEqual(prediction.iloc[0], 2.0)
        self.assertEqual(niveau.iloc[0], 0)

    def test_repli_sur_les_niveaux_plus_larges(self):
        a_predire = pd.DataFrame({"culture": ["Maize", "Maize", "Cassava"], "zone": ["Z9", np.nan, "Z1"]})
        prediction, niveau = reference_hierarchique(self.entrainement, a_predire, "rendement", NIVEAUX)

        self.assertAlmostEqual(prediction.iloc[0], 32 ** (1 / 3))
        self.assertEqual(niveau.tolist(), [1, 1, 2])
        self.assertAlmostEqual(prediction.iloc[2], math.exp(np.log([1.0, 4.0, 8.0, 2.0]).mean()))

    def test_saison_manquante_forme_une_modalite(self):
        entrainement = pd.DataFrame({"culture": ["Maize", "Maize"], "saison": [np.nan, "Belg"], "rendement": [1.0, 9.0]})
        a_predire = pd.DataFrame({"culture": ["Maize"], "saison": [np.nan]})
        prediction, niveau = reference_hierarchique(entrainement, a_predire, "rendement", [["culture", "saison"]])

        self.assertAlmostEqual(prediction.iloc[0], 1.0)
        self.assertEqual(niveau.iloc[0], 0)


if __name__ == "__main__":
    unittest.main()
