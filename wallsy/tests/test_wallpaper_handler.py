"""
Test wallpaper_handler

Validate that updates to Gnome desktop background are performed correctly.

This module uses Pytest fixtures and parametrization as the primary means of test
organization and test data management. Custom-defined fixtures are used to provide 
test images and access to desktop background settings. 

*** Fixtures ***
- test_image (defined in conftest.py)

Useful References:
Pytest Fixtures - https://docs.pytest.org/en/6.2.x/fixture.html#fixtures
Pytest Parametrization - https://docs.pytest.org/en/6.2.x/parametrize.html#parametrize
"""

from pathlib import Path
from itertools import cycle

import pytest
from gi.repository import Gio  # see PyObject API

# following entities are tested in this module:
from wallsy.wallpaper_handler import update_wallpaper
from wallsy.wallpaper_handler import WallpaperUpdateError


@pytest.fixture
def wallpaper_settings() -> Gio.Settings:
    """
    Setup an object to represent the org.gnome.desktop.background schema for testing. See
    additional details on Gio.Settings in PyGObject API reference.
    """

    return Gio.Settings.new("org.gnome.desktop.background")


def test_update_background_success(test_image, wallpaper_settings: Gio.Settings):
    """
    Load sample images and set the background appropriately. Settings schema for org.gnome.desktop.background
    is stored in wallpaper_settings, a dict-like object provided by PyGObject to interface with GIO library.

    Note that by design, updating the picture-uri key in the schema to the empty string "" will
    intentionally set the Gnome background to no image. There are additional parameters that support
    changing the color of the background, gradients etc.

    Therefore, this function cannot in fact validate that an image was presented on screen. There is an important
    failure condition where a non-existent path is provided, which will behave the
    same as the empty string and display no image for the background, defaulting instead to the default color.

    An error should be raised and checked in another test to make sure a valid img_path file path is provided.
    """

    update_wallpaper(str(test_image))
    assert wallpaper_settings["picture-uri"] == str(test_image.resolve())


@pytest.mark.parametrize(
    "img_path",
    [
        "",
        "/not/a/real/absolute/path.jpg",
        42,
        Path().rglob("not_an_image.txt"),
    ],
)
def test_update_background_failure(img_path):
    """
    Verify that call to update_background successfully raises appropriate error type for invalid inputs.
    Call pytest.mark.parametrize with test cases to validate:
    - empty path
    - invalid path
    - invalid data type (e.g. instead of str)
    - non-image file type
    """

    with pytest.raises(WallpaperUpdateError):
        update_wallpaper(img_path)
