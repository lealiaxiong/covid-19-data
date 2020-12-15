# Get new COVID-19 county data from the NY Times Github and combine with population data

import pandas as pd

# Import NY Times COVID-19 data by county
df_counties = pd.read_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv").rename(
    columns={"cases": "total cases", "deaths": "total deaths"}
)
df_counties["date"] = pd.to_datetime(df_counties["date"])

# Import population data
df_pop = pd.read_csv("2019_county_populations.csv")

# Merge COVID-19 and population data
df_counties = pd.merge(df_counties, df_pop)

# Make column of "county, state"
df_counties["county, state"] = df_counties[["county", "state"]].agg(
    ", ".join, axis=1
)

# Make date index
df_counties.set_index("date", inplace=True)

# Save to .csv
df_counties.to_csv("clean_covid_data.csv")

