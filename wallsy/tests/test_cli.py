"""
Test the CLI driver for Wallsy

cli.py is the entry point for the wallsy program. verify that standard
invokation returns with correct exit code on success or failure.
"""

from subprocess import run

import pytest
import click
from click.testing import CliRunner

from wallsy.cli import cli

from wallsy.cli_utils.utils import import_commands
from wallsy.cli_utils.utils import attach_commands

runner = CliRunner()


@pytest.fixture(scope="module")
def subcommands():
    """
    Import and attach all of the commands found in the /subcommands folder *without*
    invoking the entrypoint (cli).
    """

    # setup

    cmds = import_commands()

    @click.command(name="_test")
    def test_command(*args, **kwargs):
        print("TEST COMMAND - I am a functioning command.")

    cmds.append(test_command)

    return cmds


@pytest.fixture(autouse=True)
def setup(subcommands, reset_commands, entry_point: click.Group = cli):
    attach_commands(entry_point, subcommands)
    yield
    reset_commands(entry_point=entry_point)


@pytest.fixture
def reset_commands():
    def inner(entry_point: click.Group = cli):
        # teardown the commands that may have been added to clean the test environment.
        entry_point.commands = {}

    return inner


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


def test_launch_as_script_success(test_image):

    result = run(f"wallsy --file {test_image} _test".split(" "))
    assert result.returncode == 0
