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

import subprocess
from subprocess import CalledProcessError
from pathlib import Path
from unittest.mock import patch

import pytest

# following entities are tested in this module:
from wallsy.wallpaper_handler import get_current_wallpaper
from wallsy.wallpaper_handler import update_wallpaper
from wallsy.wallpaper_handler import WallpaperUpdateError


def test_get_background_success():

    wallpaper = get_current_wallpaper()
    assert isinstance(wallpaper, Path)
    assert wallpaper.exists()


@patch("wallsy.wallpaper_handler.subprocess.run", autospec=True)
def test_get_background_failure(fake_run):

    fake_run.side_effect = subprocess.CalledProcessError(cmd="gsettings", returncode=1)

    with pytest.raises(WallpaperUpdateError):
        get_current_wallpaper()


def test_update_background_success(test_image):
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

    update_wallpaper(test_image)

    wallpaper = subprocess.run(
        "/usr/bin/gsettings get org.gnome.desktop.background picture-uri",
        shell=True,
        check=True,
        text=True,
        capture_output=True,
    )

    assert wallpaper.returncode == 0
    assert wallpaper.stdout.strip().removeprefix("'").removesuffix("'") == str(
        test_image.absolute()
    )


@pytest.mark.parametrize(
    "img_path",
    [
        "",
        "/not/a/real/absolute/path.jpg",
        "42",
        "/home/richie/Dropbox/repos/unsplash/wallsy/wallsy/tests/test_data/img/not_an_image.txt",
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
        update_wallpaper(Path(img_path))


@patch("wallsy.wallpaper_handler.subprocess.run", autospec=True)
def test_update_background_subprocess_failure(fake_run):

    fake_run.side_effect = subprocess.CalledProcessError(cmd="gsettings", returncode=1)

    with pytest.raises(WallpaperUpdateError):
        get_current_wallpaper()


def test_set_background_uri(test_image):

    update_wallpaper(test_image.absolute().as_uri())

    wallpaper = subprocess.run(
        "/usr/bin/gsettings get org.gnome.desktop.background picture-uri",
        shell=True,
        check=True,
        text=True,
        capture_output=True,
    )

    assert wallpaper.returncode == 0
    assert wallpaper.stdout.strip().removeprefix("'").removesuffix("'") == str(
        test_image.absolute()
    )


@patch("wallsy.wallpaper_handler.subprocess.run", autospec=True)
def test_get_background_uri(fake_run, test_image):

    fake_run.return_value = subprocess.CompletedProcess(
        args="",
        stdout=test_image.absolute().as_uri(),
        returncode=1,
    )

    wallpaper = get_current_wallpaper()
    assert isinstance(wallpaper, Path)
    assert wallpaper.exists()
