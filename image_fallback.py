"""
CSC111 Project 2: Image Fallback

This module loads the CSV file that stores bird image URLs and caches them for faster loading.
It order to cache it must be ran everytime a new visualizer tree is made, but is not necessary for the tree creation.
Without caching, visualize_tree.py will call web requests instead to load the images, which is slower and may sometimes
fail.
Thus, it is preferred that main.py runs this module everytime for more efficient and safer loading as failsafe.

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
import csv
PATH = "bird_data/image_urls.csv"

# If web request fails to retrieve image url, then a preset will be chosen from here
FALLBACK = {}


def load_url() -> None:
    """
    Loads the image url data from the csv files.
    """
    with open(PATH) as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            FALLBACK[row[0]] = row[1]


if __name__ == '__main__':
    import doctest
    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            "csv",
        ],  # the names (strs) of imported modules
        'allowed-io': [
            "load_url"
        ],  # the names (strs) of functions that call print/open/input
        'max-line-length': 120
    })
    doctest.testmod(verbose=True)
