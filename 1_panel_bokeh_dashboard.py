# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Dashboard with Panel, Holoviews and Bokeh for Spotify datasets
#
# Some documentation pages that helped me:
# - http://holoviews.org/user_guide/Plotting_with_Bokeh.html
# - https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html#custom-tooltip
# - https://github.com/pyviz-demos/glaciers

# %load_ext watermark
# %watermark -v -n -u -p numpy,pandas,bokeh,holoviews
# %reload_ext autoreload
# %autoreload 1

# +
from pathlib import Path

import holoviews as hv
import pandas as pd
import panel as pn
from bokeh.models import HoverTool
hv.extension("bokeh")
# -

# ## Get and preprocess datasets
#
# - Converting some column types.
# - Clipping some columns to avoid irrelevant outliers.
# - Creating columns for direct plotting.

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


# ## Build the main visualizations

def create_artists_points(data):
    artists_tooltips = """
        <div>
            <div>
                <img
                    src="@image" height="70" alt="@image" width="70"
                    style="float: left; margin: 0px 15px 15px 0px;"
                    border="1"
                ></img>
            </div>
            <div>
                <span style="font-size: 15px;"><b>@name</b></span>
            </div>
            <div>
                <span style="font-weight: bold;">Main genre:</span>
                <span>@genre_cluster</span>
            </div>
            <div>
                <span style="font-weight: bold;">Subgenre:</span>
                <span>@genre_specific</span>
            </div>
        </div>
    """
    artists_hover = HoverTool(tooltips=artists_tooltips)
    artists_points = hv.Points(
        data=data, kdims=["genre_x", "genre_y"],
        vdims=["genre_cluster", "genre_specific", "popularity", "image", "name"]
    )
    artists_points.opts(
        tools=["box_select", "lasso_select", artists_hover, "tap"],
        color="genre_cluster", cmap="dark2",
        line_color="black", size=hv.dim("popularity")/5,
        padding=0.1, width=800, height=600, show_grid=False, show_frame=False,
        xaxis="bare", yaxis="bare", title="Artists"
    )
    return artists_points

def create_albums_points(data=None, x=None, y=None, color=None):
    if data is None:
        data = albums
    x = x or x_select.value
    y = y or y_select.value
    color = color or color_select.value

    albums_tooltips = """
        <div>
            <div>
                <img
                    src="@image" height="70" alt="@image" width="70"
                    style="float: left; margin: 0px 15px 15px 0px;"
                    border="2"
                ></img>
            </div>
            <div>
                <span>@artist_name</span>
            </div>
            <div>
                <span>@name</span>
            </div>
            <div>
                <span>@year</span>
            </div>
        </div>
    """
    albums_hover = HoverTool(tooltips=albums_tooltips)
    albums_points = hv.Points(
        data, [x, y],
        ["name", "artist_name", "image", "year", color]
    )
    albums_points.opts(
        tools=[albums_hover], color=color, cmap="viridis",
        line_color="black", size=10, colorbar=True,
        padding=0.1, width=800, height=600, title="Albums"
    )
    return albums_points

# ### Widgets

# +
genres = list(artists.genre_cluster.value_counts().index)
decades = sorted(albums.decade.unique(), reverse=True)
columns = sorted([
    "popularity", "release_date", "total_tracks", "duration_ms", "danceability", "energy",
    "key", "loudness", "mode", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo", "time_signature", "year"
])
decade_select = pn.widgets.CheckBoxGroup(
    name="decades", value=decades, options=decades,
    inline=False
)
x_select = pn.widgets.Select(value="valence", options=columns, name="x")
y_select = pn.widgets.Select(value="popularity", options=columns, name="y")
color_select = pn.widgets.Select(value="loudness", options=columns, name="color")

decade_box = pn.WidgetBox("# Decade", decade_select)
axes_box = pn.WidgetBox("# Axes", x_select, y_select, color_select)
# -

# ### HTML

title = "<div style='font-size:35px'>Spotify user library explorer</div>"
instruction = ("<div style='font-size:15px'>Select artists on the map and album release decade to filter albums.<br>"
               "Albums view is zoomable, and axes are customizable.<br></div>")

# ### Base layout

# +
artists_points = create_artists_points(artists)
albums_points = create_albums_points(
    x=x_select.value,
    y=y_select.value,
    color=color_select.value,
    data=albums
)

layout = pn.Column(
    pn.Row(
        pn.Column(
            pn.Pane(title, width=400),
            pn.Pane(instruction, width=400),
        ),
        pn.Pane(artists_points),
    ),
    pn.Row(
        pn.Column(
            decade_box,
            axes_box,
            width=400,
        ),
        pn.Pane(albums_points),
    ),
    width_policy="max", height_policy="max"
)


# -

# ### Interactivity and selections

# +
def update(event):
    if artists_select.index:
        artist_names = artists_points.columns()["name"][artists_select.index]
        data_albums = albums[albums.artist_name.isin(artist_names)]
    else:
        data_albums = albums
    data_albums = data_albums[data_albums.decade.isin(decade_select.value)]
    layout[-1][-1] = create_albums_points(
        x=x_select.value,
        y=y_select.value,
        color=color_select.value,
        data=data_albums
    )

artists_select = hv.streams.Selection1D(source=artists_points)

x_select.param.watch(update, "value");
y_select.param.watch(update, "value");
color_select.param.watch(update, "value");
artists_select.param.watch(update, "index");
decade_select.param.watch(update, "value");
# -

# ### Result

layout.servable()


