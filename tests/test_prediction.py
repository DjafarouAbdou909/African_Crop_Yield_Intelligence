import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.apprentissage import PARAMETRES, entrainer, matrice
from src.models.prediction import predire_avec_intervalles


class TestPrediction(unittest.TestCase):
    def test_prediction_et_intervalles_depuis_le_disque(self):
        dossier = Path(tempfile.mkdtemp())
        generateur = np.random.default_rng(2)
        table = pd.DataFrame({"Crop": generateur.choice(["Maize", "Teff"], 200), "x": generateur.normal(size=200)})
        table["rendement"] = np.exp(table["x"])
        x, categories = matrice(table, ["Crop"], ["x"])
        entrainer(x, table["rendement"], {**PARAMETRES, "min_data_in_leaf": 5, "num_threads": 1}, 20).save_model(
            str(dossier / "survey_modele.txt"))
        (dossier / "survey_modele.json").write_text(json.dumps(
            {"categorielles": ["Crop"], "numeriques": ["x"], "categories": categories}))
        pd.DataFrame({"0.8": [0.5, 0.2], "0.9": [0.7, 0.3]}, index=["ensemble", "Teff"]).to_csv(
            dossier / "survey_intervalles.csv")
        nouvelles = pd.DataFrame({"Crop": ["Teff", "Rice"], "x": [0.0, 1.0]})
        resultat = predire_avec_intervalles("survey", nouvelles, "Crop", dossier)
        prediction = resultat["rendement_predit_t_ha"]
        np.testing.assert_allclose(resultat["borne_haute_80%"], prediction * np.exp([0.2, 0.5]))
        np.testing.assert_allclose(resultat["borne_basse_90%"], prediction * np.exp([-0.3, -0.7]))
        self.assertTrue((prediction > 0).all())


if __name__ == "__main__":
    unittest.main()
