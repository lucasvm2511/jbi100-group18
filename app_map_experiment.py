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

# Load dataframe of accidents
road_df = pd.read_csv('dataset.csv')
names_df = pd.read_csv('names.csv')
names_df.set_index('district_id', inplace=True)

# Manipulate dataframe to get the data needed
my_map = names_df.to_dict()
my_map['district_name']
road_group = road_df.groupby('Local_Authority_(District)').count()['Accident_Index'].to_frame()
road_group['district_name'] = road_group.index.to_frame().replace(my_map['district_name'])['Local_Authority_(District)']
#print(road_group.head())

# Read in geojson
hucs = gpd.read_file('geojson4.json')

# Load dataframe of GB; Populate hucs['properties'] (i.e. convert to plotly-readible geojson-type)
hucs = json.loads(hucs.to_json())
from geojson_rewind import rewind
hucs_rewound = rewind(hucs, rfc7946=False)
severity = road_df.Casualty_Severity.unique()

# Make dash object
app = dash.Dash(__name__)

# Describes what the application look like; aka dash components (without data)
app.layout = html.Div([
    # Give title to website
    html.H1("Mapping of accidents in Great Britain", style={'text-align': 'center'}),
    # Make a checklist for severity; Create interactive menu Severity
    html.P("Severity:"),
    dcc.Dropdown(id="Casualty_Severity",
        options=[{'label': 'Slight', 'value': severity[0]},
                 {'label': 'Serious', 'value': severity[1]},
                {'label': 'Fatal', 'value': severity[2]}],
        multi=False,
        value=severity[0],
        style={'width': '40%'}
    ),
    html.Div(id='output_container', children=[]),

    dcc.Graph(id="choropleth", figure={}),
])

# Callback; inserts data in the dash components
@app.callback(
    [Output(component_id="output_container", component_property="children"),
     Output(component_id="choropleth", component_property="figure")],
    [Input(component_id="Casualty_Severity", component_property="value")]
)

# argument in function refers to component_property in the Input()
def update_graph(option_selected):

    container = 'The level of severity chosen was: {}'.format(option_selected)

    dff = road_group.copy()
    dff['Casualty_Severity'] = road_df['Casualty_Severity']
    dff = dff[dff["Casualty_Severity"] == option_selected]

    fig = px.choropleth(data_frame=dff,
        geojson=hucs_rewound, color="Accident_Index",
        locations="district_name", featureidkey="properties.NAME_3",
        projection="mercator", range_color=[0, 2000], color_continuous_scale=px.colors.sequential.Reds)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # What you return: is going into the Output, vb: here 1 output so 1 argument return
    return container, fig

app.run_server(debug=True)