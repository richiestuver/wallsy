import os
import sys
import json
import shutil
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from stat import S_ISFIFO
from itertools import chain
from pathlib import Path
from shutil import copy2, SameFileError
from functools import wraps
from functools import partial
from inspect import getcallargs
from urllib.parse import urlparse
from collections.abc import Iterator, Iterable
import inspect

import click
from rich import print

from wallsy import image_handler

from wallsy.config import WallsyConfig
from wallsy.config import WallsyConfigError
from wallsy.config import load_config

from wallsy.console import console
from wallsy.console import error_console
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


def load_url(url: str):
    """ """

    config = load_config()
    dest_path = config.WALLSY_MEDIA_DIR

    # let's try to prevent as many obviously invalid requests from getting through
    # as is realistically possible.

    # if there is no path component to the url, the provided url is
    # (almost) certainly not a direct link to an image resource.
    # e.g. https://example.com/  -> path is ""
    #      https://example.com/mycat.jpg  -> path is /mycat.jpg
    if urlparse(url).path in ("", "/"):
        raise WallsyLoadError("please specify a link directly to an image resource.")

    file_name = Path(urlparse(url).path).name
    describe(f":earth_asia-emoji: 'wallsy' getting image from {url} ...", end=" ")
    try:
        dest_path = image_handler.download_image(
            url=url, file_path=dest_path / file_name
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


def load_file(file=None):
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
        # inspect.getouterframes(inspect.currentframe())[1]
        # inspect.currentframe().f_back.f_code
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
        frame = inspect.currentframe()

    except Exception as error:
        raise UserWarning(
            "There was an error trying to find out the caller function for pretty printing a message."
        )

    else:
        """
        I don't love this, but we have a list of frames where the 0th index is get_caller_func,
        the 1st index is the caller of get_caller_func,
        and 2nd index is the caller of the caller (presumably the name of the function you want)
        """
        return inspect.getouterframes(frame)[index].function

    finally:
        del frame


@cli.command()
def reset():
    """remove wallsy folders and files from the config directory as part of an uninstall"""

    load_config()
    shutil.rmtree(os.environ["WALLSY_CONFIG_DIR"])


"""
DECORATORS
"""


def extend_stream(func):
    """
    Take a function that generates output(s) (or passes through new input(s) directly as an output)
    and extend an existing stream to include these new outputs. This allows functions that don't operate
    on received input to instead provide new inputs to a pipeline.
    """

    @wraps(func)
    def wrapper(input_stream, *args, **kwargs):
        def inner():
            yield func(input_stream, *args, **kwargs)

        yield from chain(input_stream, inner())

    return wrapper


def make_generator(func):
    """
    Take a function that accepts and returns a single input parameter and convert it into
    a function that accepts an input stream and yields the return value of the original function.
    """

    @wraps(func)
    def wrapper(input_stream, *args, **kwargs):

        for input in input_stream:
            yield func(input, *args, **kwargs)

    return wrapper


def make_callback(func):
    """
    Receive a function (presumably, that does not itself return a function) and convert it into a new function that returns the
    original function as a callback function.

    The Wallsy CLI is built on a callback architecture. Subcommands are invoked on the command line, each of which return a callback function
    immediately upon invocation. Once all subcommands have been invoked, a separate "process callbacks" function iterates over each of the callback
    function objects and executes them. When a function is decorated with make_callback, the callback itself will have the
    same signature and behave exactly as the original function. The invoking the origianl function name, on the otherhand, merely returns the callback
    which now must be invoked to actually execute the original function body.

    It is possible to achieve the same behavior by manually defining an inner function within each subcommand function definition. Similar to:

        def my_command(cli_args):  # any args received from command line invocation

            # any actions that would be performed immediately upon command invocation here

            def my_callback(callback_args)  # any args required for callback but not supplied directly on command line

                # body of command logic in here, processed by callback processor at a later time

                return whatever_you_need_to_for_other_command_callbacks_etc

            return my_callback

    However, the benefit to using the callback factory pattern here is that it eliminates all of the boilerplate code for doing so and reduces the
    function body to only the logic necessary for performing the desired action of the command itsef.
    """

    @wraps(func)
    def callback(*args, **kwargs):
        @wraps(func)
        def wrapper(*fargs, **fkwargs):
            new_func = partial(func, *args, **kwargs)
            return new_func(*fargs, **fkwargs)

        return wrapper

    return callback


def require_file(func):
    """
    Decorator for callbacks that require a filename to be explicitly passed in order to perform
    desired action. This decorator abstracts checking for this parameter and raises the necessary exception.

    NOTE: getcallargs is deprecated, need to move to signature() call instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_args = getcallargs(func, *args, **kwargs)
        if func_args.get("file") is None:
            raise click.ClickException(
                f"Command '{func.__name__}' did not receive a filename as part of pipeline. Did you run 'add' or 'random' to source an image?"
            )
        return func(*args, **kwargs)

    return wrapper


def catch_errors(func):
    """
    Catch and format errors with the "fail" console template and gracefully
    exit the application with an error code.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            fail(str(error))
            exit(1)

    return wrapper
