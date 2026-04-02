"""
CSC111 Project 2: Visualization using scatter plots

This module defines functions used for generating the scatter plots.

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""

import csv
import matplotlib.pyplot as plt
import plotly.graph_objects as go


def draw_scatter_static(data: list) -> None:
    """
    Create a static scatter plot from given data.

    Preconditions:
    - all([type(comparison) == dict for comparison in data])
    - all([comparison["distance"] is not None for comparison in data])
    - all([comparison["similarity"] is not None for comparison in data])
    - all([comparison["item1"] is not None for comparison in data])
    - all([comparison["item2"] is not None for comparison in data])
    """
    x = []
    y = []
    labels = []

    for comparison in data:
        x.append(comparison["distance"])
        y.append(comparison["similarity"])
        labels.append(comparison["item1"] + " & " + comparison["item2"])

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, s=50)

    plt.xlabel('Taxonomic Distance')
    plt.ylabel('Vocalization Similarity')
    plt.title('Static 2D Scatter Plot')

    i = 0
    for label in labels:
        plt.annotate(label, xy=(x[i], y[i]), textcoords="offset points", xytext=(0, 10), ha='center')
        i += 1

    plt.show()


def draw_scatter_interactive(data: list[dict], species_name: str = '') -> None:
    """Draw a scatter plot of the species analysis data,
    with detailed information when mouse hovers over the data points."""
    x = []
    y = []
    hover_texts = []

    common_name_map = load_common_name_map()

    for comparison in data:
        latin1 = comparison.get("item1", "").replace(' ', '_')
        latin2 = comparison.get("item2", "").replace(' ', '_')
        cn1 = common_name_map.get(latin1, latin1.replace('_', ' '))
        cn2 = common_name_map.get(latin2, latin2.replace('_', ' '))

        x.append(comparison["distance"])
        y.append(comparison["similarity"])

        hover_text = (
            f"<b>{latin1.replace('_', ' ')} & {latin2.replace('_', ' ')}</b><br>" +
            f"({cn1} & {cn2})<br>" +
            f"Distance: {comparison['distance']}<br>" +
            f"Similarity: {comparison['similarity']:.4f}"
        )
        hover_texts.append(hover_text)

    fig = go.Figure(data=go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(size=10, color='royalblue', opacity=0.9),
        hovertemplate="%{text}<extra></extra>",
        text=hover_texts
    ))

    if species_name != '':
        title = 'Vocalization Similarity vs Taxonomic Distance between ' + species_name + ' and other species'
    else:
        title = 'Vocalization Similarity vs Taxonomic Distance'

    fig.update_layout(
        title=title,
        xaxis_title='Taxonomic Distance',
        yaxis_title='Vocalization Similarity',
        width=1000,
        height=700,
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            bordercolor="black",
            namelength=-1
        ),
        hovermode='closest'
    )
    fig.show()


def load_common_name_map() -> dict:
    """Loads a mapping of the common name of each species and its Latin name."""
    common_map = {}
    with open('bird_data/bird_metadata.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            latin = row.get('latin_name')
            common = row.get('common_name', '')
            if latin:
                common_map[latin] = common
    return common_map


if __name__ == '__main__':
    example = {
        'item1': "AAA",
        'item2': "BBB",
        'distance': 5,
        'similarity': 5,
    }

    draw_scatter_interactive([example])
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['static_type_checker']
    })
