from pathlib import Path

from wallsy import image_handler
from wallsy.cli_utils.decorators import *
from wallsy.cli_utils.console import *

import click


@click.command(name="noir")
@make_callback
@make_generator
@catch_errors
@click.pass_obj
@require_file
def cli(obj, file):
    """Apply a noir effect to the image. Currently this only converts image to greyscale. May add
    additional enhancements (e.g. increase contrast) in the future.
    """
    describe(f":detective-emoji:  'noir' applying noir effect to '{file.name}'")

    file = image_handler.greyscale(
        img_path=file,
        path_modifier="noir",
        dest_path=Path(obj.config.WALLSY_EFFECTS_DIR) / file.name,
    )

    confirm_success(
        f":floppy_disk: 'noir' saved image as '{file.name}' in {file.parent}"
    )

    return file
