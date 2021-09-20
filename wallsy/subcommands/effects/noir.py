from pathlib import Path

import click

from wallsy import image_handler
from wallsy.config import config
from wallsy.cli_utils.decorators import *
from wallsy.cli_utils.console import *


@click.command(name="noir")
@make_callback
@make_generator
@catch_errors
@require_file
def cli(file):
    """Apply a noir effect to the image. Currently this only converts image to greyscale. May add
    additional enhancements (e.g. increase contrast) in the future.
    """
    describe(f":detective-emoji:  'noir' applying noir effect to '{file.name}'")

    file = image_handler.greyscale(
        img_path=file,
        path_modifier="noir",
        dest_path=Path(config.WALLSY_EFFECTS_DIR) / file.name,
    )

    confirm_success(
        f":floppy_disk: 'noir' saved image as '{file.name}' in {file.parent}"
    )

    return file
