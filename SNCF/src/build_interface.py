"""Génère interface.html : classement des liaisons/gares par nombre de départs
et calcul du retard cumulé d'un trajet entre deux gares (avec correspondances)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "processed" / "regularite_clean.csv"
TEMPLATE = Path(__file__).resolve().parent / "interface_template.html"
OUT = ROOT / "interface.html"


def agreger(df):
    df = df.copy()
    df["_retard_tous"] = df["retard_moyen_tous_trains_arrivee"] * df["nb_circules"]
    df["_poids_tous"] = df["nb_circules"].where(df["retard_moyen_tous_trains_arrivee"].notna(), 0)
    df["_retard_en_retard"] = df["retard_moyen_arrivee"] * df["nb_train_retard_arrivee"]
    df["_poids_en_retard"] = df["nb_train_retard_arrivee"].where(df["retard_moyen_arrivee"].notna(), 0)
    df["_duree"] = df["duree_moyenne"] * df["nb_circules"]
    df["_poids_duree"] = df["nb_circules"].where(df["duree_moyenne"].notna(), 0)

    g = df.groupby(["gare_depart", "gare_arrivee", "service", "annee"], as_index=False).agg(
        prevus=("nb_train_prevu", "sum"),
        circules=("nb_circules", "sum"),
        annules=("nb_annulation", "sum"),
        retards=("nb_train_retard_arrivee", "sum"),
        sup60=("nb_train_retard_sup_60", "sum"),
        r_tous=("_retard_tous", "sum"),
        p_tous=("_poids_tous", "sum"),
        r_ret=("_retard_en_retard", "sum"),
        p_ret=("_poids_en_retard", "sum"),
        duree=("_duree", "sum"),
        p_duree=("_poids_duree", "sum"),
    )
    return g


def main():
    df = pd.read_csv(SRC)
    g = agreger(df)
    gares = sorted(set(g["gare_depart"]) | set(g["gare_arrivee"]))
    idx = {gare: i for i, gare in enumerate(gares)}
    cols = ["prevus", "circules", "annules", "retards", "sup60", "r_tous", "p_tous", "r_ret", "p_ret", "duree", "p_duree"]
    lignes = [
        [idx[r.gare_depart], idx[r.gare_arrivee], int(r.service == "INTERNATIONAL"), int(r.annee)]
        + [round(float(getattr(r, c)), 1) for c in cols]
        for r in g.itertuples()
    ]
    data = {
        "gares": gares,
        "cols": ["dep", "arr", "intl", "annee"] + cols,
        "lignes": lignes,
        "periode": [str(df["date"].min())[:7], str(df["date"].max())[:7]],
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")
    print(f"{len(lignes)} lignes agrégées, {len(gares)} gares -> {OUT}")


if __name__ == "__main__":
    main()
