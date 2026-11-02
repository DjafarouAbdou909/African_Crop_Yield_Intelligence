import unittest

import numpy as np
import pandas as pd

from src.data.regional import (
    corriger_identifiants_ghana,
    corriger_inversion_surface_production,
    harmoniser_pays,
    jeu_modelisation_regional,
    reconstruire_niveau,
    remplacer_codes_speciaux,
    selectionner_ligne_par_cellule,
)


def ligne(**valeurs):
    base = {
        "GDAM_ID": "L2ETH1", "L0_GID": "L0ETH075", "L1_GID": "L1ETH1", "L2_GID": "L2ETH1", "L3_GID": np.nan,
        "level": 2.0, "country": "Ethiopia", "crop": "Maize", "season_name": "Main",
        "crop_production_system": "All (PS)", "harvest_year": 2015, "Source": "HarvestStat",
        "areaHa": 100.0, "productionTon": 150.0, "yieldTonHa": 1.5,
    }
    base.update(valeurs)
    return base


class TestCodesSpeciaux(unittest.TestCase):
    def test_codes_et_rendements_derives_invalides(self):
        df = pd.DataFrame([
            ligne(areaHa=-999.0, productionTon=10.0, yieldTonHa=-10 / 999),
            ligne(productionTon=-99.0, yieldTonHa=-99.0),
            ligne(),
        ])
        resultat = remplacer_codes_speciaux(df)

        self.assertTrue(resultat.loc[0, ["areaHa", "yieldTonHa"]].isna().all())
        self.assertTrue(resultat.loc[1, ["productionTon", "yieldTonHa"]].isna().all())
        self.assertEqual(resultat.loc[2, "yieldTonHa"], 1.5)


class TestInversionSurfaceProduction(unittest.TestCase):
    def test_permute_uniquement_les_lignes_inversees(self):
        df = pd.DataFrame([
            ligne(),
            ligne(crop="Cassava", areaHa=1000.0, productionTon=100.0, yieldTonHa=10.0),
            ligne(areaHa=100.0, productionTon=150.0, yieldTonHa=3.0),
        ])
        resultat = corriger_inversion_surface_production(df)

        self.assertEqual(resultat["flag_surface_production_permutees"].tolist(), [False, True, False])
        self.assertEqual(resultat["flag_relation_rendement_inexpliquee"].tolist(), [False, False, True])
        self.assertEqual(resultat.loc[1, "areaHa"], 100.0)
        self.assertEqual(resultat.loc[1, "productionTon"], 1000.0)
        self.assertEqual(resultat.loc[1, "yieldTonHa"], 10.0)


class TestReferentielGeographique(unittest.TestCase):
    def test_codes_ghana_unifies(self):
        df = pd.DataFrame([ligne(L0_GID="L0GHA097", GDAM_ID="L0GHA097"), ligne(L0_GID="L0GIN088")])
        resultat = corriger_identifiants_ghana(df)

        self.assertEqual(resultat["L0_GID"].tolist(), ["L0GHA086", "L0GIN088"])
        self.assertEqual(resultat.loc[0, "GDAM_ID"], "L0GHA086")

    def test_libelles_pays_unifies(self):
        df = pd.DataFrame([ligne(country="DRC"), ligne(country="Tanzania, United Republic of")])
        self.assertEqual(
            harmoniser_pays(df)["country"].tolist(),
            ["Democratic Republic of the Congo", "Tanzania"],
        )

    def test_niveau_reconstruit_ou_signale(self):
        df = pd.DataFrame([
            ligne(level=np.nan, L2_GID=np.nan),
            ligne(level=np.nan, L1_GID=np.nan, L2_GID=np.nan),
            ligne(level=2.0, L2_GID=np.nan),
        ])
        resultat = reconstruire_niveau(df)

        self.assertEqual(resultat.loc[0, "level"], 1)
        self.assertTrue(pd.isna(resultat.loc[1, "level"]))
        self.assertEqual(resultat["flag_niveau_ambigu"].tolist(), [False, True, False])
        self.assertEqual(resultat["flag_gid_incomplet"].tolist(), [False, False, True])


class TestSelectionLigneParCellule(unittest.TestCase):
    def test_priorite_au_systeme_global_puis_a_harveststat(self):
        df = pd.DataFrame([
            ligne(crop_production_system="Rainfed (PS)", yieldTonHa=1.2),
            ligne(Source="FAO_subnational", yieldTonHa=1.4),
            ligne(yieldTonHa=1.5),
            ligne(crop="Rice", Source="RCeA", crop_production_system=np.nan),
        ])
        resultat = selectionner_ligne_par_cellule(df)

        self.assertEqual(resultat["flag_doublon_cellule"].tolist(), [True, True, False, False])

    def test_ligne_avec_rendement_prioritaire(self):
        df = pd.DataFrame([ligne(yieldTonHa=np.nan), ligne(Source="RCeA", crop_production_system="irrigated")])
        resultat = selectionner_ligne_par_cellule(df)

        self.assertEqual(resultat["flag_doublon_cellule"].tolist(), [True, False])

    def test_jeu_modelisation_filtre_niveau_doublons_et_bornes(self):
        df = pd.DataFrame([ligne(level=0), ligne(), ligne(), ligne(yieldTonHa=np.nan)])
        df["level"] = df["level"].astype("Int64")
        df["flag_doublon_cellule"] = [False, False, True, False]
        df["flag_rendement_hors_bornes"] = False

        self.assertEqual(jeu_modelisation_regional(df).index.tolist(), [1])


if __name__ == "__main__":
    unittest.main()
