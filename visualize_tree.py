import csv, os, dash, pygame, random, time
from dash import html, Input, Output
import dash_cytoscape as cyto
from dash_iconify import DashIconify

from classes import TaxonomyTree
from classes import tree as example_tree

from import_images import get_thumbnail
from tree_style import STYLESHEET
from image_fallback import FALLBACK

TINT_OPACITY = 0.7
IMAGE_MAPPING = {}
BLANK_IMG = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

pygame.mixer.init(44100, -16, 2, 2048)

def play_random_mp3(folder_path: str) -> None:
    """
    Plays a random mp3 file from folder_path.
    The folder must contain at least one mp3 file.

    Preconditions:
     - os.path.isdir(folder_path) == True
    - sum([1 for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]) > 0
    """
    max_size = 1024 * 1024 # Only play audio whose size is less than 1mb

    mp3_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.mp3')
           and os.path.getsize(os.path.join(folder_path, f)) < max_size]

    random_file = random.choice(mp3_files)
    file_path = os.path.join(folder_path, random_file)

    print(f"Loading and playing: {random_file}")

    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

    except pygame.error as e:
        print(f"An error occurred while trying to play the file: {e}")

def build_similarity_map(data: list[dict]) -> dict:
    """
    Creates a similarity mapping based on given data

    Preconditions:
    - all([comparison["similarity"] is not None for comparison in data])
    - all([comparison["item1"] is not None for comparison in data])
    - all([comparison["item2"] is not None for comparison in data])

    >>> example = [{'item1': "AAA", 'item2': "BBB", 'similarity': 4.5}]
    >>> build_similarity_map(example)
    {'AAA': {'BBB': 4.5}, 'BBB': {'AAA': 4.5}, '_max': 4.5}
    """
    sim_map = {}
    max_sim = 0
    min_sim = 0

    for comparison in data:
        # User defined keys
        n1 = comparison.get('item1').replace(" ", "_")
        n2 = comparison.get('item2').replace(" ", "_")
        sim = comparison.get('similarity', 0.0)

        if not sim_map.get(n1): sim_map[n1] = {}
        if not sim_map.get(n2): sim_map[n2] = {}

        # Bidirectional
        sim_map[n1][n2] = sim
        sim_map[n2][n1] = sim

        if sim > max_sim:
            max_sim = sim
        elif sim < min_sim:
            min_sim = sim

    # Indexes max similarity for computation
    sim_map["_max"] = max_sim
    sim_map["_min"] = min_sim
    sim_map["_dif"] = abs(max_sim - min_sim)

    return sim_map


def get_similarity_color_rgba(similarity: float, opacity: float, max_sim: float, max_sim_dif) -> str:
    """
    Converts 0 to max similarity to Blue-to-Red RGBA string.
    Blue (0 sim) -> Red (max sim)
    """
    dif = abs(max_sim - similarity)
    ratio = dif / max_sim_dif

    r = int(ratio * 255)
    b = int((1 - ratio) * 255)

    return f'rgba({r}, 0, {b}, {opacity})'

def load_comparison_csv(file_name: str) -> list[dict]:
    """
    Loads a predefined CSV file of computed comparison data.
    Then formats into a list of dictionaries for visualization.

    Preconditions:
    - file_name != ""
    """
    data = []

    with open(file_name) as csv_file:
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
    Saves a dict of bird image URLS as CSV in case of web requests fail
    """
    os.makedirs('bird_data', exist_ok=True)

    fieldnames = ['name', 'url']
    file_path = 'bird_data/image_urls.csv'
    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        formatted_rows = [{'name': name, 'url': url} for name, url in urls.items()]

        writer.writerows(formatted_rows)


def calculate_tree_layout(tree: TaxonomyTree) -> tuple[dict, list, list]:
    """
    Recursively assigns X and Y coordinates.

    Preconditions:
    - tree.get_root() is not None
    - subtree.get_root() for all subtrees in tree
    """
    positions = {}
    edges = []
    leaves = []
    leaf_counter = [0]
    alternate = [0]

    def traverse(node, depth=0):
        node_id = node.get_root()
        subtrees = node.get_subtrees()

        if not subtrees:  # Leaf
            positions[node_id] = (leaf_counter[0], depth + alternate[0])
            leaf_counter[0] += 1
            alternate[0] += 1
            leaves.append(node_id)

            if alternate[0] >= 2:
                alternate[0] = 0

            # Fetches bird image
            species_data = node.get_species_data()

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
            my_x = sum(child_x_coords) / len(child_x_coords)
            positions[node_id] = (my_x, depth)
            return my_x

    traverse(tree)
    return positions, edges, leaves


def generate_elements(positions: dict, edges: list, leaves: list, tint_colors: dict = None) -> list:
    if tint_colors is None:
        tint_colors = {node: 'rgba(151, 194, 252, 0.0)' for node in leaves}

    elements = []

    # Generate Nodes
    for node, pos in positions.items():
        is_leaf = node in leaves
        node_str = str(node)  # Ensure string IDs
        node_data = {'id': node_str, 'label': node_str}

        if is_leaf:
            # FIX: Fallback to blank image if URL is missing
            node_data['img_url'] = IMAGE_MAPPING.get(node) or BLANK_IMG
            node_data['tint_color'] = tint_colors.get(node, 'rgba(151, 194, 252, 0.0)')

            is_tinted = node_data['tint_color'] != 'rgba(151, 194, 252, 0.0)'
            node_data['img_opacity'] = is_tinted and '0.5' or '1.0'

        elements.append({
            'data': node_data,
            'position': {'x': pos[0] * 100, 'y': pos[1] * 100},
            'classes': 'leaf' if is_leaf else 'parent'
        })

    # Generate Edges
    for edge in edges:
        elements.append({
            'data': {'source': str(edge[0]), 'target': str(edge[1])}  # Ensure string targets
        })

    return elements


def run_interactive_taxonomic_tree(tree: TaxonomyTree, data: list[dict]) -> None:
    """Initializes and runs the Dash web application."""
    positions, edges, leaves = calculate_tree_layout(tree)
    similarity_lookup = build_similarity_map(data)

    max_sim = similarity_lookup.get("_max", 0)
    max_sim_dif = similarity_lookup.get("_dif", 0)

    initial_elements = generate_elements(positions, edges, leaves)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.Header([
            DashIconify(icon="gis:tree", width=30, style={'marginRight': '10px'}),
            html.H2("Taxonomic Tree of selected species",
                    style={'display': 'inline', 'fontFamily': 'Courier New'}),
        ], style={'textAlign': 'center', 'padding': '20px', 'borderBottom': '1px solid #ccc'}),

        cyto.Cytoscape(
            id='tree',
            elements=initial_elements,
            stylesheet=STYLESHEET,
            layout={'name': 'preset'},
            style={'width': '100%', 'height': '850px', 'backgroundColor': '#eeeeee'},
            userZoomingEnabled=True,
            userPanningEnabled=True
        )
    ])

    @app.callback(
        Output('tree', 'elements'),
        Input('tree', 'tapNodeData')
    )

    # Handles mouse click event
    def update_colors_on_click(tap_data):
        if not tap_data or 'img_url' not in tap_data:
            return generate_elements(positions, edges, leaves)

        clicked_node = str(tap_data['id'])
        new_tints = {}

        for node in positions:
            if node not in leaves: continue

            if str(node) == clicked_node:
                new_tints[node] = 'rgba(255, 255, 0, 0.6)' # Yellow color for selected

                leaf = tree.get_species(node)
                family = leaf.get_parent().get_parent().get_root()

                play_random_mp3('bird_data/' + family + '/' + node)
            else:
                # Update color based on similarity score
                sim = similarity_lookup.get(clicked_node, {}).get(str(node), 0.0)
                new_tints[node] = get_similarity_color_rgba(sim, TINT_OPACITY, max_sim, max_sim_dif)

        return generate_elements(positions, edges, leaves, tint_colors=new_tints)

    # Update url data everytime to store new urls
    save_img_url(IMAGE_MAPPING)

    print("Launching interactive tree on http://127.0.0.1:8050/")
    app.run()


if __name__ == '__main__':
    import process_recordings

    species_information = process_recordings.build_species_info('bird_data/bird_metadata.csv')
    taxonomy_tree = process_recordings.build_taxonomy_tree(species_information)
    run_interactive_taxonomic_tree(taxonomy_tree, species_information)
