
from visualization import draw_scatter_interactive
from collections import defaultdict
import csv
import statistics
import matplotlib.pyplot as plt
from scipy import stats
import visualize_tree
import process_recordings

COMPARISON_DATA_FILE = 'bird_data/comparison_data.csv'


def draw_full_graph() -> None:
    """Draw the Graph of all species"""
    with open(COMPARISON_DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        comparison_data = list(reader)

    for row in comparison_data:
        row['distance'] = int(row['distance'])
        row['similarity'] = float(row['similarity'])

    draw_scatter_interactive(comparison_data)


def analyze_distance_statistics() -> None:
    """
    Draw a Bar & Whisker Plot using the mean and standard deviation of the species
    """

    with open(COMPARISON_DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    distance_groups = defaultdict(list)

    for row in data:
        try:
            dist = int(row['distance'])
            sim = float(row['similarity'])
            distance_groups[dist].append(sim)
        except (ValueError, TypeError, KeyError):
            continue

    if not distance_groups:
        return

    stats_list = []
    for dist in sorted(distance_groups.keys()):
        sims = distance_groups[dist]
        if len(sims) < 1:
            continue

        stats_list.append((dist, sims))

    print("="*70)

    # Draw the chart
    plt.figure(figsize=(10, 6))
    plot_data = [sims for _, sims in stats_list]
    x_labels = [str(dist) for dist, _ in stats_list]

    plt.boxplot(plot_data, labels=x_labels, patch_artist=True,
                boxprops=dict(facecolor='lightblue', alpha=0.8),
                medianprops=dict(color='red', linewidth=2))

    plt.xlabel('Taxonomic Distance', fontsize=12)
    plt.ylabel('Vocalization Similarity', fontsize=12)
    plt.title('Vocalization Similarity Distribution by Taxonomic Distance\n(Box & Whisker Plot)', fontsize=14)

    # Add the mean points
    for i, sims in enumerate(plot_data):
        plt.scatter(i+1, statistics.mean(sims), color='red', marker='o', s=50, label='Mean' if i == 0 else "")

    plt.grid(True, alpha=0.3, axis='y')
    plt.legend()
    plt.tight_layout()
    plt.show()


def draw_graph_of(species_name: str) -> None:
    """
    Draw the graph of the single assigned species with other species.
    """

    with open(COMPARISON_DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_data = list(reader)

        filtered_data = []
        for row in all_data:
            item1 = row.get('item1', '')
            item2 = row.get('item2', '')

            if species_name in item1 or species_name in item2:
                try:
                    row_dict = {
                        'item1': item1,
                        'item2': item2,
                        'distance': int(row['distance']),
                        'similarity': float(row['similarity'])
                    }
                    filtered_data.append(row_dict)
                except (ValueError, TypeError, KeyError):
                    continue

        draw_scatter_interactive(filtered_data, species_name)


def analyze_correlation() -> None:
    """
    Analyse the correlation between Taxonomic Distance and Vocalization Similarity,
    Output Pearson r, R^2, p-value
    """

    with open(COMPARISON_DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    distances = []
    similarities = []

    for row in data:
        try:
            dist = float(row['distance'])
            sim = float(row['similarity'])
            distances.append(dist)
            similarities.append(sim)
        except (ValueError, TypeError, KeyError):
            continue

    if len(distances) < 3:
        print("no sufficient data")
        return

    # Pearson correlation analysis
    r, p_value = stats.pearsonr(distances, similarities)
    r_squared = r ** 2

    print("\n" + "="*70)
    print("Taxonomic Distance vs Vocalization Similarity correlation analysis")
    print("="*65)
    print(f"Pearson r   : {r:.4f}")
    print(f"R^2         : {r_squared:.4f}  ({r_squared*100:.2f}%)")
    print(f"p-value     : {p_value:.6f}")
    print("="*70)


if __name__ == '__main__':
    species_information = process_recordings.build_species_info('bird_data/bird_metadata.csv')
    process_recordings.write_taxonomy_csv(species_information, 'bird_data/bird_taxonomy.csv')
    taxonomy_tree = process_recordings.build_taxonomy_tree(species_information)

    # draw_graph_of('Ninox connivens')
    # draw_full_graph()
    # analyze_distance_statistics()
    # analyze_correlation()
    visualize_tree.run_interactive_taxonomic_tree(taxonomy_tree, species_information)

# if __name__ == '__main__':
#     # ... 你的 example_tree 和 comparison_data ...
#     species_information = process_recordings.build_species_info('bird_data/bird_metadata.csv')
#     process_recordings.write_taxonomy_csv(species_information, 'bird_data/bird_taxonomy.csv')
#     taxonomy_tree = process_recordings.build_taxonomy_tree(species_information)
#
#     print("=== Starting with example_tree ===")
#     similarity_lookup = visualize_tree.build_similarity_map(species_information)  # 先计算一次
#     max_similarity = similarity_lookup.get("_max", 5.0)
#     positions, edges, leaves = visualize_tree.calculate_tree_layout(taxonomy_tree)
#
#     visualize_tree.run_interactive_taxonomic_tree(taxonomy_tree, species_information)  # 只跑一个！

    # 暂时注释掉第二个，避免端口冲突和变量覆盖
    # run_interactive_taxonomic_tree(root_tree, comparison_data)
