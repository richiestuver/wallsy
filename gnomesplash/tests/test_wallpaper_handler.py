"""
Test wallpaper_handler

Validate that updates to Gnome desktop background are performed correctly.
"""

import os.path

import pytest
from gi.repository import Gio

from gnomesplash.wallpaper_handler import update_wallpaper
from gnomesplash.wallpaper_handler import WallpaperUpdateError


@pytest.fixture
def wallpaper_settings() -> Gio.Settings:
    """
    Setup an object to represent the org.gnome.desktop.background schema for testing. See
    additional details on Gio.Settings in PyGObject API reference.
    """

    return Gio.Settings.new("org.gnome.desktop.background")


@pytest.mark.parametrize(
    "img_path",
    [
        os.path.abspath("gnomesplash/tests/test_data/img/caseen-kyle-registos-1ht1wnmfDiA-unsplash.jpg"),
        os.path.abspath("gnomesplash/tests/test_data/img/lesly-juarez-uR7DBrAa4HE-unsplash.jpg"),
        os.path.abspath("gnomesplash/tests/test_data/img/stephen-leonardi--k66u8LPqTc-unsplash.jpg"),
    ],
)
def test_update_background_success(wallpaper_settings: Gio.Settings, img_path):
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

    update_wallpaper(img_path)
    assert wallpaper_settings["picture-uri"] == img_path


@pytest.mark.parametrize(
    "img_path",
    ["", "/not/a/real/absolute/path.jpg", 42, os.path.abspath("gnomesplash/tests/test_data/img/not_an_image.txt")],
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
