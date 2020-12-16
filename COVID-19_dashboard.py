import pandas as pd
pd.set_option('mode.chained_assignment', None)
import numpy as np

import panel as pn
pn.extension()

import bokeh.plotting
import bokeh.models
import bokeh.io

import colorcet

df_counties = pd.read_csv("clean_covid_data.csv", index_col="date", parse_dates=True)

county_state_list = list(np.array(pd.read_csv("county_state_list.csv")['0']))

autocomplete_counties = pn.widgets.AutocompleteInput(
    name='Counties:', 
    options=county_state_list, 
    case_sensitive=False,
    placeholder='Add county here',
    width=200,
)

counties_selector = pn.widgets.CheckBoxGroup(
    name="Counties:", 
    options=[], 
    value=[], 
    width=200,
)

county_strings_list = []

def add_county(event):
    if event.new:
        autocomplete_counties.value = None
        if event.new not in county_strings_list:
            county_strings_list.append(event.new)
            counties_selector.options = []
            counties_selector.options = county_strings_list
            counties_selector.value = counties_selector.options


autocomplete_county_watcher = autocomplete_counties.param.watch(
    add_county, "value", onlychanged=False
)

clear_button = pn.widgets.Button(name="clear", width=200)

def clear_county_list(event):
    counties_selector.options = []
    county_strings_list.clear()
    counties_selector.options = county_strings_list
    counties_selector.value = counties_selector.options
    
clear_button.on_click(clear_county_list)

measurement_selector = pn.widgets.Select(
    name="Plot:",
    options=[
        "total cases",
        "total deaths",
        "new cases",
        "new cases (7 day average)",
        "new deaths",
        "new deaths (7 day average)",
    ],
    value="total cases",
    width=200,
)

normalization_selector = pn.widgets.Select(
    name="Normalization:", options=["none", "per 100,000"], value="none", width=200,
)

timespan_selector = pn.widgets.Select(
    name="Timespan:", options=["all", "two weeks",], value="all", width=200,
)

def get_county_data(county, state):
    """
    Makes a Pandas Data Frame with data for a given county.
    Arguments:
    `county`: county name
    `state`: state name
    """
    if county not in df_counties["county"].values:
        raise RuntimeError(f"{county} is not a valid county name.")
    if state not in df_counties["state"].values:
        raise RuntimeError(f"{state} is not a valid state.")

    df = df_counties.loc[
        (df_counties["county"] == county) & (df_counties["state"] == state)
    ]
    if len(df) == 0:
        raise RuntimeError(f"{county} is not in {state}.")

    return df

def add_new_per_day(df):
    """
    Adds columns to Dataframe for new cases/deaths per day and 7 day average.
    Argument `df` is Pandas Dataframe output from `get_county_data()`.
    """
    # Add new cases
    cases_array = np.array(df["total cases"])
    new_cases_array = np.empty(np.shape(cases_array))
    new_cases_array[0] = cases_array[0]

    for i, n in enumerate(cases_array):
        if i > 0:
            new_cases_array[i] = cases_array[i] - cases_array[i - 1]

    df["new cases"] = new_cases_array

    # Calculate 7-day average for new cases per day
    df["new cases (7 day average)"] = df["new cases"].rolling(window=7).mean()

    # Add new deaths
    deaths_array = np.array(df["total deaths"])
    new_deaths_array = np.empty(np.shape(deaths_array))
    new_deaths_array[0] = deaths_array[0]

    for i, n in enumerate(deaths_array):
        if i > 0:
            new_deaths_array[i] = deaths_array[i] - deaths_array[i - 1]

    df["new deaths"] = new_deaths_array

    # Calculate 7-day average for new cases per day
    df["new deaths (7 day average)"] = df["new deaths"].rolling(window=7).mean()

    return df

yesterday = pd.to_datetime(pd.to_datetime("today").date()) - pd.DateOffset(days=1)
two_weeks_ago = yesterday - pd.DateOffset(days=13)

@pn.depends(
    counties_selector.param.value,
    measurement_selector.param.value,
    normalization_selector.param.value,
    timespan_selector.param.value,
)
def multi_covid_plots(counties, measurement, normalization, timespan):
    """
    Plots data for given counties.
    
    Depends on `get_county_data()`, `add_new_per_day()` functions.
    """

    colors = colorcet.b_glasbey_category10
    n = len(county_strings_list) // len(colors) + 1
    color_dict = dict(zip(county_strings_list, colors * n))
    color_dict["New York City, New York"] = "gray"

    if normalization == "per 100,000":
        p = bokeh.plotting.figure(
            frame_height=300,
            frame_width=600,
            x_axis_type="datetime",
            x_axis_label="date",
            y_axis_label=str(measurement) + " (per 100,000)",
        )
    else:
        p = bokeh.plotting.figure(
            frame_height=300,
            frame_width=600,
            x_axis_type="datetime",
            x_axis_label="date",
            y_axis_label=str(measurement),
        )
    
    legend_items = []
    
    for i, county_string in enumerate(counties):
        county = county_string[: county_string.find(",")]
        state = county_string[county_string.find(",") + 2 :]
        df = get_county_data(county, state)

        # Calculate new cases per day
        if "new" in measurement:
            df = add_new_per_day(df)

        # Get data for the specified date range
        if timespan == "two weeks":
            start = two_weeks_ago
            end = yesterday
        else:
            start = None
            end = yesterday
        df = df[start:end].reset_index()

        if normalization == "per 100,000":
            measurement_per = df[measurement] / df["population"] * 100000
            df["measurement_per"] = measurement_per
            line = p.line(
                source=df,
                x="date",
                y="measurement_per",
                line_width=2,
                color=color_dict[county_string],
            #    legend_label=f"{county}, {state}",
            )
            legend_items.append((f"{county}, {state}", [line]))
        else:
            line = p.line(
                source=df,
                x="date",
                y=measurement,
                line_width=2,
                color=color_dict[county_string],
            #    legend_label=f"{county}, {state}",
            )
            legend_items.append((f"{county}, {state}", [line]))

    p.yaxis[0].formatter = bokeh.models.formatters.BasicTickFormatter(
        use_scientific=False
    )

    #p.legend.location = "top_left"
    legend = bokeh.models.Legend(items=legend_items, location="center")
    p.add_layout(legend, 'right')
    p.legend.click_policy = "hide"

    tooltips = bokeh.models.HoverTool(
        tooltips=[("date", "@date{%F}"),],
        formatters={"@date": "datetime"},
        mode="vline",
    )
    p.add_tools(tooltips)

    return p

title = pn.pane.Markdown(
    """
    #COVID-19 Dashboard
    Data from [The New York Times](https://www.nytimes.com/interactive/2020/us/coronavirus-us-cases.html), based on reports from state and local health agencies.
    """
)

# Horizontal layout
# add_county_widget = pn.Column(
#     pn.Spacer(height=15),
#     autocomplete_counties,
#     pn.Spacer(height=15),
#     counties_selector,
#     pn.Spacer(sizing_mode='stretch_both'),
#     clear_button
# )

# Vertical layout
add_county_widget = pn.Column(
    pn.Spacer(height=15),
    autocomplete_counties,
    clear_button,
    counties_selector,
)

plot = pn.Column(
    pn.Spacer(height=15),
    pn.panel(multi_covid_plots),
)
    
widgets = pn.Column(
    pn.Spacer(height=15),
    measurement_selector,
    #pn.Spacer(height=15),
    normalization_selector,
    #pn.Spacer(height=15),
    timespan_selector,
)

# Horizontal layout
# pn.Column(
#     title,
#     pn.Row(
#         add_county_widget,
#         widgets,
#         plot
#     )
# ).servable()

# Vertical layout
pn.Column(
    pn.Row(
        pn.Spacer(width=200),
        add_county_widget,
        widgets,
        pn.Spacer(width=200)
    ),
    pn.Row(
        pn.Spacer(sizing_mode='stretch_both'),
        plot,
        pn.Spacer(sizing_mode='stretch_both'),
    )
).servable()