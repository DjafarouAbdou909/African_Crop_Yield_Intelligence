"""Partition des jeux de modélisation en développement et en ensembles de test.

Chaque ligne reçoit un groupe, une partition et, dans le développement, un pli de
validation croisée. Les groupes rassemblent les lignes qui partagent un lieu, afin
qu'aucun lieu ne soit présent à la fois dans l'entraînement et dans l'évaluation.
L'affectation d'un groupe dépend uniquement d'une empreinte de son identifiant, ce
qui la rend reproductible et stable lorsque des lignes sont ajoutées.
"""

import hashlib

import pandas as pd

PART_TEST_SPATIAL = 0.20
NOMBRE_PLIS = 5
SEL_PARTITION = "grow-africa-partition"
SEL_PLI = "grow-africa-pli"
ANNEE_COUPURE_REGIONAL = 2017

DEVELOPPEMENT = "developpement"
TEST_TEMPOREL = "test_temporel"
TEST_SPATIAL = "test_spatial"
TEST_SPATIO_TEMPOREL = "test_spatio_temporel"


def composantes_connexes(df, colonnes):
    """Relie les lignes qui partagent une valeur dans l'une des colonnes indiquées.

    Deux lignes appartiennent au même groupe lorsqu'elles partagent une valeur,
    directement ou par une chaîne de lignes intermédiaires. Le groupe est désigné par
    la plus petite de ses valeurs, préfixée par le nom de sa colonne. Une ligne dont
    toutes les colonnes sont manquantes reçoit un groupe manquant.
    """
    parent = {}

    def racine(noeud):
        parent.setdefault(noeud, noeud)
        while parent[noeud] != noeud:
            parent[noeud] = parent[parent[noeud]]
            noeud = parent[noeud]
        return noeud

    noeuds = pd.DataFrame({
        colonne: (colonne + "=" + df[colonne].astype("string")) for colonne in colonnes
    }, index=df.index)

    for ligne in noeuds.drop_duplicates().itertuples(index=False):
        presents = [noeud for noeud in ligne if not pd.isna(noeud)]
        for noeud in presents:
            racine(noeud)
        for gauche, droite in zip(presents, presents[1:]):
            racine_gauche, racine_droite = racine(gauche), racine(droite)
            if racine_gauche != racine_droite:
                parent[max(racine_gauche, racine_droite)] = min(racine_gauche, racine_droite)

    premier_present = noeuds.bfill(axis=1).iloc[:, 0]
    return premier_present.map(lambda noeud: pd.NA if pd.isna(noeud) else racine(noeud)).astype("string")


def seau(identifiants, sel, modulo):
    """Associe à chaque identifiant un entier stable compris entre 0 et modulo exclu.

    Un identifiant manquant reçoit une valeur manquante.
    """
    def empreinte(identifiant):
        if pd.isna(identifiant):
            return pd.NA
        condensat = hashlib.sha256(f"{sel}|{identifiant}".encode("utf-8")).hexdigest()
        return int(condensat[:12], 16) % modulo

    return identifiants.map(empreinte).astype("Int64")


def affecter_partitions(groupes, futur):
    """Croise l'appartenance à un groupe tenu à l'écart et à la période future.

    Un groupe est tenu à l'écart lorsque son empreinte tombe dans les 20 premiers
    centièmes. Le croisement définit le développement et trois ensembles de test.
    Les lignes du développement reçoivent un pli de validation croisée par groupe.
    """
    ecarte = seau(groupes, SEL_PARTITION, 100) < round(PART_TEST_SPATIAL * 100)
    partition = pd.Series(DEVELOPPEMENT, index=groupes.index, dtype="string")
    partition[~ecarte & futur] = TEST_TEMPOREL
    partition[ecarte & ~futur] = TEST_SPATIAL
    partition[ecarte & futur] = TEST_SPATIO_TEMPOREL

    pli = seau(groupes, SEL_PLI, NOMBRE_PLIS).where(partition == DEVELOPPEMENT)
    return pd.DataFrame({"groupe": groupes, "partition": partition, "pli": pli})


def partitionner_regional(df, annee_coupure=ANNEE_COUPURE_REGIONAL):
    """Partitionne le jeu de modélisation regional.

    Le groupe réunit une région de niveau 1 et ses unités de niveau 2, ce qui place
    un agrégat régional et ses composantes du même côté. Les années de récolte
    postérieures ou égales à l'année de coupure constituent la période future.
    """
    groupes = composantes_connexes(df, ["L1_GID", "L2_GID"])
    futur = df["harvest_year"] >= annee_coupure
    return df.join(affecter_partitions(groupes, futur))


def partitionner_survey(df):
    """Partitionne le jeu de modélisation survey.

    Le groupe réunit les ménages et les grappes spatiales qui partagent des parcelles,
    ce qui suit un ménage du panel d'une vague à l'autre. À défaut, la zone de niveau 2
    puis la ligne elle-même servent de groupe. La période future correspond à la
    dernière vague des pays qui en comptent au moins deux.
    """
    groupes = (
        composantes_connexes(df, ["id_grappe", "id_menage"])
        .fillna("L2_GID=" + df["L2_GID"].astype("string"))
        .fillna("id_ligne=" + df["id_ligne"].astype("string"))
    )
    annees = df.groupby("Country")["annee_recolte"]
    futur = (annees.transform("nunique") >= 2) & (df["annee_recolte"] == annees.transform("max"))
    return df.join(affecter_partitions(groupes, futur))


def partitionner_cropcut(df, survey_partitionne):
    """Rattache chaque mesure cropcut au groupe et à la partition de sa grappe dans survey.

    Les mesures cropcut proviennent des mêmes grappes que l'enquête éthiopienne. Une
    mesure dont la grappe appartient à un groupe survey tenu à l'écart constitue donc
    une validation externe indépendante de l'entraînement. Une grappe absente de
    survey est traitée comme un groupe à part entière.
    """
    correspondance = (
        survey_partitionne.dropna(subset=["id_grappe"])
        .drop_duplicates("id_grappe")
        .set_index("id_grappe")["groupe"]
    )
    groupes = (
        df["id_grappe"].map(correspondance).astype("string")
        .fillna("id_grappe=" + df["id_grappe"].astype("string"))
    )
    ecarte = (seau(groupes, SEL_PARTITION, 100) < round(PART_TEST_SPATIAL * 100)).fillna(False)
    return df.assign(groupe=groupes, grappe_tenue_a_l_ecart=ecarte.astype(bool))
