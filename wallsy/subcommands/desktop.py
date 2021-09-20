"""
Desktop Commands
"""

from pathlib import Path
from shutil import copy2
from functools import singledispatch
from collections.abc import Generator

import click

from wallsy import wallpaper_handler

from wallsy.WallsyStream import WallsyStream
from wallsy.config import config
from wallsy.cli_utils.console import *
from wallsy.cli_utils.decorators import *
from wallsy.cli_utils.utils import *


@click.command(name="desktop")
@make_callback
def cli(stream: WallsyStream):
    """
    Set your desktop background or use your current desktop as a source image.
    """

    """
    The desktop command supports two modes: operating on the current stream (setting 
    the desktop background as a side effect) or supplying additional image(s) to the 
    stream (retrieving the filepath of the current desktop background). 

    This is made possible by evaluating the state of the generator represented by the stream
    and determining if the generator is both empty and never supplied any items. We are sort 
    of abusing the StopIteration behavior of generators to accomplish this because there is not
    a simple "is empty" style function call to get the state of the underlying iterator.

    In a future refactor, we might be able to assess this without the try/except block by
    making a call to inspect.getgeneratorlocals() and seeing if the dict that is returned as
    the first argument is empty. 

    For now, we check the state of a variable holding Path items retrieved from the stream generator
    to determine our condition. If StopIteration is raised no items were pulled from the generator
    then we execute the version of the desktop command that supplies additional items to the stream for 
    use in subsequent subcommands. 

    The dispatching logic is greatly simplified (read: abstracted partly away from this Click controller)
    by the functools @singledispatch decorator. Rather than doing this by hand, the logic here purely pertains 
    to how to determine the appropriate condition and then passing a variable argument type (either 
    a single Path object or the generator itself) to the dispatcher.

    Note that the inspect.getgeneratorstate(<generator_object...>) is insanely helpful for debugging 
    code that works with generators.
    """

    def dispatch(stream: Generator):
        """
        Evaluate the state of stream and pass arguments to the desktop dispatcher accordingly. If the stream
        is not exhausted, yield the next value from the stream. If the stream is exhausted, instead pass the empty
        generator to _desktop and receive the current desktop image instead.
        """

        file = None

        try:
            while file := next(stream):
                yield _desktop(file)

        except StopIteration:
            # the stream was emtpy at the beginning of iteration, meaning user intends to retrieve the current desktop
            if file is None:
                yield _desktop(stream)

    stream.stream = dispatch(stream.stream)
    return stream


@singledispatch
def _desktop(arg):
    """
    Callback for the desktop command. This function is a dispatcher that
    calls out to different helper functions depending on the argument type
    retrieved. Passing in a Path object should set the desktop background.
    Passing in a Generator object should extend the iterator by including the
    retrieving the current desktop wallpaper path and appending it to the
    iterator items.
    """

    raise UserWarning(f"_desktop received an invalid argument for {__name__}: {arg}")


@_desktop.register(Path)
def _set_desktop(file: Path):
    """
    Called by _desktop dispatcher to set the desktop wallpaper.
    """

    wallpaper_dir = config.WALLSY_WALLPAPER_DIR

    if not Path(wallpaper_dir / file.name).exists():

        # note: copy2 attempts to preserve file metadata. other copy functions in shutil do not do so
        copy2(file, wallpaper_dir / file.name)
        describe(
            f":desktop_computer-emoji:  'desktop' added a copy of '{file.name}' to {wallpaper_dir}"
        )

    else:
        warn(f"'{file.name}' is already located at {wallpaper_dir}")

    wallpaper_handler.update_wallpaper(img_path=wallpaper_dir / file.name)
    confirm_success(
        f":white_check_mark-emoji: 'desktop' updated wallpaper to {wallpaper_dir / file.name}"
    )

    return file


@_desktop.register(Generator)
def _get_desktop(*args):
    """
    Called by _desktop dispatcher to retrive the current wallpaper. The input argument stream is used for
    dispatching purposes and should represent an empty generator. The generator is ignored and a new file
    representing the current desktop is returned.
    """

    file = wallpaper_handler.get_current_wallpaper()
    describe(
        f":desktop_computer-emoji: 'desktop' retrieved current background '{file}'"
    )
    file = load(file)

    return file
