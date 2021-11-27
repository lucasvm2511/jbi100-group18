from jbi100_app.main import app
from jbi100_app.views.menu import make_menu_layout
from jbi100_app.views.scatterplot import Scatterplot
from jbi100_app.views.bar_chart import Bar_chart
import pandas as pd

from dash import html, dcc
import plotly.express as px
from dash.dependencies import Input, Output


if __name__ == '__main__':
    # Create data
    df = px.data.iris()
    df2 = pd.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })
    # Instantiate custom views
    scatterplot1 = Scatterplot("Scatterplot 1", 'sepal_length', 'sepal_width', df)
    scatterplot2 = Scatterplot("Scatterplot 2", 'petal_length', 'petal_width', df)
    #fig = px.bar(df2, x="Fruit", y="Amount", color="City", barmode="group")
    bar1= Bar_chart("Bar chart", 'petal_length', 'petal_width', df)

    app.layout = html.Div(
        id="app-container",
        children=[
            # Left column
            html.Div(
                id="left-column",
                className="three columns",
                children=make_menu_layout()
            ),

            # Right column
            html.Div(
                id="right-column",
                className="nine columns",
                children=[
                    scatterplot1,
                    scatterplot2,
                    bar1
                ],
            ),
        ],
    )

    # Define interactions
    @app.callback(
        Output(scatterplot1.html_id, "figure"), [
        Input("select-color-scatter-1", "value"),
        Input(scatterplot2.html_id, 'selectedData')
    ])
    def update_scatter_1(selected_color, selected_data):
        return scatterplot1.update(selected_color, selected_data)

    @app.callback(
        Output(scatterplot2.html_id, "figure"), [
        Input("select-color-scatter-2", "value"),
        Input(scatterplot1.html_id, 'selectedData')
    ])
    def update_scatter_2(selected_color, selected_data):
        return scatterplot2.update(selected_color, selected_data)

    @app.callback(
        Output(bar1.html_id, "figure"), [
        Input("select-color-bar3", "value"),
        Input(scatterplot2.html_id, 'selectedData')
    ])
    def update_bar3(selected_color, selected_data):
        return bar1.update(selected_color, selected_data)


    app.run_server(debug=False, dev_tools_ui=False)