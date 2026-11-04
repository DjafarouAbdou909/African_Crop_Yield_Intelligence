"""Sélection des modèles retenus, sur le seul développement.

La variante retenue pour chaque jeu découle des bilans des trois schémas de
validation interne, décrits dans docs/modeling.md.

- Pour regional, le modèle complet est retenu. Aucune famille de variables ne le
  dégrade en moyenne sur les trois schémas, le climat et la source l'améliorent dans
  les schémas temporels, et les sols et le relief l'améliorent dans le schéma
  temporel mais le dégradent dans le schéma spatio-temporel.
- Pour survey, le modèle sans variables climatiques est retenu. Le climat n'apporte
  rien en validation croisée et dégrade significativement la prédiction des vagues
  futures, car chaque pays ne compte que deux à sept vagues.

Le nombre d'arbres minimise la moyenne non pondérée des erreurs des trois schémas,
ce qui équilibre la prédiction de lieux nouveaux, d'années futures et des deux.
"""

import pandas as pd

from .apprentissage import PARAMETRES
from .bilan import courbe_paliers
from .experiences import JEUX, SCHEMAS, experiences_regional, experiences_survey

VARIANTES_RETENUES = {"regional": "complet", "survey": "sans_climat_fin"}


def courbes_retenues(jeu, developpement):
    """Retourne l'erreur de la variante retenue par nombre d'arbres, pour chaque schéma et en moyenne."""
    cible = JEUX[jeu][0]
    courbes = pd.DataFrame({s: courbe_paliers(jeu, s, developpement, cible, VARIANTES_RETENUES[jeu]) for s in SCHEMAS})
    courbes["moyenne"] = courbes.mean(axis=1)
    return courbes


def configuration_retenue(jeu, developpement):
    """Retourne les variables catégorielles et numériques, les paramètres et le nombre d'arbres retenus."""
    definition = {"regional": experiences_regional, "survey": experiences_survey}[jeu]()[VARIANTES_RETENUES[jeu]]
    iterations = int(courbes_retenues(jeu, developpement)["moyenne"].idxmin())
    parametres = {**PARAMETRES, **definition.get("parametres", {})}
    return definition["categorielles"], definition["numeriques"], parametres, iterations
