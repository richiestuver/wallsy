"""
wallsy blur

This module defines the 'blur' subcommand which adds a blur effect to images in the input stream.
"""

from pathlib import Path

import click

from wallsy import image_handler

from wallsy.config import config

from wallsy.cli_utils.console import describe
from wallsy.cli_utils.console import confirm_success

from wallsy.cli_utils.decorators import require_file
from wallsy.cli_utils.decorators import callback
from wallsy.cli_utils.decorators import generator
from wallsy.cli_utils.decorators import catch_errors


@click.command(name="blur")
@click.option(
    "--radius",
    default=5,
    show_default=True,
    help="Specify the pixel radius for blur effect.",
)  # note that click options are passed to the decorated command as keyword arguments. so should be specified after positional in the signature
@callback
@generator
@catch_errors
@require_file
def cli(file: Path, radius):
    """
    Apply a Gaussian blur effect to image. Default pixel radius for blur is 5.

    Note that Click handles exceptions in cases where invalid input is provided for radius (default value and type provided).
    """

    describe(
        f":blue_circle-emoji: 'blur' applying blur to '{file.name}' with radius"
        f" {radius}.."
    )

    file = image_handler.blur(
        file,
        radius=int(radius),
        dest_path=Path(config.WALLSY_EFFECTS_DIR) / file.name,
    )

    confirm_success(
        f":floppy_disk-emoji: 'blur' saved image as '{file.name}' in {file.parent}"
    )

    return file
