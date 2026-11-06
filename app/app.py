"""Application Streamlit de démonstration du modèle de rendement régional.

Lancement depuis la racine du projet avec la commande streamlit run app/app.py,
après l'export des ressources par python -m app.preparer.
"""

import json
import sys
from pathlib import Path

import altair as alt
import lightgbm as lgb
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from src.models.apprentissage import matrice  # noqa: E402
from src.models.interpretation import FAMILLES, contributions  # noqa: E402

RESSOURCES = Path(__file__).resolve().parent / "ressources"
NIVEAUX = [0.8, 0.9]
LIBELLES = {
    "crop": "Culture", "saison": "Saison", "country": "Pays", "Source": "Source statistique",
    "level": "Niveau administratif", "crop_production_system": "Système de production",
    "harvest_year": "Année de récolte", "latitude": "Latitude", "longitude": "Longitude",
    "log_surface_zone": "Surface de la région", "mois_semis": "Mois de semis", "mois_recolte": "Mois de récolte",
    "duree_saison": "Durée de saison", "pluie_cumul": "Pluie de saison", "pluie_jours": "Jours de pluie",
    "sequence_seche_max": "Plus longue séquence sèche", "bilan_hydrique": "Bilan hydrique",
    "et0_cumul": "Évapotranspiration de référence", "degres_jours": "Degrés-jours de croissance",
    "degres_jours_30": "Chaleur au-delà de 30 °C", "degres_jours_35": "Chaleur au-delà de 35 °C",
    "tmax_moyenne": "Température maximale moyenne", "tmin_moyenne": "Température minimale moyenne",
    "dpv_moyen": "Déficit de pression de vapeur", "rayonnement_moyen": "Rayonnement solaire",
    "argile_0_30": "Argile", "limon_0_30": "Limon", "sable_0_30": "Sable",
    "carbone_organique_0_30": "Carbone organique du sol", "azote_0_30": "Azote du sol", "ph_0_30": "pH du sol",
    "cec_0_30": "Capacité d'échange cationique", "densite_apparente_0_30": "Densité apparente du sol",
    "elements_grossiers_0_30": "Éléments grossiers", "altitude_moyenne": "Altitude", "pente_moyenne": "Pente",
}
UNITES = {
    "pluie_cumul": "mm", "pluie_jours": "jours", "sequence_seche_max": "jours", "bilan_hydrique": "mm",
    "et0_cumul": "mm", "tmax_moyenne": "°C", "tmin_moyenne": "°C", "degres_jours_30": "°C.jour",
    "argile_0_30": "%", "sable_0_30": "%", "carbone_organique_0_30": "g/kg", "ph_0_30": "", "altitude_moyenne": "m",
    "pente_moyenne": "degrés",
}
PARTITIONS = {
    "developpement": "Entraînement. Le modèle a vu cette ligne, et la prédiction n'est pas une mesure de performance.",
    "test_temporel": "Test temporel. Année future d'une région connue, jamais vue à l'entraînement.",
    "test_spatial": "Test spatial. Région jamais vue à l'entraînement.",
    "test_spatio_temporel": "Test spatio-temporel. Région et année jamais vues à l'entraînement.",
}
FAMILLE_DE = {variable: famille for famille, membres in FAMILLES.items() for variable in membres}


@st.cache_resource
def charger_modele():
    modele = lgb.Booster(model_file=str(RESSOURCES / "regional_modele.txt"))
    description = json.loads((RESSOURCES / "regional_modele.json").read_text())
    largeurs = pd.read_csv(RESSOURCES / "regional_intervalles.csv", index_col=0)
    largeurs.columns = [float(c) for c in largeurs.columns]
    return modele, description, largeurs


@st.cache_data
def charger_variables():
    table = pd.read_parquet(RESSOURCES / "regional_variables.parquet")
    nom = table["admin_2"].fillna(table["admin_1"]).astype(str)
    table["region"] = np.where(table["level"] == 2, nom + ", " + table["admin_1"].astype(str), nom)
    table["saison"] = table["saison"].fillna("Unique")
    return table


@st.cache_data
def charger_performance():
    return pd.read_csv(RESSOURCES / "performance.csv")


def predire(lignes):
    """Retourne la prédiction et les bornes des intervalles de chaque ligne."""
    modele, description, largeurs = charger_modele()
    entree = lignes.assign(saison=lignes["saison"].replace("Unique", np.nan))
    x, _ = matrice(entree, description["categorielles"], description["numeriques"], description["categories"])
    prediction = np.exp(modele.predict(x))
    resultat = pd.DataFrame({"prediction": prediction}, index=lignes.index)
    for niveau in NIVEAUX:
        demi = lignes["crop"].map(largeurs[niveau]).fillna(largeurs.loc["ensemble", niveau]).to_numpy()
        resultat[f"bas_{niveau:.0%}"] = prediction * np.exp(-demi)
        resultat[f"haut_{niveau:.0%}"] = prediction * np.exp(demi)
    return resultat


def selection_serie(table, cle):
    """Affiche les listes de choix du pays, de la région, de la culture et de la saison."""
    colonnes = st.columns(4)
    pays = colonnes[0].selectbox("Pays", sorted(table["country"].unique()), key=f"{cle}_pays",
                                 index=sorted(table["country"].unique()).index("Malawi"))
    sous = table[table["country"] == pays]
    region = colonnes[1].selectbox("Région", sorted(sous["region"].unique()), key=f"{cle}_region")
    sous = sous[sous["region"] == region]
    cultures = sorted(sous["crop"].unique())
    culture = colonnes[2].selectbox("Culture", cultures, key=f"{cle}_culture",
                                    index=cultures.index("Maize") if "Maize" in cultures else 0)
    sous = sous[sous["crop"] == culture]
    saison = colonnes[3].selectbox("Saison", sorted(sous["saison"].unique()), key=f"{cle}_saison")
    return sous[sous["saison"] == saison].sort_values("harvest_year")


def page_prediction(table):
    st.header("Prédire un rendement régional")
    st.write("Choisissez une région, une culture, une saison et une année de récolte. Le modèle prédit le rendement "
             "à partir de la culture, du lieu, de l'année, du climat de la saison, du sol et du relief.")
    serie = selection_serie(table, "prediction")
    annee = st.select_slider("Année de récolte", options=serie["harvest_year"].tolist(),
                             value=serie["harvest_year"].iloc[-1])
    ligne = serie[serie["harvest_year"] == annee].head(1)
    resultat = predire(ligne).iloc[0]
    observe = ligne["yieldTonHa"].iloc[0]

    a, b, c, d = st.columns(4)
    a.metric("Rendement prédit", f"{resultat['prediction']:.2f} t/ha")
    b.metric("Intervalle à 80 %", f"{resultat['bas_80%']:.2f} à {resultat['haut_80%']:.2f}")
    c.metric("Intervalle à 90 %", f"{resultat['bas_90%']:.2f} à {resultat['haut_90%']:.2f}")
    d.metric("Rendement observé", f"{observe:.2f} t/ha", f"{(resultat['prediction'] / observe - 1):+.0%} d'écart",
             delta_color="off")
    st.info(PARTITIONS[ligne["partition"].iloc[0]] + f" Source statistique {ligne['Source'].iloc[0]}.")

    modele, description, _ = charger_modele()
    entree = ligne.assign(saison=ligne["saison"].replace("Unique", np.nan))
    contribs, base = contributions(modele, description, entree)
    effets = contribs.iloc[0]
    graphe = pd.DataFrame({"variable": [LIBELLES.get(v, v) for v in effets.index],
                           "famille": [FAMILLE_DE.get(v, "autre") for v in effets.index],
                           "effet": np.expm1(effets.to_numpy()) * 100})
    graphe = graphe.reindex(graphe["effet"].abs().sort_values(ascending=False).index).head(12)
    st.subheader("Ce qui explique cette prédiction")
    st.write(f"Point de départ, le rendement moyen du modèle, de {np.exp(base.iloc[0]):.2f} t/ha. Chaque barre "
             "indique de combien une variable multiplie ce rendement, en pourcentage. Il s'agit du fonctionnement "
             "du modèle, et non d'un effet causal.")
    st.altair_chart(alt.Chart(graphe).mark_bar().encode(
        x=alt.X("effet:Q", title="Effet sur le rendement prédit, en %"),
        y=alt.Y("variable:N", sort=None, title=None),
        color=alt.Color("famille:N", title="Famille"),
        tooltip=["variable", "famille", alt.Tooltip("effet:Q", format="+.1f")],
    ), width="stretch")

    st.subheader("Conditions de la saison")
    variables = ["pluie_cumul", "pluie_jours", "sequence_seche_max", "bilan_hydrique", "tmax_moyenne",
                 "degres_jours_30", "argile_0_30", "sable_0_30", "carbone_organique_0_30", "ph_0_30",
                 "altitude_moyenne", "pente_moyenne"]
    valeurs = ligne[variables].iloc[0]
    st.dataframe(pd.DataFrame({
        "Variable": [LIBELLES[v] for v in variables],
        "Valeur": [("non disponible" if pd.isna(valeurs[v]) else f"{valeurs[v]:.1f} {UNITES.get(v, '')}".strip())
                   for v in variables],
    }), hide_index=True, width="stretch")
    if pd.isna(valeurs["pluie_cumul"]):
        st.caption("La pluie IMERG n'est disponible qu'à partir de juin 2000. Le modèle prédit sans elle.")


def page_serie(table):
    st.header("Série d'une région")
    st.write("Rendements observés et prédits année par année, avec l'intervalle de prédiction à 80 %.")
    serie = selection_serie(table, "serie")
    resultat = serie[["harvest_year", "yieldTonHa", "partition"]].join(predire(serie))
    resultat["ensemble"] = np.where(resultat["partition"] == "developpement", "entraînement", "test")
    base = alt.Chart(resultat).encode(x=alt.X("harvest_year:O", title="Année de récolte"))
    bande = base.mark_area(opacity=0.25).encode(y=alt.Y("bas_80%:Q", title="Rendement, t/ha"), y2="haut_80%:Q")
    predite = base.mark_line(color="#1f77b4").encode(y="prediction:Q")
    observee = base.mark_point(filled=True, size=60).encode(
        y="yieldTonHa:Q", color=alt.Color("ensemble:N", title="Ligne observée",
                                          scale=alt.Scale(range=["#7f7f7f", "#d62728"])),
        tooltip=["harvest_year", alt.Tooltip("yieldTonHa:Q", format=".2f", title="observé"),
                 alt.Tooltip("prediction:Q", format=".2f", title="prédit")])
    st.altair_chart((bande + predite + observee).properties(height=420), width="stretch")
    test = resultat[resultat["ensemble"] == "test"]
    if len(test):
        erreur = np.mean(np.abs(np.log(test["prediction"]) - np.log(test["yieldTonHa"])))
        st.write(f"Sur les {len(test)} années de test de cette série, l'erreur relative typique vaut "
                 f"{np.expm1(erreur):.0%}, et l'intervalle à 80 % contient {((test['yieldTonHa'] >= test['bas_80%']) & (test['yieldTonHa'] <= test['haut_80%'])).mean():.0%} des rendements observés.")
    st.caption("Les points gris ont servi à l'entraînement, les points rouges sont des années ou des régions de test.")


def page_performance():
    st.header("Performance mesurée sur les ensembles de test")
    st.write("Les modèles ont été choisis sur les seules données d'entraînement, figés, puis évalués une seule fois "
             "sur des régions, des années et des parcelles jamais vues. La métrique principale est l'erreur absolue "
             "moyenne sur le logarithme du rendement, et la référence prédit la moyenne historique du lieu.")
    performance = charger_performance()
    noms = {"test_temporel": "Années futures, lieux connus", "test_spatial": "Lieux nouveaux",
            "test_spatio_temporel": "Lieux nouveaux, années futures",
            "cropcut_grappes_tenues_a_l_ecart": "Mesures par coupe, grappes nouvelles"}
    tableau = pd.DataFrame({
        "Modèle": performance["modele"].map({"regional": "Régional", "survey": "Parcelles d'enquête"}),
        "Ensemble de test": performance["ensemble"].map(noms),
        "Lignes": performance["lignes"].astype(int),
        "Erreur du modèle": performance["mae_log"].round(3),
        "Erreur de la référence": performance["mae_log_reference"].round(3),
        "Gain sur la référence": (performance["competence"] * 100).round(1).astype(str) + " %",
        "Erreur relative typique": (performance["erreur_relative_typique"] * 100).round(0).astype(int).astype(str) + " %",
        "Couverture à 80 %": (performance["couverture_80%"] * 100).round(1).astype(str) + " %",
    })
    st.dataframe(tableau, hide_index=True, width="stretch")
    st.subheader("À retenir")
    st.markdown(
        "- Le modèle régional réduit l'erreur de la référence de 17 à 22 %, pour une erreur relative typique "
        "de 36 à 40 %.\n"
        "- Le modèle de parcelle ne la réduit que de 5 à 8 %, car les parcelles voisines diffèrent fortement pour "
        "des raisons que les variables disponibles ne décrivent pas.\n"
        "- Le climat de la saison n'explique qu'environ 2 % de la variation annuelle des rendements régionaux, "
        "une fois la tendance retirée.\n"
        "- Les rendements d'enquête sont déclarés et dépassent d'environ 40 % les mesures par coupe.\n"
        "- Le modèle ne prolonge pas la hausse des rendements au-delà de 2016, dernière année d'entraînement.\n"
        "- Quinze rendements de tabac du Malawi en 2016 sont des erreurs d'unité de la base, non corrigées."
    )


def page_a_propos():
    st.header("À propos")
    st.markdown(
        "**African Crop Yield Intelligence** prédit les rendements agricoles africains à partir de la base "
        "GROW-Africa, selon la méthode CRISP-DM.\n\n"
        "- **Données de rendement.** GROW-Africa, 145 877 rendements régionaux de 45 pays de 1960 à 2023, dont "
        "142 247 retenus à partir de 1981.\n"
        "- **Climat.** NASA POWER pour la température, le rayonnement et le vent, et IMERG pour la pluie, agrégés "
        "sur la saison de chaque culture, avec l'évapotranspiration FAO-56.\n"
        "- **Sols.** SoilGrids 2.0 à 1 km, de 0 à 30 cm.\n"
        "- **Relief.** Copernicus DEM à 90 m.\n"
        "- **Modèle.** LightGBM sur le logarithme du rendement, avec des intervalles de prédiction conformes par "
        "culture et des contributions de Shapley.\n\n"
        "Ces prédictions servent l'analyse et la recherche, et non la décision opérationnelle. La documentation "
        "complète se trouve dans le dossier `docs` du dépôt."
    )


st.set_page_config(page_title="Rendements agricoles en Afrique", page_icon="🌾", layout="wide")
# Streamlit déclare ses pages en anglais, ce qui conduit les navigateurs à « traduire » le
# texte français et à le déformer. La page est donc déclarée en français et exclue de la
# traduction automatique.
components.html(
    "<script>const racine = window.parent.document.documentElement;"
    "racine.setAttribute('lang', 'fr'); racine.setAttribute('translate', 'no');"
    "racine.classList.add('notranslate');</script>",
    height=0,
)
st.title("African Crop Yield Intelligence")
page = st.sidebar.radio("Navigation", ["Prédiction", "Série d'une région", "Performance", "À propos"])
st.sidebar.caption("Modèle régional LightGBM, entraîné sur GROW-Africa de 1981 à 2016.")
if page == "Prédiction":
    page_prediction(charger_variables())
elif page == "Série d'une région":
    page_serie(charger_variables())
elif page == "Performance":
    page_performance()
else:
    page_a_propos()
