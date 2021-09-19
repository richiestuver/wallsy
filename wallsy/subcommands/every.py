from time import sleep

import click

from wallsy.cli_utils.utils import WallsyData
from wallsy.cli_utils.console import *


@click.command(name="every")
@click.argument("interval", type=int)
def cli(interval):
    """Set wallsy to repeat this action on an interval"""

    # custom callback generator function that passes through the OG file after an interval delay
    def wrapper(stream: WallsyData):
        def _repeat(file):
            describe(f"sleeping {interval}s...")
            sleep(interval)
            return file

        stream.repeat = True
        stream.stream = (_repeat(file) for file in stream.stream)
        return stream

    return wrapper
