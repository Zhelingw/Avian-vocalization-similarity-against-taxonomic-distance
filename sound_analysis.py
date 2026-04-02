"""
CSC111 Project 2: Sound Analysis Module

This module handles vocalization similarity computation, including:
- Z-score normalization (to prevent features with large ranges from dominating)
- Cosine similarity computation
- Pairwise similarity comparison across all species

Feature extraction is handled by RecordingData in classes.py;
this module only processes the extracted data.

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
from __future__ import annotations
import math


# Feature vector conversion
def features_to_vector(features: dict) -> list[float]:
    """Convert a RecordingData.features dict into an ordered feature vector for similarity computation.

    Vector order: mfcc[0..n] + pitch_mean + centroid_mean + bandwidth_mean + rms_mean

    Preconditions:
        - features != {}
        - 'mfcc' in features
        - all(k in features for k in ['pitch_mean', 'centroid_mean', 'bandwidth_mean', 'rms_mean'])
    """
    vector = list(features['mfcc'])
    vector.append(features['pitch_mean'])
    vector.append(features['centroid_mean'])
    vector.append(features['bandwidth_mean'])
    vector.append(features['rms_mean'])
    return vector


# Similarity computation
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute the cosine similarity between two feature vectors.

    Cosine similarity measures the angle between two vectors, returning a value
    between -1 and 1. Values closer to 1 indicate greater similarity.

    Preconditions:
        - len(vec_a) == len(vec_b)
        - len(vec_a) > 0
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def euclidean_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute the Euclidean distance between two feature vectors.

    Smaller distances indicate more similar vocalizations.

    Preconditions:
        - len(vec_a) == len(vec_b)
        - len(vec_a) > 0
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))


# Z-score normalization
def normalize_features(species_vectors: dict[str, list[float]]) -> dict[str, list[float]]:
    """Perform Z-score normalization on all species feature vectors.

    Each feature dimension is standardized to have mean 0 and standard deviation 1.
    This prevents features with large numeric ranges (e.g. pitch in Hz)
    from overwhelming features with small ranges (e.g. MFCC coefficients).

    Preconditions:
        - len(species_vectors) > 0
        - all vectors have the same length
    """
    species_list = list(species_vectors.keys())
    vectors = [species_vectors[s] for s in species_list]
    num_features = len(vectors[0])
    num_species = len(vectors)

    # Compute mean and standard deviation for each feature dimension
    means = []
    stds = []
    for i in range(num_features):
        values = [vectors[j][i] for j in range(num_species)]
        mean_val = sum(values) / num_species
        variance = sum((v - mean_val) ** 2 for v in values) / num_species
        std_val = math.sqrt(variance) if variance > 0 else 1.0
        means.append(mean_val)
        stds.append(std_val)

    # Normalize
    normalized = {}
    for s in species_list:
        vec = species_vectors[s]
        normalized[s] = [(vec[i] - means[i]) / stds[i] for i in range(num_features)]

    return normalized


# Pairwise similarity computation
def compute_all_pairwise_similarities(
    species_vectors: dict[str, list[float]]
) -> list[tuple[str, str, float]]:
    """Compute cosine similarity between all pairs of species.

    Performs Z-score normalization first, then computes cosine similarity.
    Returns a list of (species1, species2, similarity) tuples,
    sorted by similarity in descending order.

    Preconditions:
        - len(species_vectors) >= 2
    """
    normalized = normalize_features(species_vectors)

    species_list = sorted(normalized.keys())
    results = []

    for i in range(len(species_list)):
        for j in range(i + 1, len(species_list)):
            s1 = species_list[i]
            s2 = species_list[j]
            sim = cosine_similarity(normalized[s1], normalized[s2])
            results.append((s1, s2, sim))

    results.sort(key=lambda x: x[2], reverse=True)
    return results


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['math'],
        'max-line-length': 120
    })
