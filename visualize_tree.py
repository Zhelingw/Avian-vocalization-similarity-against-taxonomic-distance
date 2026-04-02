"""
CSC111 Project 2: Feature Tree Visualization

This module builds a tree visualizer with dash and cytoscape.
It takes in a TaxonomyTree object and a set of processed comparison data to make an interactive graph.
User will launch the visualizer in their local browser with the following features:
- See entire taxonomic structure represented as a tree
- Interact with nodes and move them around freely
- Click on bird nodes to check its similarity with other species through a blue to red color gradient

Usage:
    from classes import TaxonomyTree
    example_tree = TaxonomyTree(...)

    import visualize_tree
    comparison_data = visualize_tree.load_comparison_csv('bird_data/comparison_data.csv')
    visualize_tree.run_interactive_taxonomic_tree(example_tree, comparison_data)

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""

import csv
import os
import random
from typing import Any

import dash
import pygame
from dash import html, Input, Output, State
import dash_cytoscape as cyto
from dash_iconify import DashIconify

import image_fallback
from classes import TaxonomyTree

from import_images import get_thumbnail
from tree_style import STYLESHEET
from image_fallback import FALLBACK

TINT_OPACITY = 0.7
IMAGE_MAPPING = {}
BLANK_IMG = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


def play_random_mp3(folder_path: str) -> None:
    """Play a random bird recording in the designated path folder."""
    max_size = 1024 * 1024  # FILTERING: max 1mb audio only

    mp3_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.mp3') and os.path.getsize(os.path.join(folder_path, f)) < max_size
    ]

    if not mp3_files:
        print(f"No valid mp3 files found in {folder_path}")
        return

    random_file = random.choice(mp3_files)
    file_path = os.path.join(folder_path, random_file)

    print(f"Playing: {random_file}")

    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
    except RuntimeError as e:
        print(f"Audio error: {e}")


def build_similarity_map(data: list[dict]) -> dict:
    """
    Create the similarity map using the inpt value.
    Computes for necessary variables such as max, min and dif of similarities.
    """
    sim_map = {}
    max_sim = 0.0
    min_sim = 0.0

    for comparison in data:
        n1 = str(comparison.get('item1', '')).replace(" ", "_")
        n2 = str(comparison.get('item2', '')).replace(" ", "_")
        sim = float(comparison.get('similarity', 0.0))

        if not n1 or not n2:
            continue

        if n1 not in sim_map:
            sim_map[n1] = {}
        if n2 not in sim_map:
            sim_map[n2] = {}

        sim_map[n1][n2] = sim
        sim_map[n2][n1] = sim

        if sim > max_sim:
            max_sim = sim
        if sim < min_sim:
            min_sim = sim

    sim_map["_max"] = max_sim
    sim_map["_min"] = min_sim
    sim_map["_dif"] = abs(max_sim - min_sim)
    return sim_map


def get_similarity_color_rgba(similarity: float, opacity: float, max_sim: float, max_sim_dif: float) -> str:
    """
    Return the color that represents the similarity between species.
    More blue represents lower similarity, and more red represents higher similarity.
    """
    if max_sim_dif <= 0 or max_sim <= 0:
        return f'rgba(80, 80, 255, {opacity})'

    norm = max(0.0, min(1.0, similarity / max_sim))

    r = int(norm * 255)
    g = int(norm * 60)
    b = int((1 - norm) * 255)

    return f'rgba({r}, {g}, {b}, {opacity})'


def load_comparison_csv(file_name: str) -> list[dict]:
    """
    Use the input CSV file to create a list of mapping for the comparison data of each species.
    """
    data = []
    with open(file_name, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader, None)
        for row in csv_reader:
            comparison_data = {
                'item1': row[0],
                'item2': row[1],
                'distance': int(row[2]),
                'similarity': float(row[3]),
            }
            data.append(comparison_data)
    return data


def save_img_url(urls: dict[str, str]) -> None:
    """
    Saves currently loaded image URLS to CSV file and updates it for future use.
    """
    os.makedirs('bird_data', exist_ok=True)
    fieldnames = ['name', 'url']
    file_path = image_fallback.PATH
    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        formatted_rows = [{'name': name, 'url': url} for name, url in urls.items()]
        writer.writerows(formatted_rows)


def calculate_tree_layout(tree: TaxonomyTree) -> tuple[dict, list, list]:
    """
    Recursively loops through the tree object and computes for the positions, number of edges, and the specific leaves.
    """
    positions = {}
    edges = []
    leaves = []

    # Uses list in replacement for global variables
    leaf_counter = [0]

    def traverse(node: TaxonomyTree, depth: int = 0) -> float:
        """
        Recursive helper that handles the main calculation.
        Calculates the positions and fetches the image URLs.
        """
        node_id = node.get_root()
        subtrees = node.get_subtrees()

        if not subtrees:  # Leaf
            spacing = round(len(leaves) % 2) # Spaces out the leaves vertically to prevent cramming
            positions[node_id] = (leaf_counter[0], depth + spacing)
            leaf_counter[0] += 1
            leaves.append(node_id)

            species_data = node.get_species_data()

            # Fetches the image URL from either caching or web request
            if species_data:
                url = FALLBACK.get(node_id) or get_thumbnail(species_data.name_common)
                IMAGE_MAPPING[node_id] = url

            return positions[node_id][0]
        else:  # Parent
            child_x_coords = []

            for child in subtrees:
                edges.append((node_id, child.get_root()))
                child_x = traverse(child, depth + 1)
                child_x_coords.append(child_x)

            # Puts the parent node in the middle of all its leaves
            my_x = sum(child_x_coords) / len(child_x_coords)
            positions[node_id] = (my_x, depth)

            return my_x

    traverse(tree)
    return positions, edges, leaves


def generate_elements(positions: dict, edges: list, leaves: list, tint_colors: dict = None) -> list:
    """
    Creates the UI elements from computed data to generate the tree visualizer.
    Uses the style settings imported from tree_style.py.
    """
    if tint_colors is None:
        tint_colors = {leaf: 'rgba(151, 194, 252, 0.0)' for leaf in leaves}

    elements = []

    for node, pos in positions.items():
        is_leaf = node in leaves
        node_str = str(node)
        node_data = {'id': node_str, 'label': node_str}

        if is_leaf:
            node_data['img_url'] = IMAGE_MAPPING.get(node) or BLANK_IMG
            node_data['tint_color'] = tint_colors.get(node, 'rgba(151, 194, 252, 0.0)')
            is_tinted = node_data['tint_color'] != 'rgba(151, 194, 252, 0.0)'
            node_data['img_opacity'] = '0.5' if is_tinted else '1.0'

        elements.append({
            'data': node_data,
            'position': {'x': pos[0] * 100, 'y': pos[1] * 100},
            'classes': 'leaf' if is_leaf else 'parent'
        })

    for edge in edges:
        elements.append({
            'data': {'source': str(edge[0]), 'target': str(edge[1])}
        })

    return elements


def run(tree: TaxonomyTree, data: list[dict]) -> None:
    """
    Main launcher that creates the tree visualizer
    Runs the tree visualizer in browser.
    Handles user input, image loading, and audio replay.
    Rerun to create and launch a new tree.
    """
    positions, edges, leaves = calculate_tree_layout(tree)
    similarity_lookup = build_similarity_map(data)

    max_sim = similarity_lookup.get("_max", 0)
    max_sim_dif = similarity_lookup.get("_dif", 0)

    initial_elements = generate_elements(positions, edges, leaves)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.Header([
            DashIconify(icon="gis:tree", width=30, style={'marginRight': '10px'}),
            html.H2("Taxonomic Tree of selected species of orders Passeriformes, Strigiformes, and Piciformes",
                    style={'display': 'inline', 'fontFamily': 'Courier New'}),
        ], style={'textAlign': 'center', 'padding': '20px', 'borderBottom': '1px solid #ccc'}),

        cyto.Cytoscape(
            id='tree',
            elements=initial_elements,
            stylesheet=STYLESHEET,
            layout={'name': 'preset', 'fit': False},
            style={'width': '100%', 'height': '850px', 'backgroundColor': '#eeeeee'},
            userZoomingEnabled=True,
            userPanningEnabled=True,
            minZoom=0.05,
            maxZoom=15,
            zoom=1.0,
            pan={'x': 0, 'y': 0}
        )
    ])

    @app.callback(
        Output('tree', 'elements'),
        Output('tree', 'zoom'),
        Output('tree', 'pan'),
        Input('tree', 'tapNodeData'),
        Input('tree', 'tapBackgroundData'),
        Input('tree', 'tapEdgeData'),
        State('tree', 'zoom'),
        State('tree', 'pan')
    )
    def on_input(tap_node: dict, *args: Any) -> tuple[list, Any, Any]:
        """
        Handles user input when clicking on PC or tapping on mobile devices.
        Clicking on a Leaf node updates the color of all leaves based on how similar they are.
        Blue = more similar. Red = less similar.
        Clicking on a Leaf node will also play a random bird sound of the bird that the node represents.
        Clicking on the background or an edge resets the colors.

        Note: Cytoscape inputs 5 arguments, but only 1 is needed. So we use *args to prevent erroring.
        """
        print("Unused arguments:", args)
        ctx = dash.callback_context

        # Initial load or unhandled trigger
        if not ctx.triggered:
            return generate_elements(positions, edges, leaves), dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[1]

        # Background or edge was specifically clicked -> clear colors
        if trigger_id in ('tapBackgroundData', 'tapEdgeData'):
            print("[DEBUG] Background or edge clicked → clearing colors")
            return generate_elements(positions, edges, leaves), dash.no_update, dash.no_update

        # Leaf node was specifically clicked
        if trigger_id == 'tapNodeData':
            if not tap_node or 'img_url' not in tap_node:
                return generate_elements(positions, edges, leaves), dash.no_update, dash.no_update

            clicked_node = str(tap_node.get('id', ''))
            print(f"[DEBUG] Node clicked: {clicked_node}")

            new_tints = {}
            for node in positions:
                if node not in leaves:
                    continue

                node_str = str(node)
                if node_str == clicked_node:
                    new_tints[node] = 'rgba(255, 255, 0, 0.85)'  # Yellow for selected node

                    # Plays a random sound
                    leaf = tree.get_species(node)
                    family = leaf.get_parent().get_parent().get_root()
                    play_random_mp3(f'bird_data/{family}/{node}')
                else:
                    # Updates color for all other Leaf nodes
                    sim = similarity_lookup.get(clicked_node, {}).get(node_str, 0.0)
                    new_tints[node] = get_similarity_color_rgba(sim, TINT_OPACITY, max_sim, max_sim_dif)

            return generate_elements(positions, edges, leaves, tint_colors=new_tints), dash.no_update, dash.no_update

        # Fallback
        return generate_elements(positions, edges, leaves), dash.no_update, dash.no_update

    # Updates the URL library everytime to store new thumbnails for next time
    save_img_url(IMAGE_MAPPING)

    print("Launching interactive tree on http://127.0.0.1:8050/")
    app.run(debug=False, port=8050)   # Launches the tree


if __name__ == '__main__':
    import python_ta
    import doctest

    python_ta.check_all(config={
        'extra-imports': [
            "dash",
            "os",
            "csv",
            "pygame",
            "random",
            "html",
            "dash_cytoscape",
            "dash_iconify",
            "import_images",
            "FALLBACK",
            "tree_style",
            "image_fallback",
            "get_thumbnail",
            "classes",
            "typing"
        ],  # the names (strs) of imported modules
        'allowed-io': [
            "run_interactive_taxonomic_tree",
            "play_random_mp3",
            "save_img_url",
            "load_comparison_csv"
        ],  # the names (strs) of functions that call print/open/input
        'max-line-length': 120
    })
    doctest.testmod(verbose=True)
