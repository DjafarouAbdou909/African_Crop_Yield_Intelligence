import unittest

import numpy as np
import pandas as pd

from src.recherche.zones_climatiques import apport_par_strate, classe_aridite, indice_aridite_zones


class TestZonesClimatiques(unittest.TestCase):
    def test_seuils_du_pnue(self):
        classes = classe_aridite(pd.Series([0.01, 0.05, 0.19, 0.2, 0.5, 0.64, 0.65, 1.5]))
        self.assertEqual(classes.tolist(), ["hyperaride", "aride", "aride", "semi_aride", "subhumide_seche",
                                            "subhumide_seche", "humide", "humide"])

    def test_indice_pondere_et_mailles_manquantes(self):
        poids = pd.DataFrame({"lieu": ["Z", "Z", "Z"], "maille": ["a", "b", "c"], "poids": [0.5, 0.25, 0.25]})
        climat = pd.DataFrame({"pluie_annuelle": [400.0, 800.0, np.nan], "et0_annuelle": [2000.0, 2000.0, 2000.0]},
                              index=["a", "b", "c"])
        resultat = indice_aridite_zones(poids, climat).loc["Z"]
        # La maille c n'a pas de pluie, les poids des mailles a et b sont renormalisés.
        self.assertAlmostEqual(resultat["pluie_annuelle"], (0.5 * 400 + 0.25 * 800) / 0.75)
        self.assertAlmostEqual(resultat["indice_aridite"], resultat["pluie_annuelle"] / 2000)
        self.assertEqual(resultat["classe_aridite"], "semi_aride")

    def test_apport_par_strate_et_minimum(self):
        lignes = pd.DataFrame({
            "yieldTonHa": [1.0] * 6, "complet": [1.1] * 6, "sans_climat": [1.2] * 6, "reference": [1.3] * 6,
            "groupe": ["g1", "g2", "g3", "g1", "g2", "g3"], "country": ["A"] * 6,
            "strate": ["x", "x", "x", "x", "y", "y"],
        })
        resultat = apport_par_strate(lignes, "strate", minimum=3)
        self.assertEqual(list(resultat.index), ["x"])
        self.assertAlmostEqual(resultat.loc["x", "apport_climat"], np.log(1.2) - np.log(1.1))
        self.assertGreater(resultat.loc["x", "competence"], 0)


if __name__ == "__main__":
    unittest.main()
