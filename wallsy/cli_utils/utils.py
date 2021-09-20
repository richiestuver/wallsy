"""
wallsy CLI Utilities

This module contains utilities for working across Click subcommands and operations on common 
I/O data for those commands, such as: getting filepaths from standard input, retrieving and saving filepaths or urls, and importing subcommands
from directories.
"""


import os
import sys
import shutil
import inspect
import importlib.util

from stat import S_ISFIFO
from functools import singledispatch
from pathlib import Path
from urllib.parse import ParseResult
from collections.abc import Iterable

import click

import wallsy.cli_utils

from wallsy import image_handler
from wallsy.config import config
from wallsy.cli_utils.console import *


class WallsyLoadError(Exception):
    """Raise when loading a resource from file or URL fails."""

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
    """
    Load a file or url for use by additional subcommands in the wallsy image pipeline. Note that urls must be
    passed by providing the result of urllib.parse.urlparse(url). Files should be passed as pathlib.Path objects.
    """

    raise Exception(
        f"load was called incorrectly with argument: {file} of type f{type(file)}"
    )


@load.register
def _load_url(url: ParseResult) -> Path:
    """
    Private. This function is called when 'load' dispatcher receives the result of a urllib.parse.urlparse()
    call as its first argument.
    """

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
def _load_file(file: Path) -> Path:
    """
    Private. This function is called when the 'load' dispatcher receives a Path object as its first argument.
    """

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
        shutil.copy2(file, dest_path)
        confirm_success(
            f":floppy_disk-emoji: '{get_caller_func_name()}' saved '{dest_path.name}' to {dest_path.parent}"
        )
    except shutil.SameFileError:
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
        frame = inspect.currentframe()

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
        return inspect.getouterframes(frame)[index].function

    # according to the inspect module docs, it's important to cleanup references to frame objects
    # after they are done being used due to hanging around in memory afterward.

    finally:
        del frame


def import_commands(
    module_paths: Iterable = Path(wallsy.__file__).parent.rglob(
        "**/subcommands/**/*.py"
    ),
) -> list[click.Command]:
    """
    Retrieve a set of click Commands from module_paths. Default directory is the built in subcommands
    directory for commands that come pre-installed with Wallsy.


    A valid wallsy command should define a "cli" function that is wrapped as
    a click Command object. This function will be exposed as a command to the end user.
    Set the 'name' keyword argument in the @click.command decorator to set the
    name of the command intended for the end user.

    """

    commands = []

    for path in module_paths:
        name = inspect.getmodulename(path)
        if name != "__init__":

            # Recipe for loading and executing modules from given filepath
            # comes from importlib docs:
            # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly

            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

            try:
                cli = getattr(module, "cli")
                commands.append(cli)

            except AttributeError:
                warn(f"Cannot add command {name}: no 'cli' function found.")

    return commands


def attach_commands(group: click.Group, commands: list[click.Command]):
    """
    Attach each command in a list of click Command objects to a provided group. Useful when
    retrieving a dynamic list of subcommands with import_commands().
    """

    for command in commands:
        group.add_command(command)
