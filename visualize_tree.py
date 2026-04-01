import csv
import os
import dash
import pygame
import random

from dash import html, Input, Output, State
import dash_cytoscape as cyto
from dash_iconify import DashIconify

from classes import TaxonomyTree

from import_images import get_thumbnail
from tree_style import STYLESHEET
from image_fallback import FALLBACK

TINT_OPACITY = 0.7
IMAGE_MAPPING = {}
BLANK_IMG = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

pygame.mixer.init(44100, -16, 2, 2048)


def play_random_mp3(folder_path: str) -> None:
    """Play the recording at the designated path."""
    max_size = 1024 * 1024

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
    except pygame.error as e:
        print(f"Audio error: {e}")


def build_similarity_map(data: list[dict]) -> dict:
    """Create the similarity map using the inpt value."""
    sim_map = {}
    max_sim = 0
    min_sim = 0

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
    """Use the input file to create a list of mapping about the comparison data of each species."""
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


def run_interactive_taxonomic_tree(tree: TaxonomyTree, data: list[dict]) -> None:
    """修复版：点击空白处清除颜色 + 尽量保持缩放不重置"""
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
            layout={'name': 'preset'},
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
    def update_colors_on_click(tap_node, tap_bg, tap_edge, current_zoom, current_pan):
        # === 1. 点击空白处或边 → 清除所有颜色高亮 ===
        if tap_bg is not None or tap_edge is not None:
            print("[DEBUG] Background or edge clicked → clearing colors")
            return (
                generate_elements(positions, edges, leaves),   # 无 tint 默认状态
                current_zoom,
                current_pan
            )

        # === 2. 没有有效节点点击 ===
        if not tap_node:
            return generate_elements(positions, edges, leaves), current_zoom, current_pan

        clicked_node = str(tap_node.get('id', ''))
        if not clicked_node or 'img_url' not in tap_node:
            return generate_elements(positions, edges, leaves), current_zoom, current_pan

        print(f"[DEBUG] Node clicked: {clicked_node}")

        # === 3. 更新颜色 ===
        new_tints = {}
        for node in positions:
            if node not in leaves:
                continue

            node_str = str(node)
            if node_str == clicked_node:
                new_tints[node] = 'rgba(255, 255, 0, 0.85)'   # 选中黄色

                # 播放声音
                try:
                    leaf = tree.get_species(node)
                    family = leaf.get_parent().get_parent().get_root()
                    play_random_mp3(f'bird_data/{family}/{node}')
                except Exception as e:
                    print(f"Audio error for {node}: {e}")
            else:
                sim = similarity_lookup.get(clicked_node, {}).get(node_str, 0.0)
                new_tints[node] = get_similarity_color_rgba(sim, TINT_OPACITY, max_sim, max_sim_dif)

        new_elements = generate_elements(positions, edges, leaves, tint_colors=new_tints)

        # 返回新 elements + **保持用户当前的 zoom 和 pan**
        return new_elements, current_zoom, current_pan

    save_img_url(IMAGE_MAPPING)
    print("Launching interactive tree on http://127.0.0.1:8050/")
    app.run(debug=False, port=8050)   # 使用 app.run


if __name__ == '__main__':
    import process_recordings

    species_information = process_recordings.build_species_info('bird_data/bird_metadata.csv')
    taxonomy_tree = process_recordings.build_taxonomy_tree(species_information)

    run_interactive_taxonomic_tree(taxonomy_tree, species_information)
