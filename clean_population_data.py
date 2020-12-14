# Make population data into clean .csv

import pandas as pd

df_pop = pd.read_excel(
        "co-est2019-annres.xlsx", usecols="A,M", skiprows=[0, 1, 2, 4], skipfooter=6,
    ).rename(columns={"Unnamed: 0": "geographic area", 2019: "population"})
df_pop[["county", "state"]] = df_pop["geographic area"].str.split(
    "County,", expand=True
)[[0, 1]]
df_pop["county"] = df_pop["county"].str.strip(" .")
df_pop["state"] = df_pop["state"].str.strip(" ")
df_pop = df_pop.drop(columns="geographic area")
# Make NYC its own entry
df_nyc_pop = pd.DataFrame(
    [[8336817, "New York City", "New York"]],
    columns=["population", "county", "state"],
)
df_pop = df_pop.append(df_nyc_pop)

df_pop.to_csv("2019_county_population.csv", index=False)