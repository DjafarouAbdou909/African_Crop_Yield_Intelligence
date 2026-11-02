import unittest

import numpy as np
import pandas as pd

from src.data.common import (
    bornes_filtre_auteurs,
    hors_bornes,
    identifiant_grappe,
    normaliser_textes,
    signaler_hierarchie_incoherente,
)


class TestNormaliserTextes(unittest.TestCase):
    def test_supprime_bom_et_jetons_manquants(self):
        df = pd.DataFrame({
            "gid": ["﻿L1LSO1721", "[]", " L1ETH0927 ", None],
            "systeme": ["none", "All (PS)", "irrigated", "none"],
            "valeur": [1.0, -999.0, 2.0, np.nan],
        })
        resultat = normaliser_textes(df)

        self.assertEqual(resultat["gid"].tolist()[0], "L1LSO1721")
        self.assertTrue(pd.isna(resultat["gid"].iloc[1]))
        self.assertEqual(resultat["gid"].iloc[2], "L1ETH0927")
        self.assertEqual(resultat["systeme"].isna().sum(), 2)
        pd.testing.assert_series_equal(resultat["valeur"], df["valeur"])

    def test_ne_modifie_pas_le_tableau_source(self):
        df = pd.DataFrame({"gid": ["[]"]})
        normaliser_textes(df)
        self.assertEqual(df["gid"].iloc[0], "[]")


class TestBornesFiltreAuteurs(unittest.TestCase):
    def test_bornes_par_culture(self):
        rendements = pd.Series([1.0, 2.0, 3.0, -99.0, 10.0, 10.0])
        cultures = pd.Series(["Maize", "Maize", "Maize", "Maize", "Cassava", "Cassava"])
        bornes = bornes_filtre_auteurs(rendements, cultures)

        self.assertAlmostEqual(bornes.loc["Maize", "borne_basse"], 0.2)
        self.assertAlmostEqual(bornes.loc["Maize", "borne_haute"], 2 * pd.Series([1.0, 2.0, 3.0]).quantile(0.98))
        self.assertAlmostEqual(bornes.loc["Cassava", "borne_basse"], 1.0)

    def test_hors_bornes(self):
        bornes = pd.DataFrame({"borne_basse": [0.2], "borne_haute": [6.0]}, index=["Maize"])
        rendements = pd.Series([0.1, 1.0, 7.0, np.nan, 50.0])
        cultures = pd.Series(["Maize", "Maize", "Maize", "Maize", "Teff"])

        self.assertEqual(hors_bornes(rendements, cultures, bornes).tolist(), [True, False, True, False, False])


class TestIdentifiantGrappe(unittest.TestCase):
    def test_grappe_manquante_si_coordonnee_absente(self):
        latitudes = pd.Series([9.5, 9.5, np.nan])
        longitudes = pd.Series([38.1, 38.1, 38.1])
        grappes = identifiant_grappe(latitudes, longitudes)

        self.assertEqual(grappes.iloc[0], grappes.iloc[1])
        self.assertTrue(pd.isna(grappes.iloc[2]))


class TestHierarchieGid(unittest.TestCase):
    def test_signale_un_enfant_a_plusieurs_parents(self):
        df = pd.DataFrame({
            "L0_GID": ["L0A", "L0A", "L0A", "L0B"],
            "L1_GID": ["L1A1", "L1A2", "L1A1", "L1B1"],
            "L2_GID": ["L2X", "L2X", "L2Y", np.nan],
            "L3_GID": [np.nan, np.nan, np.nan, np.nan],
        })
        resultat = signaler_hierarchie_incoherente(df)

        self.assertEqual(resultat["flag_hierarchie_gid_incoherente"].tolist(), [True, True, False, False])


if __name__ == "__main__":
    unittest.main()
