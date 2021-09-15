import os
import sys
import shutil

from dataclasses import dataclass

from stat import S_ISFIFO
from itertools import chain
from shutil import copy2, SameFileError

from functools import singledispatch

from inspect import getouterframes
from inspect import currentframe

from pathlib import Path

from urllib.parse import ParseResult

from collections.abc import Iterable

import click
from rich import print

from wallsy import image_handler

from wallsy.config import WallsyConfig
from wallsy.config import load_config

from wallsy.console import describe
from wallsy.console import warn
from wallsy.console import fail
from wallsy.console import confirm_success


class WallsyLoadError(Exception):
    """Raise when loading a resource from file or URL fails."""

    pass


@dataclass
class WallsyData:
    """
    Used to store application data for purpose of passing around subcommands. Currently stores the
    existing config settings (contains common directories) and the initial input file stream.
    """

    config: WallsyConfig
    stream: Iterable = ()  # empty iterator
    repeat: bool = False
    interval: int = 0


@click.group()
def cli():
    pass


def yield_stdin():
    """
    Check for a pipeline by reading the file handler for standard input and read the content
    if there are values on this stream. Yield these values as Path objects.
    """

    # S_ISFIFO determines if the mode (file type and permissions) of a given file descriptor refers to a pipe.
    # 0 is the FD for std in, 1 = stdout, 2 = stderr
    if S_ISFIFO(os.stat(0).st_mode):
        describe(f":arrow_right-emoji: 'wallsy' got input stream from standard input")
        for line in sys.stdin:
            yield Path(line.strip()).expanduser().resolve()

    else:
        warn("no pipeline detected for standard input")
        return


@singledispatch
def load(file) -> Path:
    raise Exception(
        f"load was called incorrectly with argument: {file} of type f{type(file)}"
    )


@load.register
def load_url(url: ParseResult) -> Path:
    """ """

    config = load_config()
    dest_path = config.WALLSY_MEDIA_DIR

    # let's try to prevent as many obviously invalid requests from getting through
    # as is realistically possible.

    # if there is no path component to the url, the provided url is
    # (almost) certainly not a direct link to an image resource.
    # e.g. https://example.com/  -> path is ""
    #      https://example.com/mycat.jpg  -> path is /mycat.jpg
    if url.path in ("", "/"):
        raise WallsyLoadError("please specify a link directly to an image resource.")

    file_name = Path(url.path).name
    describe(
        f":earth_asia-emoji: '{get_caller_func_name()}' getting image from {url.geturl()} ...",
        end=" ",
    )
    try:
        dest_path = image_handler.download_image(
            url=url.geturl(), file_path=dest_path / file_name
        )
    except image_handler.ImageDownloadError as error:
        raise WallsyLoadError(str(error))
    except image_handler.InvalidImageError as error:
        raise WallsyLoadError(str(error))
    except Exception as error:
        raise WallsyLoadError(f"something unexpected happened: {error}")

    # if we get this far, we should have a validated image. make the path available to other
    # subcommands by storing in the click context's object attribute (which is designed for this purpose)

    confirm_success(
        f":white_check_mark-emoji: \n:floppy_disk: '{get_caller_func_name()}' saved '{dest_path.name}' to {dest_path.parent}"
    )
    return dest_path


@load.register
def load_file(file: Path) -> Path:
    """ """

    config = load_config()
    dest_path = config.WALLSY_MEDIA_DIR

    # if file is not a Path, (can also be str or TextIOBuffer), convert to Path
    file = Path(file).expanduser().resolve()
    dest_path = dest_path / file.name

    # validate that the input file is a valid image.
    try:
        image_handler.validate_image(file)

    except image_handler.InvalidImageError as error:
        raise WallsyLoadError(str(error))

    # copy the file contents to destination
    try:
        # Note that copy2 attempts to preserve metedata, other copy funcs in shutil do not
        copy2(file, dest_path)
        confirm_success(
            f":floppy_disk-emoji: '{get_caller_func_name()}' saved '{dest_path.name}' to {dest_path.parent}"
        )
    except SameFileError:
        warn(f"'{file.name}' is already located at {dest_path.parent}")

    # if we get this far, we should have a validated image. make the path available to other
    # subcommands by storing in the click context's object attribute (which is designed for this purpose)

    return dest_path


def get_caller_func_name(index=2) -> str:
    """
    Return the name of the function that the caller of this utility function was called by. Typical use case is
    for logging and printing the subcommand name (which matches the func name by Wallsy design) instead of
    the caller's name.
    """

    try:
        frame = currentframe()

    except Exception as error:
        raise UserWarning(
            f"There was an error trying to find out the caller function for pretty printing a message: {error}"
        )

    else:
        """
        I don't love this, but we have a list of frames where the 0th index is get_caller_func,
        the 1st index is the caller of get_caller_func,
        and 2nd index is the caller of the caller (presumably the name of the function you want)
        """
        return getouterframes(frame)[index].function

    # according to the inspect module docs, it's important to cleanup references to frame objects
    # after they are done being used due to hanging around in memory afterward.

    finally:
        del frame


@cli.command()
def reset():
    """remove wallsy folders and files from the config directory as part of an uninstall"""

    load_config()
    shutil.rmtree(os.environ["WALLSY_CONFIG_DIR"])
