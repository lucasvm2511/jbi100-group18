import dash
import dash_core_components as dcc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

df = px.data.election()
geojson = px.data.election_geojson()
candidates = df.winner.unique()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Candidate:"),
    dcc.RadioItems(
        id='candidate',
        options=[{'value': x, 'label': x}
                 for x in candidates],
        value=candidates[0],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id="choropleth"),
])

@app.callback(
    Output("choropleth", "figure"),
    [Input("candidate", "value")])
def display_choropleth(candidate):
    fig = px.choropleth(
        df, geojson=geojson, color=candidate,
        locations="district", featureidkey="properties.district",
        projection="mercator", range_color=[0, 6500])
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig

app.run_server(debug=True)