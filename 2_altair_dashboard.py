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

# # Dashboard with Altair
#
# Resources:
# - https://altair-viz.github.io/gallery/scatter_linked_brush.html
# - https://altair-viz.github.io/gallery/multiple_interactions.html
# - https://altair-viz.github.io/gallery/select_detail.html
# - https://altair-viz.github.io/user_guide/interactions.html
# - https://altair-viz.github.io/user_guide/customization.html
# - https://github.com/altair-viz/altair/issues/1552
# - https://stackoverflow.com/questions/57244390/has-anyone-figured-out-a-workaround-to-add-a-subtitle-to-an-altair-generated-cha

# +
from pathlib import Path

import altair as alt
import pandas as pd
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
albums["loudness"] = albums.loudness.clip(albums.loudness.quantile(0.05), albums.loudness.quantile(0.95))

# ## Adapt data for simple charts
#
# Join artists to albums to have one unique dataset. This makes Altair interactions much easier.

artists_columns = ["genre_cluster", "genre_specific", "genre_x", "genre_y"]
albums_columns = ["name", "release_date", "popularity", "loudness", "artist_uri", "artist_name"]
data = albums[albums_columns].join(
    artists.set_index("uri")[artists_columns],
    on="artist_uri", how="inner"
).drop("artist_uri", axis=1)

# ## Charts and interactions

# +
genres_selector = alt.selection_multi(fields=["genre_cluster"])
artists_selector = alt.selection(type="interval")
base_chart = alt.Chart(data)
genres_color = alt.condition(genres_selector, alt.Color("genre_cluster:N", legend=None), alt.value("lightgray"))

genres_points = base_chart.mark_point().encode(
    y="genre_cluster:N",
    color=genres_color,
).add_selection(genres_selector)

artists_points = base_chart.mark_point().encode(
    x=alt.X("mean(genre_x)", axis=None),
    y=alt.Y("mean(genre_y)", axis=None),
    color=genres_color,
    tooltip=["artist_name", "genre_cluster", "genre_specific"],
).add_selection(
    artists_selector
)

base_albums_points = base_chart.mark_point().encode(
    x="release_date",
    y="popularity",
)

albums_points = base_albums_points.encode(
    color=alt.condition(
        artists_selector,
        alt.Color("loudness:Q", scale=alt.Scale(scheme="viridis")),
        alt.value("lightgray")
    ),
)

albums_tooltips = base_albums_points.encode(
    opacity=alt.value(0),
    tooltip=["artist_name", "name", "release_date"]
).transform_filter(
    artists_selector
)

# +
title = alt.Chart(
    {"values": [{"text": "Spotify user library explorer"}]}
).mark_text(size=20).encode(
    text="text:N",
)

subtitle = alt.Chart(
    {"values": [{"text": "Click on a genre to filter artists, select artists to filter albums, albums view is zoomable"}]}
).mark_text(size=14).encode(
    text="text:N",
)
# -

chart = alt.vconcat(
    title,
    subtitle,
    alt.hconcat(
        genres_points.properties(title="Genres"),
        artists_points.properties(title="Artists")
    ),
    (albums_points + albums_tooltips).interactive().properties(title="Albums")
).configure_view(
    stroke=None
).configure_concat(
    spacing=10
)
chart

chart.save("altair_dashboard.html")
