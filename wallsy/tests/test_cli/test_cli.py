"""
Test the CLI driver for Wallsy

cli.py is the entry point for the wallsy program. verify that standard
invokation returns with correct exit code on success or failure.
"""

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

    assert result.exit_code == 0


def test_option_quiet(test_image):

    result = runner.invoke(
        cli, ["--file", str(test_image.resolve()), "--quiet", "show"]
    )

    assert result.exit_code == 0
