from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


# Data
DATA_DIR = Path("data/")

albums = pd.read_json(DATA_DIR / "albums_features.json")
artists = pd.read_json(DATA_DIR / "artists_features.json")

albums["name"] = albums["name"].astype(str)
albums["release_date"] = pd.to_datetime(albums.release_date)
albums["year"] = albums.release_date.dt.year
albums["decade"] = albums.year.astype(str).str[:3] + "0"
albums["loudness"] = albums.loudness.clip(
    albums.loudness.quantile(0.05), albums.loudness.quantile(0.95)
)

decades = sorted(albums.decade.unique())
columns = sorted(
    [
        "popularity",
        "release_date",
        "total_tracks",
        "duration_ms",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "time_signature",
        "year",
    ]
)


# Dash
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[
        html.H2(children="Spotify user library explorer"),
        html.Div(
            children="""
        Select artists and album release decade to filter albums.
        Albums view is zoomable, and axes are customizable.
    """
        ),
        dcc.Graph(
            id="artists-points",
            figure={
                "data": [
                    go.Scatter(
                        x=group.genre_x,
                        y=group.genre_y,
                        mode="markers",
                        name=name,
                        hovertext=group.name,
                        marker=dict(size=albums["popularity"] / 5),
                    )
                    for name, group in artists.groupby("genre_cluster")
                ],
                "layout": go.Layout(
                    title="Artists",
                    hovermode="closest",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                ),
            },
        ),
        html.Div(
            [
                html.Div("Axes:"),
                dcc.Dropdown(
                    id="xaxis-column",
                    options=[{"label": i, "value": i} for i in columns],
                    value="release_date",
                ),
                dcc.Dropdown(
                    id="yaxis-column",
                    options=[{"label": i, "value": i} for i in columns],
                    value="popularity",
                ),
                dcc.Dropdown(
                    id="color-column",
                    options=[{"label": i, "value": i} for i in columns],
                    value="loudness",
                ),
                html.Div("Decades:"),
                dcc.RangeSlider(
                    id="decades-slider",
                    marks={i: dec for i, dec in enumerate(decades)},
                    min=0,
                    max=len(decades) - 1,
                    value=[0, len(decades) - 1],
                ),
            ],
            style={"width": "29%", "float": "left"},
        ),
        html.Div(
            dcc.Graph(id="albums-points"), style={"width": "69%", "float": "right"}
        ),
    ]
)


@app.callback(
    dash.dependencies.Output("albums-points", "figure"),
    [
        dash.dependencies.Input("xaxis-column", "value"),
        dash.dependencies.Input("yaxis-column", "value"),
        dash.dependencies.Input("color-column", "value"),
        dash.dependencies.Input("decades-slider", "value"),
    ],
)
def update_albums_points(
    xaxis_column_name, yaxis_column_name, color_column_name, decades_idx
):
    selected_decades = decades[decades_idx[0]:decades_idx[1]]
    df = albums[albums.decade.isin(selected_decades)]
    return {
        "data": [
            go.Scatter(
                x=df[xaxis_column_name],
                y=df[yaxis_column_name],
                mode="markers",
                marker=dict(
                    color=df[color_column_name],
                    colorscale="Viridis",
                    showscale=True,
                ),
                hovertext=df.name,
            )
        ],
        "layout": go.Layout(
            title="Albums",
            hovermode="closest",
            xaxis=dict(zeroline=False, title=xaxis_column_name),
            yaxis=dict(zeroline=False, title=yaxis_column_name),
        ),
    }


if __name__ == "__main__":
    app.run_server()
