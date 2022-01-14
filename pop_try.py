import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import json

road_df = pd.read_csv('dataset.csv')
pop_df = pd.read_csv('population_districts.csv')

names_df = pd.read_csv('names.csv')
names_df.set_index('district_id', inplace=True)
population_df = pd.read_csv('population_districts.csv')
population_df.set_index('district',inplace=True)

# Manipulate dataframe to get the data needed
my_map = names_df.to_dict()
my_map_population = population_df.to_dict()
road_df['Local_Authority_(District)'].replace(my_map['district_name'],
                                              inplace=True)  # replace district id with district name
road_df['Population']=road_df['Local_Authority_(District)']
road_df['Population'].replace(my_map_population['population'],
                                              inplace=True)  # replace district name with district population

print(road_df.district.unique())

