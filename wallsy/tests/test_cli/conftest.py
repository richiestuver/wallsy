"""
conftest.py

Test configuration for CLI and entrypoint tests.

Defines pytest fixtures specifically related to CLI and click operations.
"""


import pytest
import click

from wallsy.cli import cli
from wallsy.cli_utils.utils import import_commands
from wallsy.cli_utils.utils import attach_commands
from wallsy.cli_utils.decorators import generator
from wallsy.cli_utils.decorators import callback


@pytest.fixture(scope="session")
def subcommands():
    """
    Import and attach all of the commands found in the /subcommands folder *without*
    invoking the entrypoint (cli).
    """

    # setup

    cmds = import_commands()

    @click.command(name="_test")
    @callback
    @generator
    def test_command(file, *args, **kwargs):

        print("TEST COMMAND - I am a functioning command.")
        return file

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
