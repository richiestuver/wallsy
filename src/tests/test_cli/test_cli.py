"""
Test the CLI driver for Wallsy

cli.py is the entry point for the wallsy program. verify that standard
invokation returns with correct exit code on success or failure.
"""

import unittest.mock
from urllib.parse import urlparse
from pathlib import Path
from subprocess import run


from click.testing import CliRunner

from wallsy.cli import cli

runner = CliRunner()


def test_invocation_no_args():
    result = runner.invoke(cli)

    assert result.exit_code == 0


def test_invocation_failure_invalid_args():
    result = runner.invoke(cli, ["--thiswillneverbeanoption"])

    assert result.exception is not None
    assert result.exit_code != 0


def test_invocation_failure_no_commands(test_image):
    result = runner.invoke(cli, ["--file", str(test_image.resolve())])

    assert result.exception is not None
    assert result.exit_code != 0


def test_option_file_single_success(test_image):
    result = runner.invoke(cli, ["--file", str(test_image.resolve()), "show"])

    print(result.stderr, result.stdout)
    assert result.exit_code == 0


# see test_image_handler.py to see this pattern used extensively for mocking out network calls
@unittest.mock.patch("wallsy.image_handler.requests.models.Response", autospec=True)
@unittest.mock.patch("wallsy.image_handler.requests.get", autospec=True)
def test_option_url_single_success(
    mock_get,
    mock_response,
    test_image,
    img_url: str = "https://images.unsplash.com/photo-1536431311719-398b6704d4cc",
):
    """
    Verify that download_image function successfully downloads the target image. Attempt to open the file
    and verify that file downloaded is in fact an image. Filename should be the basename of the img_url
    provided, with an additional extension based on image type. Expect jpg for tests.
    """

    with open(test_image, "rb") as img:

        mock_get.return_value = mock_response
        mock_response.content = img.read()
        mock_response.url = img_url

    result = runner.invoke(cli, ["--url", img_url, "show"])

    assert result.exit_code == 0


def test_option_quiet(test_image):

    result = runner.invoke(
        cli, ["--file", str(test_image.resolve()), "--quiet", "show"]
    )

    assert result.exit_code == 0


def test_launch_as_command_success(test_image):

    result = run(f"wallsy --file {test_image} _test".split(" "))
    assert result.returncode == 0


def test_launch_as_module_success(test_image):

    # make sure to provide a valid wallsy command or the return code won't be zero
    result = run(f"python3 -m wallsy --file {test_image} _test".split(" "))
    assert result.returncode == 0


def test_launch_as_script_success(test_image):

    result = run(f"python3 src/wallsy/cli.py --file {test_image} _test".split(" "))
    assert result.returncode == 0
