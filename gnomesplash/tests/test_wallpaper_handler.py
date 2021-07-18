"""
Test wallpaper_handler

Validate that updates to Gnome desktop background are performed correctly.

This module uses Pytest fixtures and parametrization as the primary means of test
organization and test data management. Custom-defined fixtures are used to provide 
test images and access to desktop background settings. 

*** MOCKING REQUEST CALLS ***

This module uses the patch function from unittest.mock in the standard library to 
mock requests to an external url for the purposes of downloading images. To prevent 
a network call from being executed during test, we patch the get() method from the 
requests module. This replaces the actual get() with a MagicMock from unittest.mock.

In most tests that would require a network call, we also patch the Response object from
requests with a MagicMock. The mocked response is configured to have the necessary behavior
required for a given test, for example, an HTTPError side effect, 200 status code, etc. 
Doing so is necessary when our test depends on the response of a network call that was 
otherwise patched with the mock get request instead.

*** Important Notes on Pytest fixtures and Unittest.Mock.patch ***

When used as decorators, both the patch function and Pytest fixtures employ the pattern 
of injecting arguments into the decorated function implicitly and expecting corresponding
parameters to be defined in the signature of the test function. While straightforward
if there is only one decorator and the function otherwise specifies no parameters, this 
behavior can quickly get confusing when there are multiple decorators at play. Even more 
so when mixing the patch decorator with Pytest fixtures and the parametrize decorator. 
This is largely due to most of these wrappers relying on positional arguments and so the 
signature of the test function becomes extremely brittle and will easily break if these
injected parameters are not defined in the proper order.

A few tips to get correct behavior:
- Place @patch decorators closest to the function definition. 
- Place @parametrize decorator calls above @patch decorators. 
- Place mock_ parameters before Pytest fixtures in the function signature. 
- Parameters "unroll" such that the last decorator before the function definition
    should be the first parameter defined in the signature. The unittest.mock docs 
    have an explanatory note and example clarifying this.

*** Why use decorators instead of context managers? ***
Personal preference, but I find the readibility much greater despite the nasty parameter
situation described above. Try opening a file in a context manager, then mocking a 
function in another context manager, then mocking some other object in another context manager
and suddenly the layers of nested managers gets deep and unpleasant.

For example:

    with open('myfile.txt', 'r') as file:
        with patch('my_function') as mock_func:
            with patch('my_attribute') as mock_attr:
                # do stuff with file, mock_func, mock_attr
                # assert something

One benefit to the above approach instead is the variable definition for mocks is made explicit in
the context manager whereas for the decorator that explicit connection is lost.

Useful References:
Unittest.Mock - https://docs.python.org/3/library/unittest.mock.html
Pytest Fixtures - https://docs.pytest.org/en/6.2.x/fixture.html#fixtures
Pytest Parametrization - https://docs.pytest.org/en/6.2.x/parametrize.html#parametrize
"""

import imghdr  # validate image type
import logging  # report info to pytest output
import os  # manage files and dirs on fs
import os.path  # handle path arguments for saving to fs
import unittest.mock
from pathlib import Path
from urllib.parse import urlparse
from itertools import cycle

import pytest
from requests import HTTPError
from gi.repository import Gio  # see PyObject API

# following entities are tested in this module:
from wallpaper_handler import update_wallpaper
from wallpaper_handler import download_image
from wallpaper_handler import WallpaperUpdateError
from wallpaper_handler import ImageDownloadError


@pytest.fixture
def wallpaper_settings() -> Gio.Settings:
    """
    Setup an object to represent the org.gnome.desktop.background schema for testing. See
    additional details on Gio.Settings in PyGObject API reference.
    """

    return Gio.Settings.new("org.gnome.desktop.background")


@pytest.fixture(scope="module")
def cycle_test_images() -> cycle:
    """
    Return cycle (like an infinitely repeating generator) that collects all available test images
    (Path objects pointing to location in test directory) so that we can iterate through them for testing.
    Note that Pytest fixture scope is set to 'module' so that this fixture (and thus, the image generator)
    is not torn down after each test.
    """

    # rglob is glob but appends **/ so we don't worry about relative pathing from execution dir and test_data
    # from pathlib docs: ** means recursively search across current and all subdirectories
    return cycle(Path().rglob("test_data/**/*.jpg"))


@pytest.fixture
def test_image(cycle_test_images, scope="module") -> Path:
    """
    Returns the next Path object representing an image in the test_data folder.
    """

    return next(cycle_test_images)


@pytest.mark.parametrize(
    "img_url",
    [
        "https://example.com/fakephoto",
        "https://images.unsplash.com/photo-1473081556163-2a17de81fc97",
        "https://images.unsplash.com/photo-1536431311719-398b6704d4cc",
        "https://images.unsplash.com/photo-1558328511-7d6490908755",
    ],
)
@unittest.mock.patch("wallpaper_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallpaper_handler.requests.get", autospec=True)
def test_download_image_success(
    mock_get,
    mock_response,
    tmp_path,
    test_image,
    img_url: str,
):
    """
    Verify that download_image function successfully downloads the target image. Attempt to open the file
    and verify that file downloaded is in fact an image. Filename should be the basename of the img_url
    provided, with an additional extension based on image type. Expect jpg for tests.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = tmp_path / f"{file_name}.jpg"

    with open(test_image, "rb") as img:

        mock_get.return_value = mock_response
        mock_response.content = img.read()

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
@unittest.mock.patch("wallpaper_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallpaper_handler.requests.get", autospec=True)
def test_download_image_new_directory(
    mock_get, mock_response, tmp_path, test_image, img_url: str
):
    """
    Verify that download_image function creates a new directory path in the event the target file path does not exist.
    """

    # make sure the directory is removed before this test.
    extra_dir = tmp_path / "extra_dir"

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = extra_dir / f"{file_name}.jpg"

    with open(test_image, "rb") as img:

        mock_get.return_value = mock_response
        mock_response.content = img.read()

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
@unittest.mock.patch("wallpaper_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallpaper_handler.requests.get", autospec=True)
def test_download_image_size_not_zero(
    mock_get, mock_response, tmp_path, test_image, img_url: str
):
    """
    Verify that image downloaded is not a 0kb file as can sometimes occur if an error in saving
    data occurred but file nevertheless is written.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = tmp_path / f"{file_name}.jpg"

    with open(test_image, "rb") as img:
        mock_get.return_value = mock_response
        mock_response.content = img.read()

        download_image(img_url, file_path=file_path)

    assert file_path.stat().st_size > 0


@pytest.mark.parametrize(
    "img_url",
    [
        "https://example.com/images/myphoto.jpg",
        "https://raw.githubusercontent.com/richiestuver/gnomesplash/master/README.md",
    ],
)
@unittest.mock.patch("wallpaper_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallpaper_handler.requests.get", autospec=True)
def test_download_image_invalid_failure(
    mock_get, mock_response, tmp_path, test_image, img_url: str
):
    """
    Download image should fail if the target is not a valid url or is not an image. Should raise
    an appropriate error (TBD) instead of failing silently or saving the file to filesystem.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = tmp_path / f"{file_name}.jpg"

    with open(test_image, "rb") as img:

        mock_response.content = img.read()
        mock_response.raise_for_status.side_effect = HTTPError
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(ImageDownloadError):
            download_image(img_url, file_path)


@pytest.mark.parametrize(
    "img_url",
    [
        "https://images.unsplash.com/photo-1473081556163-2a17de81fc97",
    ],
)
@unittest.mock.patch("wallpaper_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallpaper_handler.requests.get", autospec=True)
def test_download_image_file_exists_failure(
    mock_get, mock_response, tmp_path, test_image, img_url: str
):
    """
    Verify that download_image function does not repeat image download when file at specified
    path already exists. Function should raise FileNotFound error.
    """

    file_name = os.path.basename(urlparse(img_url).path)
    file_path = tmp_path / f"{file_name}.jpg"

    # make sure there is a file at the specified path already
    if not os.path.exists(file_path):
        with open(file_path, "w"):
            pass

    with open(test_image, "rb") as img:

        mock_get.return_value = mock_response
        mock_response.content = img.read()

        with pytest.raises(FileExistsError):
            download_image(img_url, file_path)


@pytest.mark.parametrize(
    "img_path",
    # collect paths for all images found in subdirectories of project
    [str(file_path) for file_path in Path().rglob("*.jpg")],
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
    assert wallpaper_settings["picture-uri"] == str(Path(img_path).resolve())


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
