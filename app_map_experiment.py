# Import libraries needed
import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import json
from collections import defaultdict

# Make dash object
app = dash.Dash(__name__)
# --------------------------------------------------------------------
# Load dataframe of accidents
px.set_mapbox_access_token(
    'pk.eyJ1IjoibHVjYXN2bSIsImEiOiJja3lsYmg4aTMwNHY5Mm9wYmxrMGNmeTdmIn0.zPxtZHL_qWWh13-Np-zmog')  # set mapbox token
road_df = pd.read_csv('dataset.csv')
road_df.drop(inplace=True, columns=['Location_Easting_OSGR', 'Location_Northing_OSGR', 'Police_Force',
                                    'Number_of_Vehicles', 'Number_of_Casualties', 'Local_Authority_(Highway)',
                                    '1st_Road_Class', '1st_Road_Number', 'Road_Type',
                                    'Junction_Detail', '2nd_Road_Class',
                                    '2nd_Road_Number', 'Pedestrian_Crossing-Human_Control',
                                    'Pedestrian_Crossing-Physical_Facilities', 'Light_Conditions',
                                    'Road_Surface_Conditions',
                                    'Special_Conditions_at_Site', 'Carriageway_Hazards',
                                    'Urban_or_Rural_Area', 'Did_Police_Officer_Attend_Scene_of_Accident',
                                    'LSOA_of_Accident_Location', 'Vehicle_Reference_df_res',
                                    'Casualty_Reference', 'Casualty_Class', 'Sex_of_Casualty',
                                    'Age_of_Casualty', 'Age_Band_of_Casualty',
                                    'Pedestrian_Location', 'Pedestrian_Movement', 'Car_Passenger',
                                    'Bus_or_Coach_Passenger', 'Pedestrian_Road_Maintenance_Worker',
                                    'Casualty_Type', 'Casualty_Home_Area_Type', 'Casualty_IMD_Decile',
                                    'Vehicle_Reference_df', 'Vehicle_Type', 'Towing_and_Articulation',
                                    'Vehicle_Manoeuvre', 'Vehicle_Location-Restricted_Lane',
                                    'Junction_Location', 'Skidding_and_Overturning',
                                    'Hit_Object_in_Carriageway', 'Vehicle_Leaving_Carriageway',
                                    'Hit_Object_off_Carriageway', '1st_Point_of_Impact',
                                    'Was_Vehicle_Left_Hand_Drive?', 'Journey_Purpose_of_Driver', 'Age_Band_of_Driver',
                                    'Engine_Capacity_(CC)', 'Propulsion_Code', 'Age_of_Vehicle',
                                    'Driver_Home_Area_Type'])
names_df = pd.read_csv('names.csv')
names_df.set_index('district_id', inplace=True)
population_df = pd.read_csv('population_districts.csv')
population_df.set_index('district', inplace=True)
# Manipulate dataframe to get the data needed
my_map = names_df.to_dict()
my_map_population = population_df.to_dict()
road_df['Local_Authority_(District)'].replace(my_map['district_name'],
                                              inplace=True)  # replace district id with district name
road_df['Population'] = road_df['Local_Authority_(District)']
road_df['Population'].replace(my_map_population['population'],
                              inplace=True)  # replace district name with district population
road_df['Time2'] = road_df.Time[road_df.Time != "?"]
road_df['Time2'] = pd.to_datetime(road_df.Time2, format='%H:%M')
filtered_road_df = road_df
# Read in geojson
hucs = gpd.read_file('geojson4.json')
# Load dataframe of GB; Populate hucs['properties'] (i.e. convert to plotly-readible geojson-type)
hucs = json.loads(hucs.to_json())
from geojson_rewind import rewind

hucs_rewound = rewind(hucs, rfc7946=False)
severity = road_df.Casualty_Severity.unique()
Weather_Conditions = road_df.Weather_Conditions.unique()
junction_control = road_df.Junction_Control.unique()

print(population_df.head(5))
print(population_df.loc['Northumberland'])
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
                                    {'label': 'Authorised person', 'value': junction_control[1]},
                                    {'label': 'Auto traffic signal', 'value': junction_control[2]},
                                    {'label': 'Stop sign', 'value': junction_control[3]},
                                    {'label': 'Give way or uncontrolled', 'value': junction_control[4]}],
                           multi=False,
                           value='All',
                           style={}
                           ),
              dcc.Graph(id='age_hist', figure={}),
              dcc.Graph(id='district_graph', figure={})], style={'width': '30%', 'display': 'inline-block'}),
    html.Div(children=[
        html.Button('Show density heatmap', id='btn_2', n_clicks=0),
        html.Button('Show district heatmap', id='btn_1', n_clicks=0),
        html.Button('Change colors', id='btn_3', n_clicks=0),
        html.Button('Change to absolute/relative amount', id='btn_4', n_clicks=0),
        dcc.Graph(id="fig_map", figure={}, config={'scrollZoom': False,}),
        dcc.Graph(id='time_hist'),
        html.Div(id='output_container', children=[]),
        html.Div(id='output_container2', children=[]),
        html.Div(id='output_container3', children=[])],
        style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'top'})], style={'font-family': 'verdana'})


# Make a checklist for weather; Create interactive menu Severity
# -----------------------------------------------------------------------------
# Callback; Connect the plotly graphs with dash components; inserts data in the dash components
@app.callback(
    [Output(component_id="output_container", component_property="children"),
     Output(component_id="fig_map", component_property="figure"), ],
    [Input(component_id="Casualty_Severity", component_property="value"),
     Input(component_id="weather_conditions", component_property="value"),
     Input(component_id="junction_control", component_property="value"),
     Input(component_id="btn_1", component_property='n_clicks'),
     Input(component_id="btn_2", component_property='n_clicks'),
     Input(component_id="btn_3", component_property='n_clicks'),
     Input(component_id="btn_4", component_property='n_clicks')]
)
# Argument in function refers to component_property in the Input(), here 3 arguments so three inputs in callback
def update_graph(option_selected, option_selected2, option_selected3, n_clicks_b1, n_clicks_b2, n_clicks_b3,
                 n_clicks_b4):
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
        filtered_df_junction = filtered_df_weather  # if all is selected, do not filter
    else:
        filtered_df_junction = filtered_df_weather[filtered_df_weather['Junction_Control'] == option_selected3]
    filtered_df_junction['Accidents_amount'] = filtered_df_junction['Accident_Index']
    global filtered_road_df #make the filtered dataframe available to the other callback
    filtered_road_df = filtered_df_junction
    filtered_group_df = filtered_df_junction.groupby('Local_Authority_(District)').count()[
        'Accidents_amount'].to_frame().reset_index()
    merged = pd.merge(left=filtered_group_df, right=population_df, left_on='Local_Authority_(District)',
                      right_on='district')
    merged['per10000'] = merged['Accidents_amount'] * 10000 / merged['population']
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    colorscale_list = [px.colors.sequential.tempo, px.colors.sequential.Reds, px.colors.sequential.matter,
                       px.colors.sequential.Cividis]

    global button1
    global button2
    global filterchange
    global absrelchange
    global amount_column
    if 'Casualty_Severity' in changed_id or 'weather_conditions' in changed_id or 'junction_control' in changed_id:
        filterchange = True
    else:
        filterchange = False
    if 'btn_1' in changed_id or (n_clicks_b1 == 0 and n_clicks_b2 == 0):
        button1 = True
        button2 = False
    elif 'btn_2' in changed_id:
        button1 = False
        button2 = True
    if ('btn_4' in changed_id and (n_clicks_b4 % 2 == 0)) or (n_clicks_b4 == 0):
        amount_column = 'Accidents_amount'
        absrelchange = True
    elif 'btn_4' in changed_id and (n_clicks_b4 % 2 == 1):
        amount_column = 'per10000'
        absrelchange = True
    else:
        absrelchange = False
    if (button1 or (button1 and (filterchange or absrelchange)) or (n_clicks_b1 == 0 and n_clicks_b2 == 0)):
        fig_map = px.choropleth(data_frame=merged,  # choropleth map
                                geojson=hucs_rewound, color=amount_column,
                                locations="Local_Authority_(District)", featureidkey="properties.NAME_3",
                                projection="mercator", range_color=[0, merged[amount_column].max()],
                                hover_name='Local_Authority_(District)',hover_data={'Accidents_amount':True, 'per10000':True, 'population':True, 'Local_Authority_(District)':False},
                                labels={'Accidents_amount':'Number of accidents','per10000':'Number of accidents per 10000', 'population':'Population'},
                                color_continuous_scale=colorscale_list[n_clicks_b3 % 4], height=500)
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, coloraxis_colorbar=dict(
            title="Number of accidents",
            len=0.5))  # , title=dict(text="A Figure Specified By A Graph Object"), title_font_size= 30)
    if button2 or (button2 and (filterchange or absrelchange)):
        fig_map = px.density_mapbox(filtered_df_junction, lat='Latitude', lon='Longitude', radius=3,  # density map
                                    center=dict(lat=51.5085300, lon=-0.1257400), zoom=7,
                                    mapbox_style='mapbox://styles/lucasvm/ckypzzw6kq7i815pcy5ig2slk',
                                    color_continuous_scale=colorscale_list[n_clicks_b3 % 4])

    text = 'The level of severity chosen was: {}, weather condition {} and junction control {}.'.format(option_selected,
                                                                                                        option_selected2,
                                                                                                        option_selected3)
    # What you return: is going into the Output, vb: here 1 output so 1 argument return
    return text, fig_map


@app.callback(
    [Output(component_id="output_container2", component_property="children"),
     Output(component_id="district_graph", component_property="figure"),
     Output(component_id="age_hist", component_property="figure"),
     Output(component_id="time_hist", component_property='figure')],
    [Input('fig_map', 'clickData'),
     Input(component_id="fig_map", component_property="figure")])
def select_district(clickData, a):
    district = None
    if clickData is not None: #if a location is clicked on the map

        district = clickData['points'][0]['location']
        d = defaultdict(lambda: '0')  # give not selected district value zero
        d[district] = '1'  # give selected district value one
        road_df['selected_district_bool'] = road_df['Local_Authority_(District)'].map(d)
        new = road_df.groupby(['selected_district_bool', 'Speed_limit']).count()[['Accident_Index']].reset_index()
        new.loc[new['selected_district_bool'] == '0', 'Accident_Index'] = new.loc[new['selected_district_bool'] == '0', 'Accident_Index'] / (6722-(population_df.loc[district,'population']/10000))
        new.loc[new['selected_district_bool'] == '1', 'Accident_Index'] = new.loc[new['selected_district_bool'] == '1', 'Accident_Index'] / (population_df.loc[district,'population']/10000)
        fig = px.bar(new, x='Speed_limit', y='Accident_Index', color='selected_district_bool',
                     barmode="group", title=str('Amount of accidents per speed limit in ' + district))
        age_hist = px.histogram(road_df, x='Age_of_Driver',color='selected_district_bool',
                                category_orders={"Age_of_Driver": [*range(100), '?']},
                                title=str('Driver age histogram in ' + district), histnorm='probability', barmode='overlay')
        time_hist = px.histogram(road_df, x="Time2", nbins=24, color='selected_district_bool', histnorm='probability', barmode='overlay', title=str('Accident time in ' + district))
        time_hist.update_layout(xaxis_title="Time of the day (hour)")
    else:
        df_gb = filtered_road_df.groupby(['Speed_limit']).count()[['Accident_Index']].reset_index()
        fig = px.bar(df_gb, x='Speed_limit', y='Accident_Index',
                     title=str('Amount of accidents per speed limit in Great Britain'))
        age_hist = px.histogram(filtered_road_df, x='Age_of_Driver',
                                category_orders={"Age_of_Driver": [*range(100), '?']},
                                title=str('Driver age histogram in Great Britain'))

        time_hist = px.histogram(filtered_road_df, x="Time2", nbins=24, color='Sex_of_Driver',title=str('Accident time in Great Britain Per sex'))
        time_hist.update_layout(xaxis_title="Time of the day (hour)", barmode='overlay')
    return district, fig, age_hist, time_hist


app.run_server(debug=True)
