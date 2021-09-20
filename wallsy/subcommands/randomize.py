"""
wallsy random

This module defines the 'random' subcommand, which permits the user to grab a random image either from 
a local directory or online (source: Unsplash).
"""


from random import sample
from urllib.parse import urlparse

import click

from wallsy.cli_utils.utils import load
from wallsy.config import config
from wallsy.cli_utils.decorators import make_callback
from wallsy.cli_utils.decorators import extend_stream
from wallsy.cli_utils.decorators import catch_errors

from wallsy.cli_utils.console import confirm_success

from wallsy import unsplash_handler


@click.command(name="random")
@click.option(
    "--keyword",
    "-q",
    multiple=True,
    help="Specify keyword to refine random results. Can use multiple times e.g. random -q pizza -q lemon",
)
@click.option(
    "--size",
    "-s",
    "dimensions",
    type=(int, int),
    help="(--online only) specify dimensions of the image to retrieve, e.g. -s 1920 1080",
)
@click.option(
    "--local/--online",
    is_flag=True,
    show_default=True,
    default=False,
    help="Grab an image from Unsplash or locally from your wallsy folder.",
)
@click.option(
    "--count",
    type=int,
    help="Number of random images to get",
    default=1,
    show_default=True,
)
@make_callback
@extend_stream
@catch_errors
def cli(keyword, dimensions, local, count):
    """
    Generate a random image from source (default: Unsplash).
    """

    """
    'random' is a generator that yields user's desired number of images. when the 'extend_stream' decorator is
    applied, this generator is effectively appended to the end of the existing input stream.

    If random is specified somewhere in the middle of a chain
    of commands, the current behavior is to "ignore" input all previous commands and generate a new file as usual.
    While probably unintended usage, this could have limited utility in the case a user wants to perform processing on a small
    finite number of files in a single line on the terminal.
    """

    for _ in range(count):

        file = None

        if local:

            img_set = list(config.WALLSY_MEDIA_DIR.iterdir())
            file = sample(img_set, 1)[0].resolve()
            confirm_success(
                f":game_die-emoji: 'random' grabbed '{file.name}' from {config.WALLSY_MEDIA_DIR}"
            )

        else:
            url = unsplash_handler.random_featured_photo(
                keywords=keyword if keyword else None,
                dimensions=dimensions if dimensions else None,
            )
            file = load(urlparse(url))

        yield file
