import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.agregation import indicateurs_lieux, moyenne_ponderee, voisinages_grappes
from src.features.climat import DEBUT_IMERG, DEBUT_POWER, FIN_POWER


def ecrire_magasin(dossier, produit, mailles, debut, valeurs):
    dates = pd.date_range(debut, FIN_POWER, freq="D")
    pd.DataFrame({"maille": mailles, "latitude": 0.0, "longitude": 0.0, "altitude": 0.0}).to_csv(
        dossier / f"{produit}_mailles.csv", index=False)
    pd.Series(dates.strftime("%Y-%m-%d"), name="date").to_csv(dossier / f"{produit}_dates.csv", index=False)
    for variable, valeur in valeurs.items():
        tableau = np.lib.format.open_memmap(dossier / f"{produit}_{variable}.npy", mode="w+", dtype=np.float32,
                                            shape=(len(mailles), len(dates)))
        tableau[:] = np.asarray(valeur, dtype=np.float32)[:, None]
        tableau.flush()


class TestAgregation(unittest.TestCase):
    def test_moyenne_ponderee_ignore_les_valeurs_manquantes(self):
        tableau = np.array([[1.0, np.nan, np.nan], [3.0, 5.0, np.nan], [9.0, 9.0, 9.0]])
        resultat = moyenne_ponderee(tableau, np.array([1, 0]), np.array([0.25, 0.75]))

        self.assertEqual(resultat[0], 0.75 * 1.0 + 0.25 * 3.0)
        self.assertEqual(resultat[1], 5.0)
        self.assertTrue(np.isnan(resultat[2]))

    def test_voisinage_de_5_km(self):
        voisinage = voisinages_grappes([10.0], [2.0]).to_crs("EPSG:6933").iloc[0]
        self.assertAlmostEqual(voisinage.area / 1e6 / (np.pi * 25), 1.0, delta=0.01)

    def test_indicateurs_par_lieu_et_debordement(self):
        with tempfile.TemporaryDirectory() as dossier:
            dossier = Path(dossier)
            ecrire_magasin(dossier, "power", ["A", "B"], DEBUT_POWER, {
                "T2M_MAX": [30.0, 34.0], "T2M_MIN": [20.0, 20.0], "T2MDEW": [15.0, 15.0],
                "ALLSKY_SFC_SW_DWN": [20.0, 20.0], "WS2M": [2.0, 2.0], "ET0": [4.0, 6.0],
            })
            ecrire_magasin(dossier, "imerg", ["A", "B"], DEBUT_IMERG, {"IMERG_PRECTOT": [2.0, 0.0]})
            poids = pd.DataFrame({"lieu": ["Z", "Z"], "maille": ["A", "B"], "poids": [0.5, 0.5]})
            fenetres = pd.DataFrame({
                "lieu": ["Z", "Z", "Z"],
                "debut": pd.to_datetime(["2010-06-01", "1990-06-01", "2023-11-01"]),
                "fin": pd.to_datetime(["2010-06-10", "1990-06-10", "2024-01-31"]),
            })
            resultat = indicateurs_lieux(poids, fenetres, dossier)

        self.assertEqual(resultat.loc[0, "pluie_cumul"], 10.0)
        self.assertEqual(resultat.loc[0, "pluie_jours"], 10.0)
        self.assertEqual(resultat.loc[0, "et0_cumul"], 50.0)
        self.assertEqual(resultat.loc[0, "tmax_moyenne"], 32.0)
        self.assertEqual(resultat.loc[0, "degres_jours_30"], 20.0)
        self.assertTrue(np.isnan(resultat.loc[1, "pluie_cumul"]))
        self.assertEqual(resultat.loc[1, "tmax_moyenne"], 32.0)
        self.assertTrue(resultat.loc[2, ["pluie_cumul", "tmax_moyenne"]].isna().all())


if __name__ == "__main__":
    unittest.main()
