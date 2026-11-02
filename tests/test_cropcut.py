import unittest

import numpy as np
import pandas as pd

from src.data.cropcut import (
    jeu_validation_cropcut,
    reconstruire_menage,
    signaler_dates_invalides,
    signaler_mesures_incoherentes,
)


class TestPreparationCropcut(unittest.TestCase):
    def test_menage_reconstruit_par_division_entiere(self):
        df = pd.DataFrame({"holder_id": [101010160100201.0, 1301010010204000.0, np.nan]})
        resultat = reconstruire_menage(df)

        self.assertEqual(resultat["id_menage"].iloc[0], "ETH_1010101601002")
        self.assertEqual(resultat["id_menage"].iloc[1], "ETH_13010100102040")
        self.assertTrue(pd.isna(resultat["id_menage"].iloc[2]))

    def test_poids_incoherents(self):
        df = pd.DataFrame({"freshWeightKg": [0.9, 0.5, 0.0, np.nan], "dryWeightKg": [0.81, 2.2, 0.3, 0.4]})
        self.assertEqual(signaler_mesures_incoherentes(df)["flag_poids_incoherent"].tolist(), [False, True, True, False])

    def test_dates_calendrier_ethiopien(self):
        df = pd.DataFrame({"cropCutMonth": [2.0, 13.0, 13.0, 0.0, 83.0, np.nan], "cropCutDay": [30.0, 5.0, 7.0, 1.0, 13.0, 4.0]})
        self.assertEqual(
            signaler_dates_invalides(df)["flag_date_mesure_invalide"].tolist(),
            [False, False, True, True, True, False],
        )

    def test_jeu_validation(self):
        df = pd.DataFrame({"Yield_ton_ha_": [1.0, 1.0, 1.0]})
        df["flag_poids_incoherent"] = [False, True, False]
        df["flag_rendement_hors_bornes"] = [False, False, True]
        self.assertEqual(jeu_validation_cropcut(df).index.tolist(), [0])


if __name__ == "__main__":
    unittest.main()
