import unittest

import numpy as np
import pandas as pd

from src.models.donnees import VARIABLES_CLIMAT
from src.recherche.horizons_prevision import developpement_horizon, fenetres_tronquees, fin_observee


class TestHorizonsPrevision(unittest.TestCase):
    def test_fin_observee_a_mi_saison_et_un_mois_avant(self):
        debut = pd.to_datetime(["2010-06-01", "2010-11-01"])
        fin = pd.to_datetime(["2010-09-30", "2011-02-28"])

        mi_saison = fin_observee(debut, fin, "mi_saison")
        self.assertEqual(list(mi_saison.strftime("%Y-%m-%d")), ["2010-07-31", "2010-12-30"])
        un_mois = fin_observee(debut, fin, "un_mois_avant")
        self.assertEqual(list(un_mois.strftime("%Y-%m-%d")), ["2010-08-31", "2011-01-31"])

    def test_saison_d_un_mois_sans_jour_observe_un_mois_avant(self):
        climat = pd.DataFrame({
            "GDAM_ID": ["A", "B"], "crop": ["Maize", "Maize"], "saison": ["Main", "Main"],
            "harvest_year": [2010, 2010], "lieu": ["A", "B"],
            "debut": ["2010-06-01", "2010-09-01"], "fin": ["2010-09-30", "2010-09-30"],
        })
        fenetres = fenetres_tronquees(climat, "un_mois_avant")
        self.assertEqual(fenetres.loc[0, "fin"], pd.Timestamp("2010-08-31"))
        self.assertTrue(fenetres.loc[1, ["debut", "fin"]].isna().all())

    def test_remplacement_des_variables_sans_changer_l_index(self):
        cle = {"GDAM_ID": ["A", "B"], "crop": ["Maize", "Rice"], "saison": ["Main", "Main"], "harvest_year": [2010, 2011]}
        developpement = pd.DataFrame({**cle, **{v: [1.0, 2.0] for v in VARIABLES_CLIMAT}, "autre": [5, 6]},
                                     index=[10, 20])
        variables = pd.DataFrame({**{k: v[::-1] for k, v in cle.items()},
                                  **{v: [30.0, np.nan] for v in VARIABLES_CLIMAT}})

        resultat = developpement_horizon(developpement, variables)
        self.assertEqual(resultat.index.tolist(), [10, 20])
        self.assertTrue(np.isnan(resultat.loc[10, "pluie_cumul"]))
        self.assertEqual(resultat.loc[20, "pluie_cumul"], 30.0)
        self.assertEqual(resultat["autre"].tolist(), [5, 6])
        self.assertEqual(developpement.loc[10, "pluie_cumul"], 1.0)


if __name__ == "__main__":
    unittest.main()
