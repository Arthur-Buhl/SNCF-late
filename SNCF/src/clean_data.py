from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "regularite_tgv.csv"
OUT = ROOT / "data" / "processed" / "regularite_clean.csv"

COLS_COMMENTAIRES = ["commentaire_annulation", "commentaire_retards_depart", "commentaires_retard_arrivee"]
COLS_COMPTAGES = [
    "nb_train_prevu", "nb_annulation", "nb_train_depart_retard", "nb_train_retard_arrivee",
    "nb_train_retard_sup_15", "nb_train_retard_sup_30", "nb_train_retard_sup_60",
]
COLS_RETARDS_TRAINS_EN_RETARD = ["retard_moyen_depart", "retard_moyen_arrivee", "retard_moyen_trains_retard_sup15"]
COLS_RETARDS_TOUS_TRAINS = ["retard_moyen_tous_trains_depart", "retard_moyen_tous_trains_arrivee"]
COLS_CAUSES = [
    "prct_cause_externe", "prct_cause_infra", "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant", "prct_cause_gestion_gare", "prct_cause_prise_en_charge_voyageurs",
]


def charger():
    return pd.read_csv(RAW, sep=";")


def nettoyer(df):
    df = df.drop(columns=COLS_COMMENTAIRES).drop_duplicates()

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    for col in ["service", "gare_depart", "gare_arrivee"]:
        df[col] = df[col].str.strip().str.upper()

    df = df[df["nb_train_prevu"] > 0]
    df = df[df["nb_annulation"] <= df["nb_train_prevu"]]
    df = df[df["nb_train_retard_arrivee"] <= df["nb_train_prevu"] - df["nb_annulation"]]

    df[COLS_COMPTAGES] = df[COLS_COMPTAGES].mask(df[COLS_COMPTAGES] < 0)
    df[COLS_RETARDS_TRAINS_EN_RETARD] = df[COLS_RETARDS_TRAINS_EN_RETARD].mask(df[COLS_RETARDS_TRAINS_EN_RETARD] < 0)
    df[COLS_RETARDS_TOUS_TRAINS] = df[COLS_RETARDS_TOUS_TRAINS].mask(df[COLS_RETARDS_TOUS_TRAINS] < -30)
    df["duree_moyenne"] = df["duree_moyenne"].replace(0, np.nan)
    df.loc[df[COLS_CAUSES].sum(axis=1) == 0, COLS_CAUSES] = np.nan

    return df.reset_index(drop=True)


def enrichir(df):
    df["annee"] = df["date"].dt.year
    df["mois"] = df["date"].dt.month
    df["liaison"] = df["gare_depart"] + " → " + df["gare_arrivee"]
    df["nb_circules"] = df["nb_train_prevu"] - df["nb_annulation"]
    df["taux_annulation"] = df["nb_annulation"] / df["nb_train_prevu"] * 100
    df["taux_retard_arrivee"] = df["nb_train_retard_arrivee"] / df["nb_circules"].replace(0, np.nan) * 100
    df["taux_ponctualite"] = 100 - df["taux_retard_arrivee"]
    return df


def main():
    brut = charger()
    df = enrichir(nettoyer(brut))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(brut)} lignes brutes -> {len(df)} lignes propres ({len(brut) - len(df)} supprimées)")
    print(f"Fichier : {OUT}")


if __name__ == "__main__":
    main()
