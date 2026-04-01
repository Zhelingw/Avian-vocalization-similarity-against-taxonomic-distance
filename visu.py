
import dash
from dash import html, Input, Output
import dash_cytoscape as cyto
from dash_iconify import DashIconify

from classes import TaxonomyTree
from classes import tree as example_tree

from import_images import get_thumbnail
from tree_style import STYLESHEET

TINT_OPACITY = 0.7
IMAGE_MAPPING = {}
BLANK_IMG = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

def build_similarity_map(data: list[dict]) -> dict:
    """
    Creates a similarity mapping based on given data

    Preconditions:
    - all([type(comparison) == dict for comparison in data])
    - all([comparison["similarity"] is not None for comparison in data])
    - all([comparison["item1"] is not None for comparison in data])
    - all([comparison["item2"] is not None for comparison in data])

    >>> example = [{'item1': "AAA", 'item2': "BBB", 'similarity': 4.5}]
    >>> build_similarity_map(example)
    {'AAA': {'BBB': 4.5}, 'BBB': {'AAA': 4.5}, '_max': 4.5}
    """
    sim_map = {}
    max_sim = 0

    for comparison in data:
        # User defined keys
        n1 = comparison.get('item1')
        n2 = comparison.get('item2')
        sim = comparison.get('similarity', 0.0)

        if not sim_map.get(n1): sim_map[n1] = {}
        if not sim_map.get(n2): sim_map[n2] = {}

        # Bidirectional
        sim_map[n1][n2] = sim
        sim_map[n2][n1] = sim

        if sim > max_sim:
            max_sim = sim

    # Indexes max similarity for computation
    sim_map["_max"] = max_sim

    return sim_map


def get_similarity_color_rgba(similarity: float, opacity: float, max_similarity: float) -> str:
    """
    Converts 0 to max similarity to Blue-to-Red RGBA string.
    Blue (0 sim) -> Red (max sim)
    """
    # Clamp between 0 and max_similarity
    sim = max(0.0, min(float(max_similarity), float(similarity)))

    # Normalize to 0.0 - 1.0 range for RGB math
    norm_sim = sim / max_similarity

    r = int(norm_sim * 255)
    b = int((1 - norm_sim) * 255)

    return f'rgba({r}, 0, {b}, {opacity})'


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

    def traverse(node, depth=0):
        node_id = node.get_root()
        subtrees = node.get_subtrees()

        if not subtrees:  # Leaf
            positions[node_id] = (leaf_counter[0], depth)
            leaf_counter[0] += 1
            leaves.append(node_id)

            # Fetches bird image
            species_data = node.get_species_data()

            if species_data:
                url = get_thumbnail(species_data.name_common)
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
    max_similarity = similarity_lookup.get("_max", 5)

    initial_elements = generate_elements(positions, edges, leaves)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.Header([
            DashIconify(icon="gis:tree", width=30, style={'marginRight': '10px'}),
            html.H2("Dynamic Taxonomic Tree",
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
            else:
                # Update color based on similarity score
                sim = similarity_lookup.get(clicked_node, {}).get(str(node), 0.0)
                new_tints[node] = get_similarity_color_rgba(sim, TINT_OPACITY, max_similarity)

        return generate_elements(positions, edges, leaves, tint_colors=new_tints)

    print("Launching interactive tree on http://127.0.0.1:8050/")
    app.run()


if __name__ == '__main__':
    # Example for testing
    leaf_aaa = TaxonomyTree("", "AAA", [])
    leaf_bbb = TaxonomyTree("", "BBB", [])
    leaf_ccc = TaxonomyTree("", "CCC", [])
    leaf_ddd = TaxonomyTree("", "DDD", [])
    parent_1 = TaxonomyTree("", "Parent1", [leaf_aaa, leaf_bbb])
    parent_2 = TaxonomyTree("", "Parent2", [leaf_ccc, leaf_ddd])
    root_tree = TaxonomyTree("", "Root", [parent_1, parent_2])

    comparison_data = [
        {'item1': "AAA", 'item2': "BBB", 'similarity': 4.5},  # High
        {'item1': "AAA", 'item2': "CCC", 'similarity': 2.0},  # Medium
        {'item1': "AAA", 'item2': "DDD", 'similarity': 0.5},  # Low
        {'item1': "BBB", 'item2': "CCC", 'similarity': 1.0},
        {'item1': "BBB", 'item2': "DDD", 'similarity': 3.0},
        {'item1': "CCC", 'item2': "DDD", 'similarity': 5.0},  # Very high
    ]

    # For testing
    # IMAGE_MAPPING = {
    #     "AAA": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/"
    #            "Great_tit_%28Parus_major%29%2C_Parc_du_Rouge-Cloitre%2C_For%C3%AAt_de_Soignes%2C_Brussels_%"
    #            "2826194636951%29.jpg/330px-Great_tit_%28Parus_major%29%2C_Parc_du_Rouge-Cloitre%2C_For%C3%AAt_de_Soignes%"
    #            "2C_Brussels_%2826194636951%29.jpg"
    # }

    # For real application pass in a complete TaxonomyTree object
    # For comparison_data, follows the same format all other graphs
    run_interactive_taxonomic_tree(example_tree, comparison_data)
