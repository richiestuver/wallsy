"""
Unsplash API Handler

This module contains functions for retrieving random photos from the Unsplash
API. The API requires a developer account and corresponding API key however
it is otherwise free to use.
"""

# TODO: handle api keys
# TODO: rewrite as a class to initialize API key since it is common across all functions defined below
# TODO: likewise, image data is handled by two out of three methods.


def get_topics(api_key: str) -> list:
    """
    Return a list of all Topics currently available from Unsplash. Topics can
    be supplied as filter criteria for requests for photos.
    """

    pass


def get_random_photo(api_key: str, topics=None, orientation="landscape") -> dict:
    """
    Return a dictionary of JSON response from Unsplash API representing a
    single image data.
    See https://unsplash.com/documentation#get-a-random-photo for endpoint
    documentation.

    :param topics: keyword argument is a list of strings representing topics to
    filter results by.
    :param orientation: valid values from API are 'landscape', 'portrait',
    'squarish'
    """

    pass


def download_photo(api_key: str, photo_data: dict):
    """
    Download a photo using the correct url path provided in the photo data
    dict. REQUIRED - this method must call the download endpoint to track
    downloads as per API guidelines.


    """

    pass
