# Import libraries needed
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import json

# Make dash object
app = dash.Dash(__name__)

# --------------------------------------------------------------------
# Load dataframe of accidents
road_df = pd.read_csv('dataset.csv')
names_df = pd.read_csv('names.csv')
names_df.set_index('district_id', inplace=True)
population_df = pd.read_csv('population_districts.csv')
population_df.set_index('district',inplace=True)

# Manipulate dataframe to get the data needed
population_df['population'] = population_df['population'].str.replace(',', '')
population_df['population'] = population_df['population'].astype(int)
my_map = names_df.to_dict()
my_map_population = population_df.to_dict()
road_df['Local_Authority_(District)'].replace(my_map['district_name'],
                                              inplace=True)  # replace district id with district name
road_df['Population'] = road_df['Local_Authority_(District)']
road_df['Population'].replace(my_map_population['population'],
                                              inplace=True)  # replace district name with district population
road_df['relative_pop'] = (road_df['Population'] / 64812699) * 100
# Read in geojson
hucs = gpd.read_file('geojson4.json')

# Load dataframe of GB; Populate hucs['properties'] (i.e. convert to plotly-readible geojson-type)
hucs = json.loads(hucs.to_json())
from geojson_rewind import rewind

hucs_rewound = rewind(hucs, rfc7946=False)
severity = road_df.Casualty_Severity.unique()
Weather_Conditions = road_df.Weather_Conditions.unique()
junction_control = road_df.Junction_Control.unique()
print(junction_control)
# ----------------------------------------------------------------------
# App layout: Describes what the application look like; aka dash components (without data)

app.layout = html.Div([
    # Give title to website
    html.H1("Mapping of accidents in Great Britain", style={'text-align': 'center'}),
    html.Div([html.H3('Filtering'), html.P("Pick severity:"),
              dcc.Dropdown(id="Casualty_Severity",
                           options=[{'label': 'All', 'value': 'All'},
                                    {'label': 'Slight', 'value': severity[0]},
                                    {'label': 'Serious', 'value': severity[1]},
                                    {'label': 'Fatal', 'value': severity[2]}],
                           multi=False,
                           value='All',
                           style={}
                           ),
              html.P("Pick weather conditions:"),
              dcc.Dropdown(id="weather_conditions",
                           options=[{'label': 'All', 'value': 'All'},
                                    {'label': 'Fine no high winds', 'value': 1},
                                    {'label': 'Raining no high winds', 'value': 2},
                                    {'label': 'Snowing no high winds', 'value': 3},
                                    {'label': 'Fine + high winds', 'value': 4},
                                    {'label': 'Raining + high winds', 'value': 5},
                                    {'label': 'Snowing + high winds', 'value': 6}],
                           multi=False,
                           value='All',
                           style={}
                           ),
              html.P("Pick junction control:"),
              dcc.Dropdown(id="junction_control",
                           options=[{'label': 'All', 'value': 'All'},
                                    #{'label': 'Not a junction or within 20 meters', 'value': junction_control[0]},
                                    {'label': 'Authorised person', 'value': junction_control[1]},
                                    {'label': 'Auto traffic signal', 'value': junction_control[2]},
                                    {'label': 'Stop sign', 'value': junction_control[3]},
                                    {'label': 'Give way or uncontrolled', 'value': junction_control[4]}],
                                    #{'label': 'Unknown', 'value': junction_control[9]}],
                           multi=False,
                           value='All',
                           style={}
                           ),
              dcc.Graph(id='age_hist', figure={}),
              dcc.Graph(id='district_graph', figure={})], style={'width': '30%', 'display': 'inline-block'}),
    html.Div(children=[
        dcc.Graph(id="choropleth", figure={}, config={'scrollZoom': False}),
        html.Div(id='output_container', children=[]),
        html.Div(id='output_container2', children=[]),
        html.Div(id='output_container3', children=[])],
        style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'top'})], style={'font-family': 'verdana'})

# -----------------------------------------------------------------------------
# Callback; Connect the plotly graphs with dash components; inserts data in the dash components
@app.callback(
    [Output(component_id="output_container", component_property="children"),
     Output(component_id="choropleth", component_property="figure"), ],
    [Input(component_id="Casualty_Severity", component_property="value"),
     Input(component_id="weather_conditions", component_property="value"),
     Input(component_id="junction_control", component_property="value")]
)
# Argument in function refers to component_property in the Input(), here 3 arguments so three inputs in callback
def update_choropleth(option_selected, option_selected2, option_selected3):
    if option_selected == 'All':
        filtered_df_casualty = road_df  # if all is selected, do not filter
    else:
        filtered_df_casualty = road_df[(road_df['Casualty_Severity'] == option_selected)]

    if option_selected2 == 'All':
        filtered_df_weather = filtered_df_casualty  # if all is selected, do not filter
    else:
        filtered_df_weather = filtered_df_casualty[filtered_df_casualty['Weather_Conditions'] == option_selected2]
    filtered_df_weather['Accidents_amount'] = filtered_df_weather['Accident_Index']

    if option_selected3 == 'All':
        filtered_df_junction = road_df  # if all is selected, do not filter
    else:
        filtered_df_junction = road_df[road_df['Junction_Control'] == option_selected3]
    filtered_df_junction['Accidents_amount'] = filtered_df_junction['Accident_Index']

    filtered_group_df = filtered_df_junction.groupby('Local_Authority_(District)').count()[
        'Accidents_amount'].to_frame().reset_index()

    fig = px.choropleth(data_frame=filtered_group_df,
                        geojson=hucs_rewound, color="Accidents_amount",
                        locations="Local_Authority_(District)", featureidkey="properties.NAME_3",
                        projection="mercator", range_color=[0, filtered_group_df['Accidents_amount'].max()],
                        color_continuous_scale=px.colors.sequential.Reds, height=650)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    text = 'The level of severity chosen was: {}, weather condition {} and junction control {}.'.format(option_selected,
                                                                                                        option_selected2,
                                                                                                        option_selected3)
    # What you return: is going into the Output, vb: here 1 output so 1 argument return
    return text, fig

@app.callback(
    [Output(component_id="output_container2", component_property="children"),
     Output(component_id="district_graph", component_property="figure"),
     Output(component_id="age_hist", component_property="figure")],
    [Input(component_id='choropleth', component_property='clickData'),
     Input(component_id='Casualty_Severity', component_property="value"),
     Input(component_id="weather_conditions", component_property="value"),
     Input(component_id="junction_control", component_property="value")
     ])
# One argument in def() so 1 input in callback
def select_district_and_update_age_speedlimit(clickData, option_selected, option_selected2, option_selected3):
    fig = {}
    district = None
    if clickData is not None:
        district = clickData['points'][0]['location']
        df_selected_district = road_df[road_df['Local_Authority_(District)'] == district]
        df_selected_district['selected_district_bool'] = district
        df_not_selected_district = road_df[road_df['Local_Authority_(District)'] != district]
        df_not_selected_district['selected_district_bool'] = 'Average other district'

        df_both = pd.concat([df_selected_district, df_not_selected_district])

        df_selected_district_gr = df_both.groupby(['selected_district_bool', 'Speed_limit']).count()[
            ['Accident_Index']].reset_index()
        df_selected_district_gr.loc[df_selected_district_gr['selected_district_bool'] != district, 'Accident_Index'] = \
        df_selected_district_gr.loc[df_selected_district_gr['selected_district_bool'] != district, 'Accident_Index'] / (
                    309 - 1)

        fig = px.bar(df_selected_district_gr, x='Speed_limit', y='Accident_Index', color='selected_district_bool',
                     barmode="group", title=str('Amount of accidents per speed limit in ' + district))
        age_hist = px.histogram(df_selected_district, x='Age_of_Driver',
                                category_orders={"Age_of_Driver": [*range(100), '?']},
                                title=str('Driver age histogram in ' + district))
    else:
        # If no district is clicked
        df_gb = road_df.groupby(['Speed_limit', 'Casualty_Severity', 'Weather_Conditions', 'Junction_Control']).count()[['Accident_Index']].reset_index()
        # Include dropdown interaction for bar speed limit
        if option_selected == 'All':
            filtered_df_casualty = df_gb  # if all is selected, do not filter
        else:
            filtered_df_casualty = df_gb[(df_gb['Casualty_Severity'] == option_selected)]
        if option_selected2 == 'All':
            filtered_df_weather = filtered_df_casualty  # if all is selected, do not filter
        else:
            filtered_df_weather = filtered_df_casualty[filtered_df_casualty['Weather_Conditions'] == option_selected2]
        filtered_df_weather['Accidents_amount'] = filtered_df_weather['Accident_Index']

        if option_selected3 == 'All':
            filtered_df_junction = df_gb  # if all is selected, do not filter
        else:
            filtered_df_junction = df_gb[df_gb['Junction_Control'] == option_selected3]
        filtered_df_junction['Accidents_amount'] = filtered_df_junction['Accident_Index']

        filtered_group_df = filtered_df_junction
        fig = px.bar(filtered_group_df, x='Speed_limit', y='Accident_Index', title=str('Amount of accidents per speed limit in Great Britain'))

    # # Include dropdown interaction for age graph
    #     if option_selected == 'All':
    #         filtered_df_casualty = road_df  # if all is selected, do not filter
    #     else:
    #         filtered_df_casualty = road_df[(road_df['Casualty_Severity'] == option_selected)]
    #     if option_selected2 == 'All':
    #         filtered_df_weather = filtered_df_casualty  # if all is selected, do not filter
    #     else:
    #         filtered_df_weather = filtered_df_casualty[filtered_df_casualty['Weather_Conditions'] == option_selected2]
    #     filtered_df_weather['Accidents_amount'] = filtered_df_weather['Accident_Index']
    #     if option_selected3 == 'All':
    #         filtered_df_junction = road_df  # if all is selected, do not filter
    #     else:
    #         filtered_df_junction = road_df[road_df['Junction_Control'] == option_selected3]
    #     filtered_df_junction['Accidents_amount'] = filtered_df_junction['Accident_Index']
    #
    #     filtered_group_df = filtered_df_junction
        age_hist = px.histogram(filtered_group_df, x='Age_of_Driver',
                                category_orders={"Age_of_Driver": [*range(100), '?']},
                                title=str('Driver age histogram in Great Britain'))
    return district, fig, age_hist

app.run_server(debug=True)
# test


