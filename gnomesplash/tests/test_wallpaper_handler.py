"""
Test wallpaper_handler

Validate that updates to Gnome desktop background are performed correctly.
"""

import imghdr  # validate image type
import logging  # report info to pytest output
import os  # manage files and dirs on fs
import os.path  # handle path arguments for saving to fs
from urllib.parse import urlparse
from _pytest.nodes import File

import pytest
from gi.repository import Gio  # see PyObject API


# following entities are tested in this module:
from gnomesplash.wallpaper_handler import update_wallpaper
from gnomesplash.wallpaper_handler import download_image
from gnomesplash.wallpaper_handler import WallpaperUpdateError
from gnomesplash.wallpaper_handler import ImageDownloadError


@pytest.fixture
def wallpaper_settings() -> Gio.Settings:
    """
    Setup an object to represent the org.gnome.desktop.background schema for testing. See
    additional details on Gio.Settings in PyGObject API reference.
    """

    return Gio.Settings.new("org.gnome.desktop.background")


@pytest.fixture
def clear_downloads(caplog) -> None:
    # store images downloaded as a result of tests in the project directory only.
    # This directory should be cleared prior to each run to ensure a clean test.

    dirs = [
        os.path.abspath("gnomesplash/tests/test_data/downloads"),
        os.path.abspath("gnomesplash/tests/test_data/downloads/extra_dir"),
    ]

    for downloads_folder in dirs:
        if os.path.exists(downloads_folder):
            # raise FileNotFoundError(
            #     f"Directory {downloads_folder} does not exist. Make sure project structure is intact."
            # )

            # scandir returns an iterator of DirEntry objects that contains a representation of each file in the directory
            # along with useful attributes like name, path, is_file, etc.
            with os.scandir(downloads_folder) as dir:
                for (
                    file_entry
                ) in dir:  # iterator, so continues until StopIteration is raised
                    os.remove(file_entry.path)

        # show result of test setup in testing output. see caplog info in Pytest docs.
        caplog.set_level(logging.INFO)
        logging.info(f"Pre-test setup: {downloads_folder} does not exist or is empty.")


@pytest.mark.parametrize(
    "img_url",
    [
        "https://images.unsplash.com/photo-1473081556163-2a17de81fc97",
        "https://images.unsplash.com/photo-1536431311719-398b6704d4cc",
        "https://images.unsplash.com/photo-1558328511-7d6490908755",
    ],
)
def test_download_image_success(clear_downloads, img_url: str):
    """
    Verify that download_image function successfully downloads the target image. Attempt to open the file
    and verify that file downloaded is in fact an image. Filename should be the basename of the img_url
    provided, with an additional extension based on image type. Expect jpg for tests.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = os.path.join(
        "gnomesplash/tests/test_data/downloads", f"{file_name}.jpg"
    )

    download_image(img_url, file_path=file_path)

    with open(file_path, "rb") as file:  # will raise FileNotFound error
        assert imghdr.what(file) is not None  # None returned for invalid files


@pytest.mark.parametrize(
    "img_url",
    [
        "https://images.unsplash.com/photo-1473081556163-2a17de81fc97",
        "https://images.unsplash.com/photo-1536431311719-398b6704d4cc",
        "https://images.unsplash.com/photo-1558328511-7d6490908755",
    ],
)
def test_download_image_new_directory(img_url: str):
    """
    Verify that download_image function creates a new directory path in the event the target file path does not exist.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = os.path.join(
        "gnomesplash/tests/test_data/downloads/extra_dir", f"{file_name}.jpg"
    )

    download_image(img_url, file_path=file_path)

    with open(file_path, "rb") as file:  # will raise FileNotFound error
        assert imghdr.what(file) is not None  # None returned for invalid files


@pytest.mark.parametrize(
    "img_url",
    [
        "https://example.com/images/myphoto.jpg",
        "https://raw.githubusercontent.com/richiestuver/gnomesplash/master/README.md",
    ],
)
def test_download_image_invalid_failure(img_url: str):
    """
    Download image should fail if the target is not a valid url or is not an image. Should raise
    an appropriate error (TBD) instead of failing silently or saving the file to filesystem.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = os.path.join(
        "gnomesplash/tests/test_data/downloads", f"{file_name}.jpg"
    )

    with pytest.raises(ImageDownloadError):
        download_image(img_url, file_path)


@pytest.mark.parametrize(
    "img_url",
    [
        "https://images.unsplash.com/photo-1473081556163-2a17de81fc97",
    ],
)
def test_download_image_file_exists_failure(img_url: str):
    """
    Verify that download_image function does not repeat image download when file at specified
    path already exists. Function should raise FileNotFound error.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = os.path.join(
        "gnomesplash/tests/test_data/downloads", f"{file_name}.jpg"
    )

    # make sure there is a file at the specified path already
    if not os.path.exists(file_path):
        with open(file_path, "w"):
            pass

    with pytest.raises(FileExistsError):
        download_image(img_url, file_path)


@pytest.mark.parametrize(
    "img_path",
    [
        os.path.abspath(
            "gnomesplash/tests/test_data/img/caseen-kyle-registos-1ht1wnmfDiA-unsplash.jpg"
        ),
        os.path.abspath(
            "gnomesplash/tests/test_data/img/lesly-juarez-uR7DBrAa4HE-unsplash.jpg"
        ),
        os.path.abspath(
            "gnomesplash/tests/test_data/img/stephen-leonardi--k66u8LPqTc-unsplash.jpg"
        ),
    ],
)
def test_update_background_success(wallpaper_settings: Gio.Settings, img_path: str):
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
    [
        "",
        "/not/a/real/absolute/path.jpg",
        42,
        os.path.abspath("gnomesplash/tests/test_data/img/not_an_image.txt"),
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
