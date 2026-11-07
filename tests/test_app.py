import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RESSOURCES = RACINE / "app" / "ressources"


@unittest.skipUnless((RESSOURCES / "regional_modele.txt").exists(), "ressources de l'application absentes")
class TestApplication(unittest.TestCase):
    def test_les_quatre_pages_s_executent(self):
        from streamlit.testing.v1 import AppTest

        application = AppTest.from_file(str(RACINE / "app" / "app.py"), default_timeout=180).run()
        self.assertFalse(application.exception)
        etiquettes = [m.label for m in application.metric]
        self.assertIn("Rendement prédit", etiquettes)
        for page in ["Série d'une région", "Performance", "À propos"]:
            application.sidebar.radio[0].set_value(page).run()
            self.assertFalse(application.exception, page)

    def test_parametres_de_l_adresse(self):
        from streamlit.testing.v1 import AppTest

        application = AppTest.from_file(str(RACINE / "app" / "app.py"), default_timeout=180)
        for cle, valeur in {"page": "serie", "pays": "Malawi", "region": "Lilongwe", "culture": "Maize"}.items():
            application.query_params[cle] = valeur
        application.run()
        self.assertFalse(application.exception)
        self.assertEqual(application.sidebar.radio[0].value, "Série d'une région")
        self.assertEqual([s.value for s in application.selectbox][:3], ["Malawi", "Lilongwe", "Maize"])


if __name__ == "__main__":
    unittest.main()
