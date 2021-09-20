"""
wallsy every

This module defines the "every" command, which allows the user to schedule the inputted
sequence of subcommands on a repeating interval. The most common use case is to update
the desktop wallpaper on a regular period (e.g. every hour) but other creative use cases exist.
"""

from time import sleep

import click

from wallsy.WallsyStream import WallsyStream
from wallsy.cli_utils.console import describe


@click.command(name="every")
@click.argument("interval", type=int)
def cli(interval):
    """Set wallsy to repeat this action on an interval"""

    # custom callback generator function that passes through the OG file after an interval delay
    def wrapper(stream: WallsyStream):
        def _repeat(file):
            describe(f"Waiting {interval}s for next action...")
            sleep(interval)
            return file

        stream.repeat = True
        stream.stream = (_repeat(file) for file in stream.stream)
        return stream

    return wrapper
