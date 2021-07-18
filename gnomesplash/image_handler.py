"""
Image Handler

Utilities for downloading and manipulating images. 

Downloading images: Supports only requests directly for network requests for image files specified
by URL, with no expectation of authentication or other API 
requests (searching for images on a service, etc). Such activities should be 
performed by the specific source handler.

Image manipulation: is intended only to support limited use cases
related to creating backgrounds/wallpapers for video streaming or 
desktop environment use. Other analogous use cases are welcome
but this is not intended to be a comprehensive photo manipulation program.
"""

import os
import os.path
from pathlib import Path
import imghdr  # use to determine if image is valid
import io
from PIL import Image, UnidentifiedImageError

import requests

# see PyGObject API ref for Gio.Settings or >>> help(Gio.Settings) in REPL
from gi.repository import Gio


class ImageDownloadError(Exception):
    """
    Raised when an image download is unsuccessful.
    """

    pass


def download_image(url: str, file_path: str):
    """
        Download an image at specified url. This is an API agnostic function that does not
        take an API key for a particular service. Expectation is that resource is generally
        accesssible.
    .
        Attempt to save image at target file path. If file path does not exist, it will be created.
        Default location is user's home directory. Returns the location on filesystem where image was saved.

        If downloading image fails for one of various reasons, will raise an appropriate error instead of
        failing silently.

        If file already exists, do not overwrite.
    """

    destination_path = os.path.abspath(file_path)

    # prevent overwriting an existing file. this is a design decision to prevent unintentional deletions
    if os.path.exists(destination_path):
        raise FileExistsError(f"File already exists at {destination_path}.")

    # make sure there is a valid directory path to prevent file not found errors on save later
    if not os.path.exists(os.path.dirname(destination_path)):
        os.makedirs(os.path.dirname(destination_path))

    # now for the good stuff. get the raw image content and use the imaging library to save to file.
    # two main error conditions: bad http request or trying to access something that's not an image.
    r = requests.get(url)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ImageDownloadError(
            f"Download error: something went wrong trying to access {url} (status code {r.status_code})"
        )

    try:
        with Image.open(io.BytesIO(r.content)) as image:
            image.save(destination_path)

    except UnidentifiedImageError:
        raise ImageDownloadError(
            f"Download error: the target resource at {url} does not appear to be an image."
        )
