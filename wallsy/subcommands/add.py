from pathlib import Path
from urllib.parse import urlparse

from wallsy.cli_utils.utils import load

from wallsy.cli_utils.decorators import callback
from wallsy.cli_utils.decorators import stream
from wallsy.cli_utils.decorators import catch_errors

import click


@click.command(name="add")
@click.option(
    "--file",
    "-f",
    "files",
    type=click.Path(
        path_type=Path
    ),  # make sure that file paths are always Path objects.
    help="Load an image from file path. Ensures image is valid and stores a copy of the image in the Wallsy folder.",
    multiple=True,
)
@click.option("--url", "-u", "urls", type=str, multiple=True)
@callback
@stream
@catch_errors
def cli(files: list[Path] = None, urls: list[str] = None):
    """
    Add a copy of image to the Wallsy folder. Useful for things like random --local and image management. Use as part of a pipeline
    or specify a file / url manually.
    """

    if files:
        for file in files:
            yield load(file)

    elif urls:
        for url in urls:
            yield load(urlparse(url))

    else:
        raise click.UsageError(
            "'add' recieved nothing from stdin and no file or url specified."
        )
