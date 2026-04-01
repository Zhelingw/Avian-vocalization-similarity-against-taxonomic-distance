import requests
from typing import Optional

def get_thumbnail(science_name: str) -> Optional[str]:
    """
    Returns the thumbnail url of a wikipedia page for a type of birds, if it exists.
    """
    url = (f'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages|pageprops&format=json&'
           f'piprop=thumbnail&titles={science_name}&pithumbsize=300&redirects')

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
                print(f"No Wikipedia page found for: {science_name}")
                return None

            if 'thumbnail' in page_info:
                image_url = page_info['thumbnail']['source']
                # print(f"Image URL for {science_name}: {image_url}")
                return image_url
            else:
                print(f"A page was found for {science_name}, but it doesn't have a thumbnail image.")
                return None

    except requests.exceptions.RequestException as error:
        print(f"Error: {error}")
        return None


if __name__ == '__main__':
    # Test with the Great tit
    image = get_thumbnail("Great_tit")
    print(image)