"""
Gnome Wallpaper Handler

This module handles updates to the Gnome desktop background by interfacing with the 
settings XML for org.gnome.desktop.background exposed by the GObject API.

Python has available a third-party package PyGObject which provides an interface
for  GTK/Gnome/GIO entities. More information can be found at:
https://pygobject.readthedocs.io/en/latest/ 

Settings for desktop backgrounds are defined under the schema: org.gnome.desktop.background
More information on this schema can be found at: 
https://github.com/GNOME/gsettings-desktop-schemas/blob/master/schemas/org.gnome.desktop.background.gschema.xml.in 
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


class WallpaperUpdateError(Exception):
    """
    Raised when an attempt to update Gnome desktop background fails.
    """

    pass


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


def update_wallpaper(img_path: str, options=None) -> None:
    """
    Update the background image to the one specified by file_path. Raise BackgroundUpdateError if issues encountered
    during attempt to update background.
    """

    """
    Gio Settings object provides Dict-like access to key-value pairs which in this case allow
    us to interact with the Gnome desktop background image settings.
    the target key for changing wallpapers is 'picture-uri' and takes a string representing
    a full path. No errors are thrown for invalid values. Instead, background is set 
    to not include an image. Note that this effect can be desirable for cases where
    a gradient or color is set to the background, but note that this is not currently
    supported by this application. 
    """

    gnome_background_settings = Gio.Settings(schema="org.gnome.desktop.background")

    # check that path exists before update. if not, raise error and notify user
    # following code returns false for empty string "" and invalid rel or abs paths
    # NOTE: os.path.exists accepts integers (open file descriptors). This won't catch
    # invalid types for our purposes. Additional check should be used.

    if type(img_path) != str:
        raise WallpaperUpdateError(f"Invalid parameter: {img_path} is not a string.")

    if not os.path.exists(img_path):
        raise WallpaperUpdateError(
            f"Invalid path provided for image location: {img_path} does not exist."
        )

    # what() returns None if no matching image type is determined for a given file path.
    # See list of valid image types at https://docs.python.org/3/library/imghdr.html
    if imghdr.what(os.path.abspath(img_path)) is None:
        raise WallpaperUpdateError(
            f"Invalid image type provided. {os.path.split(img_path)[-1]} is not a valid image."
        )

    # make sure to use the absolute path so resource is locatable when accessed from schema
    # XML schema is read directly, there is no path validation done by Gnome desktop
    gnome_background_settings["picture-uri"] = os.path.abspath(img_path)
