import unittest

import pandas as pd

from src.features.variables import annee_recolte_survey
from src.features.variables_cropcut import cropcut_comme_survey, date_calendrier_ethiopien


class TestVariablesCropcut(unittest.TestCase):
    def test_nouvel_an_et_meskel(self):
        # L'année éthiopienne commencée en 2011 suit une année bissextile éthiopienne,
        # puisque 2012 est bissextile, et commence donc le 12 septembre.
        # L'année commencée en 2018 est bissextile et son treizième mois compte 6 jours,
        # le dernier précédant le nouvel an du 12 septembre 2019.
        dates = date_calendrier_ethiopien([2011, 2018, 2018, 2018], [1, 1, 1, 13], [1, 1, 17, 6])
        self.assertEqual([d.date().isoformat() for d in dates], ["2011-09-12", "2018-09-11", "2018-09-27", "2019-09-11"])

    def test_mois_de_coupe_courants(self):
        # Le 30 du deuxième mois existe dans le calendrier éthiopien et tombe en novembre.
        self.assertEqual(date_calendrier_ethiopien([2011], [2], [30])[0].date().isoformat(), "2011-11-10")
        self.assertTrue(pd.isna(date_calendrier_ethiopien([None], [2], [1])[0]))

    def test_vague_de_cropcut_alignee_sur_survey(self):
        cropcut = pd.DataFrame({"Year": [2012, 2019], "id_mesure": ["ETH2011_0", "ETH2018_5"]})
        resultat = cropcut_comme_survey(cropcut)
        self.assertEqual(resultat["AgYearStart"].tolist(), [2011, 2018])
        self.assertEqual(resultat["id_ligne"].tolist(), ["ETH2011_0", "ETH2018_5"])
        # Le calendrier éthiopien de mai à janvier place la récolte en Year, comme dans survey.
        self.assertEqual(annee_recolte_survey(resultat["AgYearStart"], [5, 5], [1, 1], ["Ethiopia"] * 2).tolist(),
                         [2012, 2019])


if __name__ == "__main__":
    unittest.main()
