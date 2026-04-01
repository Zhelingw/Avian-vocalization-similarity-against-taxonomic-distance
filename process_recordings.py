"""
CSC111 Project 2: Main Module

Entry point for the full pipeline:
1. Read bird_metadata.csv and extract unique species information
2. Build a taxonomy tree
3. Extract vocalization features for each species using RecordingData
4. Compute pairwise taxonomy distance and vocalization similarity
5. Visualize results

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
import csv

from classes import TaxonomyTree, RecordingData
from sound_analysis import (
    normalize_features,
    cosine_similarity
)
# from visualization import draw_scatter_static, draw_scatter_interactive
import os


###############################################################################