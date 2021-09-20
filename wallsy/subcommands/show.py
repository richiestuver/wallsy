"""
wallsy show

This module defines the 'show' subcommand which displays images in the input stream by 
launching the default image viewer defined by the OS. 
"""

from pathlib import Path

import click

from wallsy.cli_utils.decorators import *


@click.command(name="show")
@make_callback
@make_generator
@catch_errors
@require_file
def cli(file: Path):
    """Show the current image using default image viewer."""

    click.launch(str(file))
    return file
