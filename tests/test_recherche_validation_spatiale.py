import unittest

import numpy as np
import pandas as pd

from src.recherche.validation_spatiale import (
    RAYON_TAMPON_KM,
    blocs_geographiques,
    cartesiennes,
    decoupages,
    distance_a_l_entrainement,
    distances_km,
    zones,
)


def developpement_synthetique():
    """Seize zones réparties sur quatre amas éloignés, deux lignes par zone."""
    lignes = []
    centres = [(0, 0, "A"), (0, 20, "B"), (15, 0, "C"), (15, 20, "D")]
    for latitude, longitude, pays in centres:
        for k in range(4):
            zone = f"{pays}{k}"
            for annee in [2000, 2001]:
                lignes.append({"GDAM_ID": zone, "country": pays, "latitude": latitude + 0.5 * k,
                               "longitude": longitude + 0.5 * k, "harvest_year": annee})
    return pd.DataFrame(lignes)


class TestValidationSpatiale(unittest.TestCase):
    def test_distance_d_un_degre_a_l_equateur(self):
        points = cartesiennes([0, 0], [0, 1])
        self.assertAlmostEqual(distances_km(points[:1], points[1:])[0, 0], 111.19, places=1)
        self.assertAlmostEqual(distances_km(points[:1], points[:1])[0, 0], 0.0, places=6)

    def test_blocs_stables(self):
        table = zones(developpement_synthetique())
        self.assertTrue((blocs_geographiques(table) == blocs_geographiques(table)).all())

    def test_un_pays_tenu_a_l_ecart(self):
        developpement = developpement_synthetique()
        decoupes = decoupages(developpement, "S1")
        self.assertEqual(len(decoupes), 4)
        for apprentissage, evaluation in decoupes:
            self.assertEqual(developpement.loc[evaluation, "country"].nunique(), 1)
            self.assertFalse((apprentissage & evaluation).any())

    def test_zone_tampon(self):
        developpement = developpement_synthetique()
        table = zones(developpement)
        points = pd.DataFrame(cartesiennes(table["latitude"], table["longitude"]), index=table.index)
        for apprentissage, evaluation in decoupages(developpement, "S3"):
            evaluees = developpement.loc[evaluation, "GDAM_ID"].unique()
            apprises = developpement.loc[apprentissage, "GDAM_ID"].unique()
            if len(apprises):
                minimum = distances_km(points.loc[evaluees].to_numpy(), points.loc[apprises].to_numpy()).min()
                self.assertGreaterEqual(minimum, RAYON_TAMPON_KM)
        distance = distance_a_l_entrainement(developpement, decoupages(developpement, "S2"))
        self.assertFalse(distance.isna().any())
        self.assertTrue((distance > 0).all())


if __name__ == "__main__":
    unittest.main()
