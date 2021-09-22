"""
wallsy test
"""

from pathlib import Path
from typing import Union

import click
from PIL import Image, ImageFilter, ImageOps, ImageColor

from wallsy import image_handler

from wallsy.config import config

from wallsy.cli_utils.console import describe
from wallsy.cli_utils.console import confirm_success

from wallsy.cli_utils.decorators import require_file
from wallsy.cli_utils.decorators import callback
from wallsy.cli_utils.decorators import generator
from wallsy.cli_utils.decorators import catch_errors


@click.command(name="colorize")
@click.option(
    "--dark",
    default=("midnightblue"),
    help="Speficy a color name or RGB value to replace dark areas with.",
)
@click.option(
    "--light",
    default="white",
    help="Specify a color name or RGB value to replace light areas with.",
)
@callback
@generator
@catch_errors
@require_file
def cli(file: Path, dark, light):
    """
    Apply a Gaussian blur effect to image. Default pixel radius for blur is 5.

    Note that Click handles exceptions in cases where invalid input is provided for radius (default value and type provided).
    """

    describe(
        f":paintbrush-emoji:  'colorize' changing dark areas to {dark} and light areas to {light}..."
    )
    file = image_handler.colorize(file, dark, light)
    confirm_success(
        f":floppy_disk-emoji: 'colorize' saved to {file.name} in {file.parent}"
    )

    return file
