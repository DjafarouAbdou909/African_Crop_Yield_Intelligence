import unittest

import numpy as np
import pandas as pd

from src.evaluation.partitions import (
    DEVELOPPEMENT,
    TEST_SPATIAL,
    TEST_SPATIO_TEMPOREL,
    TEST_TEMPOREL,
    affecter_partitions,
    composantes_connexes,
    partitionner_cropcut,
    partitionner_regional,
    partitionner_survey,
    seau,
)


class TestComposantesConnexes(unittest.TestCase):
    def test_relie_les_lignes_par_chaine(self):
        df = pd.DataFrame({
            "grappe": ["g1", "g2", "g2", "g3", np.nan],
            "menage": ["m1", "m1", "m2", "m3", np.nan],
        })
        groupes = composantes_connexes(df, ["grappe", "menage"])

        self.assertEqual(groupes.iloc[0], groupes.iloc[1])
        self.assertEqual(groupes.iloc[1], groupes.iloc[2])
        self.assertNotEqual(groupes.iloc[0], groupes.iloc[3])
        self.assertTrue(pd.isna(groupes.iloc[4]))

    def test_independant_de_l_ordre_des_lignes(self):
        df = pd.DataFrame({"a": ["x", "y", "y", "z"], "b": ["1", "1", "2", "3"]})
        directs = composantes_connexes(df, ["a", "b"])
        inverses = composantes_connexes(df.iloc[::-1], ["a", "b"]).reindex(df.index)
        pd.testing.assert_series_equal(directs, inverses)


class TestAffectation(unittest.TestCase):
    def test_seau_stable_et_borne(self):
        identifiants = pd.Series([f"groupe_{i}" for i in range(1000)] + [np.nan])
        premier = seau(identifiants, "sel", 100)
        second = seau(identifiants, "sel", 100)

        pd.testing.assert_series_equal(premier, second)
        self.assertTrue(premier.dropna().between(0, 99).all())
        self.assertTrue(pd.isna(premier.iloc[-1]))
        self.assertAlmostEqual(float((premier.dropna() < 20).mean()), 0.20, delta=0.04)

    def test_un_groupe_reste_d_un_seul_cote(self):
        groupes = pd.Series([f"g{i % 50}" for i in range(500)], dtype="string")
        futur = pd.Series([i % 3 == 0 for i in range(500)])
        resultat = affecter_partitions(groupes, futur)

        ecarte = resultat["partition"].isin([TEST_SPATIAL, TEST_SPATIO_TEMPOREL])
        self.assertTrue((ecarte.groupby(groupes).nunique() == 1).all())
        self.assertTrue(resultat.loc[futur & ~ecarte, "partition"].eq(TEST_TEMPOREL).all())
        self.assertTrue(resultat["pli"].notna().eq(resultat["partition"] == DEVELOPPEMENT).all())
        self.assertTrue((resultat.dropna(subset=["pli"]).groupby("groupe")["pli"].nunique() == 1).all())


class TestPartitionsParFichier(unittest.TestCase):
    def test_regional_place_niveau_1_et_niveau_2_ensemble(self):
        df = pd.DataFrame({
            "L1_GID": ["R1", "R1", "R2", "R3"],
            "L2_GID": [np.nan, "D1", "D1", np.nan],
            "harvest_year": [2010, 2010, 2020, 2020],
        })
        resultat = partitionner_regional(df)

        self.assertEqual(resultat["groupe"].nunique(), 2)
        self.assertEqual(resultat["partition"].isin([TEST_TEMPOREL, TEST_SPATIO_TEMPOREL]).tolist(),
                         [False, False, True, True])

    def test_survey_futur_limite_aux_pays_a_plusieurs_vagues(self):
        df = pd.DataFrame({
            "Country": ["A", "A", "B"],
            "annee_recolte": [2015, 2019, 2022],
            "id_grappe": ["A_g1", "A_g1", np.nan],
            "id_menage": ["A_m1", "A_m1", np.nan],
            "L2_GID": ["L2A", "L2A", np.nan],
            "id_ligne": ["s_0", "s_1", "s_2"],
        })
        resultat = partitionner_survey(df)

        self.assertEqual(resultat["groupe"].iloc[0], resultat["groupe"].iloc[1])
        self.assertEqual(resultat["groupe"].iloc[2], "id_ligne=s_2")
        self.assertEqual(resultat["partition"].isin([TEST_TEMPOREL, TEST_SPATIO_TEMPOREL]).tolist(),
                         [False, True, False])

    def test_cropcut_herite_du_groupe_survey(self):
        survey = pd.DataFrame({"id_grappe": ["g1", "g2"], "groupe": ["id_grappe=g1", "id_grappe=g1"]})
        cropcut = pd.DataFrame({"id_grappe": ["g2", "g9", np.nan]})
        resultat = partitionner_cropcut(cropcut, survey)

        self.assertEqual(resultat["groupe"].tolist()[:2], ["id_grappe=g1", "id_grappe=g9"])
        self.assertFalse(resultat["grappe_tenue_a_l_ecart"].iloc[2])


if __name__ == "__main__":
    unittest.main()
