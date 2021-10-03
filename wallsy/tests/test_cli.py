"""
Test the CLI driver for Wallsy

cli.py is the entry point for the wallsy program. verify that standard
invokation returns with correct exit code on success or failure.
"""

import pytest
import click
from click.testing import CliRunner

from wallsy.cli import cli
from wallsy.cli_utils.utils import import_commands
from wallsy.cli_utils.utils import attach_commands

runner = CliRunner()


@pytest.fixture
def subcommands(entry_point: click.Group = cli):
    """
    Import and attach all of the commands found in the /subcommands folder *without*
    invoking the entrypoint (cli).
    """

    # setup

    cmds = import_commands()
    attach_commands(cli, cmds)

    yield cli

    # teardown
    cli.commands = {}


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


def test_option_file_single_success(test_image, cli=subcommands):
    result = runner.invoke(cli, ["--file", str(test_image.resolve()), "show"])

    print("OUTPUT:", result.stdout)

    assert result.exit_code == 0


def test_option_quiet(test_image, cli=subcommands):

    result = runner.invoke(cli, ["--file", str(test_image.resolve()), "show"])

    print("OUTPUT:", result.stdout)
    assert result.exit_code == 0


def test_no_commands():

    assert cli.commands == {}
