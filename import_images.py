"""
CSC111 Project 2: Importing Bird Images

This module handles importing bird thumbnails through the wikimedia API.
Takes the common name of a bird species and searches for a corresponding wikipedia page.
If the page exists, then it fetches the link of the thumbnail image.
However, web requests may fail or hit a rate limit, which is why caching and loading thumbnails locally are preferred.

Usage:
    import import_images

    image = import_images.get_thumbnail("Great_tit")
    print(image)

Output:
    https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Great_tit_%28Parus_major%29%2C_Parc_du_Rouge-Cloitre%2C
    _For%C3%AAt_de_Soignes%2C_Brussels_%2826194636951%29.jpg/330px-Great_tit_%28Parus_major%29%2C_Parc_du_Rouge-Cloit
    re%2C_For%C3%AAt_de_Soignes%2C_Brussels_%2826194636951%29.jpg

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
from typing import Optional
import requests


def get_thumbnail(common_name: str) -> Optional[str]:
    """
    Returns the thumbnail url of a wikipedia page for a type of birds, if it exists.
    """
    url = (f'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages|pageprops&format=json&'
           f'piprop=thumbnail&titles={common_name}&pithumbsize=300&redirects')

    headers = {
        'User-Agent': 'BirdImageFetcher'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        pages = data.get('query', {}).get('pages', {})

        # Wikipedia uses dynamic page ID as the dictionary key, loop through them
        for page_id, page_info in pages.items():
            # Check if the page actually exists
            if page_id == "-1":
                print(f"No Wikipedia page found for: {common_name}")
                return None

            if 'thumbnail' in page_info:
                image_url = page_info['thumbnail']['source']

                return image_url

        print(f"A page was found for {common_name}, but it doesn't have a thumbnail image.")
        return None
    except requests.exceptions.RequestException as error:
        print(f"Error: {error}")
        return None


if __name__ == '__main__':
    import doctest
    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            "typing",
            "requests"
        ],  # the names (strs) of imported modules
        'allowed-io': [
            "get_thumbnail"
        ],  # the names (strs) of functions that call print/open/input
        'max-line-length': 120
    })
    doctest.testmod(verbose=True)
