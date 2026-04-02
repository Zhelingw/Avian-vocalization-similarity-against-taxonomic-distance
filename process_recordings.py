"""
CSC111 Project 2: recordings processing file

Entry point for the full pipeline:
1. Read bird_metadata.csv and extract unique species information
2. Build a taxonomy tree
3. Extract vocalization features for each species using RecordingData
4. Compute pairwise taxonomy distance and vocalization similarity

Copyright (c) 2026 Lucy Wang,  Ted Song, Yiming Xu. All rights reserved.
"""
import csv
import os

from classes import TaxonomyTree, RecordingData
from sound_analysis import (
    normalize_features,
    cosine_similarity
)


# Constants
API_DATA_FILE = 'bird_data/bird_metadata.csv'
TAXONOMY_INFORMATION = 'bird_data/bird_taxonomy.csv'
COMPARISON_DATA_FILE = 'bird_data/comparison_data.csv'


# Read metadata and build species information
def build_species_info(metadata_file: str) -> list[dict[str, str]]:
    """Read the metadata CSV and return a list of unique species records.

    Each record is a dict containing: family, genus, species, latin_name, common_name.

    Preconditions:
        - metadata_file is a valid CSV file path
    """
    species_information = []
    existing_species: set[str] = set()

    with open(metadata_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)  # skip header
        for row in reader:
            if row[3] not in existing_species:
                existing_species.add(row[3])
                species_information.append({
                    'family': row[0],
                    'genus': row[1],
                    'species': row[2],
                    'latin_name': row[3],
                    'common_name': row[4]
                })

    return species_information


def write_taxonomy_csv(species_information: list[dict[str, str]],
                       output_file: str) -> None:
    """Write unique species information to a CSV file for building the taxonomy tree.

    Preconditions:
        - species_information is non-empty
        - output_file is a valid writable path
    """
    fieldnames = ['family', 'genus', 'species', 'latin_name', 'common_name']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(species_information)


# Build taxonomy tree
def build_taxonomy_tree(species_information: list[dict[str, str]]) -> TaxonomyTree:
    """Build a TaxonomyTree from species_information.

    Preconditions:
        - species_information is non-empty
    """
    taxonomy_tree = TaxonomyTree(
        rank='Class',
        root='Aves',
        subtrees=[]
    )

    for row in species_information:
        taxonomy_tree.add_species(
            family=row['family'],
            genus=row.get('genus', row['latin_name'].split('_')[0]),
            latin_name=row['latin_name'],
            common_name=row['common_name'],
            recording_data=RecordingData([])
        )

    return taxonomy_tree


# Extract features and build feature vector dictionary
def collect_recording_paths(metadata_file: str) -> dict[str, list[str]]:
    """Collect all recording file paths for each species from the metadata CSV.

    Returns a dict: latin_name -> [list of recording file paths]

    Preconditions:
        - metadata_file is a valid CSV file path
    """
    species_paths: dict[str, list[str]] = {}

    with open(metadata_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            latin_name = row[3]
            path = 'bird_data/' + row[6]
            if latin_name not in species_paths:
                species_paths[latin_name] = []
            species_paths[latin_name].append(path)

    return species_paths


def extract_all_species_features(
    species_paths: dict[str, list[str]]
) -> dict[str, list[float]]:
    """Create a RecordingData for each species, extract features, and convert to feature vectors.

    Returns a dict: latin_name -> feature vector (list[float])

    Preconditions:
        - species_paths is non-empty
        - each latin_name maps to a non-empty list of paths
    """
    species_vectors: dict[str, list[float]] = {}

    for latin_name, paths in species_paths.items():
        print(f'  Extracting features for {latin_name} ({len(paths)} recordings)...')
        recording = RecordingData(paths)

        vector = recording.get_feature_vector()
        if vector:
            species_vectors[latin_name] = vector
        else:
            print(f'    Warning: {latin_name} has no valid features, skipping.')

    return species_vectors


# Compute taxonomy distance + vocalization similarity
def build_comparison_data(
    taxonomy_tree: TaxonomyTree,
    species_vectors: dict[str, list[float]]
) -> list[dict]:
    """Build comparison data for visualization.

    For each pair of species with extracted features, compute:
        - taxonomic distance (from the taxonomy tree)
        - vocalization similarity (cosine similarity after normalization)

    Returns a list of dicts in the format expected by visualization.py:
        {'item1': str, 'item2': str, 'distance': int, 'similarity': float}

    Preconditions:
        - len(species_vectors) >= 2
    """
    normalized = normalize_features(species_vectors)
    species_list = sorted(normalized.keys())

    comparison_data = []

    for i in range(len(species_list)):
        for j in range(i + 1, len(species_list)):
            s1 = species_list[i]
            s2 = species_list[j]

            distance = taxonomy_tree.get_distance_between(s1, s2)

            if distance is not None:
                similarity = cosine_similarity(normalized[s1], normalized[s2])

                comparison_data.append({
                    'item1': s1.replace('_', ' '),
                    'item2': s2.replace('_', ' '),
                    'distance': distance,
                    'similarity': round(similarity, 4)
                })

    return comparison_data


def save_comparison_data(comparison_data: list[dict], output_file: str) -> None:
    """Save the pairwise comparison data to a CSV file.

    This allows quick reloading for visualization without recomputing everything.

    Preconditions:
        - output_file is a valid writable path
    """
    if not comparison_data:
        print('Warning: No comparison data to save.')
        return

    fieldnames = ['item1', 'item2', 'distance', 'similarity']

    file_exists = os.path.isfile(output_file)

    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(comparison_data)


def process_data() -> None:
    """Run the data analysis pipeline.

    Steps:
    1. Read metadata
    2. Build tree
    3. Extract features
    4. Pairwise comparison
    5. Output to designated file
    """
    species_information = build_species_info(API_DATA_FILE)
    write_taxonomy_csv(species_information, TAXONOMY_INFORMATION)

    taxonomy_tree = build_taxonomy_tree(species_information)

    species_paths = collect_recording_paths(API_DATA_FILE)
    species_vectors = extract_all_species_features(species_paths)

    comparison_data = build_comparison_data(taxonomy_tree, species_vectors)

    save_comparison_data(comparison_data, COMPARISON_DATA_FILE)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['csv', 'os', 'classes', 'sound_analysis'],
        'allowed-io': ['build_species_info', 'write_taxonomy_csv', 'collect_recording_paths',
                       'extract_all_species_features', 'save_comparison_data', 'process_data'],
        'max-line-length': 120
    })