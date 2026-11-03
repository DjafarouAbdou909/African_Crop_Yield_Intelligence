import unittest

import numpy as np
import pandas as pd

from src.data.survey import (
    construire_identifiants,
    harmoniser_annee,
    harmoniser_pays,
    jeu_modelisation_survey,
    signaler_surface_gps_recopiee,
    signaler_valeurs_impossibles,
    supprimer_doublons_exacts,
)


def ligne(**valeurs):
    base = {
        "Country": "Ethiopia", "Source": "LSMS_ETH2015", "GPS_lat": 9.5, "GPS_lon": 38.1,
        "Crop": "Maize", "prcCrop": 100.0, "ReportedArea_ha_": 0.5, "GPSArea_ha_": 0.4,
        "YieldUsingGPS_ton_ha_": 1.2, "AgYearStart": 2015, "AgYearEnd": 2016.0, "hhid": "1001",
    }
    base.update(valeurs)
    return base


class TestPreparationSurvey(unittest.TestCase):
    def test_doublons_exacts_supprimes(self):
        df = pd.DataFrame([ligne(), ligne(), ligne(hhid="1002")])
        self.assertEqual(supprimer_doublons_exacts(df).index.tolist(), [0, 2])

    def test_libelle_cote_divoire(self):
        df = pd.DataFrame([ligne(Country="Cote dIvoire")])
        self.assertEqual(harmoniser_pays(df)["Country"].iloc[0], "Côte dIvoire")

    def test_annee_de_fin_deduite(self):
        df = pd.DataFrame([ligne(AgYearStart=2021, AgYearEnd=np.nan), ligne()])
        self.assertEqual(harmoniser_annee(df)["annee_recolte"].tolist(), [2022, 2016])

    def test_valeurs_impossibles_signalees(self):
        df = pd.DataFrame([ligne(prcCrop=150.0), ligne(ReportedArea_ha_=5.99e9), ligne()])
        resultat = signaler_valeurs_impossibles(df)

        self.assertEqual(resultat["flag_prccrop_invalide"].tolist(), [True, False, False])
        self.assertEqual(resultat["flag_surface_aberrante"].tolist(), [False, True, False])

    def test_surface_gps_recopiee(self):
        df = pd.DataFrame([
            ligne(GPSArea_ha_=0.5),
            ligne(),
            ligne(GPSArea_ha_=np.nan, ReportedArea_ha_=np.nan),
        ])
        resultat = signaler_surface_gps_recopiee(df)

        self.assertEqual(resultat["flag_surface_gps_recopiee"].tolist(), [True, False, False])

    def test_identifiants(self):
        df = pd.DataFrame([
            ligne(),
            ligne(hhid="1.010108880091e+16"),
            ligne(hhid=np.nan, GPS_lat=np.nan),
        ])
        resultat = construire_identifiants(df)

        self.assertEqual(resultat["id_ligne"].tolist(), ["LSMS_ETH2015_0", "LSMS_ETH2015_1", "LSMS_ETH2015_2"])
        self.assertEqual(resultat["id_menage"].iloc[0], "Ethiopia_1001")
        self.assertTrue(resultat["id_menage"].iloc[1:].isna().all())
        self.assertEqual(resultat["flag_hhid_tronque"].tolist(), [False, True, False])
        self.assertEqual(resultat["id_grappe"].iloc[0], resultat["id_grappe"].iloc[1])
        self.assertTrue(pd.isna(resultat["id_grappe"].iloc[2]))

    def test_jeu_modelisation(self):
        df = pd.DataFrame([ligne(), ligne(YieldUsingGPS_ton_ha_=np.nan), ligne(), ligne()])
        df["flag_rendement_hors_bornes"] = [False, False, True, False]
        df["flag_prccrop_invalide"] = [False, False, False, True]
        df["flag_surface_aberrante"] = False

        self.assertEqual(jeu_modelisation_survey(df).index.tolist(), [0])


if __name__ == "__main__":
    unittest.main()
