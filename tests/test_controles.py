import unittest

import numpy as np
import pandas as pd

from src.features.controles import alignement_regional, ecart_mois, incoherences_annee_semis


class TestControles(unittest.TestCase):
    def test_ecart_mois_circulaire(self):
        self.assertEqual(ecart_mois([1, 12, 6], [12, 1, 6]).tolist(), [1, 1, 0])

    def test_annee_de_semis_incoherente(self):
        regional = pd.DataFrame({
            "country": ["A", "A", "B"],
            "planting_month": [11.0, 6.0, 6.0],
            "harvest_month": [5.0, 11.0, 11.0],
            "planting_year": [2016.0, 2016.0, 2015.0],
            "harvest_year": [2016, 2016, 2016],
        })
        resultat = incoherences_annee_semis(regional)

        self.assertEqual(resultat.loc["A", "semis_publie_trop_tard"], 1)
        self.assertEqual(resultat.loc["B", "semis_publie_trop_tot"], 1)

    def test_alignement_retrouve_le_bon_decalage(self):
        rng = np.random.default_rng(0)
        annees = np.arange(2001, 2021)
        climat = rng.normal(size=len(annees) + 2)
        regional = pd.DataFrame({
            "country": "A", "GDAM_ID": "Z", "crop": "Maize", "saison": "Main",
            "harvest_year": annees, "yieldTonHa": np.exp(climat[1:-1]),
        })
        valeurs = {d: climat[1 + d:len(annees) + 1 + d] for d in [-1, 0, 1]}
        table = alignement_regional(regional, valeurs)

        self.assertAlmostEqual(table.loc["A", 0], 1.0)
        self.assertLess(table.loc["A", 1], 0.9)
        self.assertEqual(table.loc["A", "paires"], len(annees) - 1)


if __name__ == "__main__":
    unittest.main()
