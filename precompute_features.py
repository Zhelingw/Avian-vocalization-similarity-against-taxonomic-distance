"""
CSC111 Project 2: Feature Pre-computation Module

This module extracts vocalization features from all bird recordings
and saves them to a CSV file. This is the slow step (several minutes),
so it only needs to be run once. After that, main.py loads the saved
features directly.

Usage:
    python precompute_features.py

Output:
    bird_data/species_features.csv

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
import csv
from classes import RecordingData
from sound_analysis import features_to_vector

API_DATA_FILE = 'bird_data/bird_metadata.csv'
OUTPUT_FILE = 'bird_data/species_features.csv'


def collect_recording_paths(metadata_file: str) -> dict[str, list[str]]:
    """Collect all recording file paths for each species from the metadata CSV.

    Returns a dict: latin_name -> [list of recording file paths]

    Preconditions:
        - metadata_file is a valid CSV file path
    """
    species_paths: dict[str, list[str]] = {}

    with open(metadata_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)  # skip header
        for row in reader:
            latin_name = row[3]
            path = 'bird_data/' + row[6]
            if latin_name not in species_paths:
                species_paths[latin_name] = []
            species_paths[latin_name].append(path)

    return species_paths


def precompute_and_save() -> None:
    """Extract features for all species and save to CSV.

    Each row in the output CSV contains:
        latin_name, mfcc_0, mfcc_1, ..., mfcc_7, pitch_mean, centroid_mean, bandwidth_mean, rms_mean
    """
    print('Collecting recording paths...')
    species_paths = collect_recording_paths(API_DATA_FILE)
    print(f'Found {len(species_paths)} species.\n')

    print('Extracting features (this may take a few minutes)...')
    rows = []
    for latin_name, paths in species_paths.items():
        print(f'  {latin_name} ({len(paths)} recordings)...', end='', flush=True)
        recording = RecordingData(paths)

        if recording.features and recording.features != {}:
            vector = features_to_vector(recording.features)
            rows.append([latin_name] + vector)
            print(' done')
        else:
            print(' no valid features, skipping')

    # Write CSV
    header = ['latin_name'] + [f'mfcc_{i}' for i in range(8)] + [
        'pitch_mean', 'centroid_mean', 'bandwidth_mean', 'rms_mean'
    ]
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f'\nSaved features for {len(rows)} species to {OUTPUT_FILE}')


if __name__ == '__main__':
    precompute_and_save()
