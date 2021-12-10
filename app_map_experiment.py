import dash
import dash_core_components as dcc
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

df = px.data.election()
road_df = pd.read_csv('dataset.csv')
names_df = pd.read_csv('names.csv')
names_df.set_index('district_id', inplace=True)
my_map = names_df.to_dict()
my_map['district_name']
road_group = road_df.groupby('Local_Authority_(District)').sum()['1st_Road_Number'].to_frame()
road_group['district_name']=road_group.index.to_frame().replace(my_map['district_name'])['Local_Authority_(District)']

geojson = px.data.election_geojson()

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/administrative/gb/topo_lad.json') as response:
    geojson2 = json.load(response)

fig = px.choropleth(
    road_group, geojson=geojson2, color="1st_Road_Number",
    locations="district_name", featureidkey="LAD13NM",
    projection="mercator", range_color=[0, 6500])
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

app = dash.Dash(__name__)

app.layout = html.Div([

    dcc.Graph(fig.show()),
])




app.run_server(debug=True)