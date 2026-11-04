import unittest

import numpy as np
import pandas as pd

from src.features.calendrier import (
    attribuer_calendrier,
    calendriers_harveststat,
    fenetre_saison,
    lire_ggcmi,
    mois_du_jour,
)
from src.features.calendrier import DOSSIER_GGCMI, FICHIER_GGCMI


class TestFenetreSaison(unittest.TestCase):
    def test_saison_dans_l_annee_a_cheval_et_sur_douze_mois(self):
        debut, fin = fenetre_saison([2016, 2016, 2016, None], [6, 11, 3, 6], [11, 5, 3, 11])

        self.assertEqual(pd.Timestamp(debut[0]), pd.Timestamp("2016-06-01"))
        self.assertEqual(pd.Timestamp(fin[0]), pd.Timestamp("2016-11-30"))
        self.assertEqual(pd.Timestamp(debut[1]), pd.Timestamp("2015-11-01"))
        self.assertEqual(pd.Timestamp(fin[1]), pd.Timestamp("2016-05-31"))
        self.assertEqual(pd.Timestamp(debut[2]), pd.Timestamp("2015-04-01"))
        self.assertEqual(pd.Timestamp(fin[2]), pd.Timestamp("2016-03-31"))
        self.assertTrue(pd.isna(debut[3]) and pd.isna(fin[3]))

    def test_mois_du_jour(self):
        self.assertEqual(mois_du_jour([1, 31, 32, 365]).tolist(), [1, 1, 2, 12])
        self.assertTrue(np.isnan(mois_du_jour([np.nan])[0]))


class TestCalendrier(unittest.TestCase):
    def setUp(self):
        self.regional = pd.DataFrame({
            "GDAM_ID": ["Z1", "Z1", "Z1", "Z2"],
            "L1_GID": ["R1", "R1", "R1", "R1"],
            "L0_GID": ["P", "P", "P", "P"],
            "crop": ["Maize", "Maize", "Maize", "Maize"],
            "saison": ["Main", "Main", "Second", "Main"],
            "planting_month": [6.0, 6.0, 1.0, 7.0],
            "harvest_month": [10.0, 10.0, 4.0, 11.0],
            "areaHa": [100.0, 50.0, 500.0, 10.0],
        })

    def test_saison_principale_par_surface(self):
        tables = calendriers_harveststat(self.regional)

        self.assertEqual(tables["zone"].loc[("Z1", "Maize")].tolist(), [1.0, 4.0])
        self.assertEqual(tables["zone"].loc[("Z2", "Maize")].tolist(), [7.0, 11.0])
        self.assertEqual(tables["niveau_1"].loc[("R1", "Maize")].tolist(), [1.0, 4.0])

    def test_priorite_des_niveaux(self):
        tables = calendriers_harveststat(self.regional)
        df = pd.DataFrame({
            "zone": ["Z2", "Z9", "Z9", "Z9"],
            "region": ["R1", "R1", "R9", "R9"],
            "pays": ["P", "P", "P", "Q"],
            "crop": ["Maize", "Maize", "Maize", "Cocoa"],
            "planting_month": [3.0, np.nan, np.nan, np.nan],
            "harvest_month": [8.0, np.nan, np.nan, np.nan],
        })
        resultat = attribuer_calendrier(df, tables, {"zone": "zone", "niveau_1": "region", "pays": "pays"},
                                        "crop", [np.nan] * 4, [np.nan] * 4)

        self.assertEqual(resultat["source_calendrier"].tolist()[:3], ["ligne", "niveau_1", "pays"])
        self.assertTrue(pd.isna(resultat["source_calendrier"].iloc[3]))
        self.assertEqual(resultat["mois_semis"].tolist()[:3], [3.0, 1.0, 1.0])

    def test_calendrier_dominant_toutes_cultures(self):
        tables = calendriers_harveststat(self.regional)
        df = pd.DataFrame({"zone": ["Z9", "Z9"], "region": ["R1", "R9"], "pays": ["P", "Q"], "crop": ["Cocoa", "Cocoa"]})
        resultat = attribuer_calendrier(df, tables, {"zone": "zone", "niveau_1": "region", "pays": "pays"},
                                        "crop", [np.nan] * 2, [np.nan] * 2)

        self.assertEqual(resultat["source_calendrier"].iloc[0], "niveau_1_dominant")
        self.assertEqual(resultat[["mois_semis", "mois_recolte"]].iloc[0].tolist(), [1.0, 4.0])
        self.assertTrue(pd.isna(resultat["source_calendrier"].iloc[1]))


@unittest.skipUnless((DOSSIER_GGCMI / FICHIER_GGCMI.format(code="mai")).exists(), "calendrier GGCMI absent")
class TestGGCMI(unittest.TestCase):
    def test_mais_au_malawi_et_au_niger(self):
        semis, recolte = lire_ggcmi("Maize", [-14.0, 13.5, 0.0], [33.8, 2.1, 0.0])

        self.assertEqual(semis[:2].tolist(), [11.0, 6.0])
        self.assertEqual(recolte[:2].tolist(), [5.0, 10.0])
        self.assertTrue(np.isnan(semis[2]))


if __name__ == "__main__":
    unittest.main()
