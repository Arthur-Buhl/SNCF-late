import pandas as pd

URL = ("https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
       "regularite-mensuelle-tgv-aqst/exports/csv?delimiter=%3B")

df = pd.read_csv(URL, sep=";")
df.to_csv("data/raw/regularite_tgv.csv", sep=";", index=False)
print(df.shape, "->", "data/raw/regularite_tgv.csv")