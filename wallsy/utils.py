import os
import sys
import json
import shutil
from pathlib import Path
from stat import S_ISFIFO
from pathlib import Path
from shutil import copy2, SameFileError
from functools import wraps
from functools import partial
from inspect import getcallargs
from urllib.parse import urlparse

import click
from rich import print

from wallsy import image_handler


class WallsyLoadError(Exception):
    """Raise when loading a resource from file or URL fails."""

    pass


class WallsyConfigError(Exception):
    """Raise when an issue occurs with handling Wallsy configuration."""

    pass


@click.group()
def cli():
    pass


def get_stdin() -> Path:

    # S_ISFIFO determines if the mode (file type and permissions) of a given file descriptor refers to a pipe.
    # 0 is the FD for std in, 1 = stdout, 2 = stderr
    if S_ISFIFO(os.stat(0).st_mode):

        file = Path(sys.stdin.read().strip()).expanduser().resolve()
        print(f"Read file from standard input: {file.name}")

        return Path(file)

    raise OSError("Stdin check: no pipeline detected for standard input.")


def init():
    """initialize the wallsy CLI app"""

    settings: dict = load_config()

    # check for existence of wallsy folder in home dir and create if does not exist
    for path in settings["paths"]:
        path = Path(settings["paths"][path])
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)

    return settings


def load_config():
    """Get configuration settings for Wallsy."""

    config_dir = Path("~/.config/wallsy").expanduser()

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=False)
        generate_config(config_dir)

    try:
        with open(config_dir / "config.json", "r") as config:
            settings: dict = json.load(config)
            # add paths to environment variables
            for item in settings["paths"]:
                os.environ[item] = settings["paths"][item]
            return settings

    except Exception as error:
        raise WallsyConfigError(error)


def load(file=None, url=None) -> Path:
    """
    Retrieve a new image from either local filesystem or URL (must point directly to an accessible image resource).
    """

    # Catch usage errors immediately on invocation.
    # At least one (but not both) of --file or --url are required.
    error_msg = (
        "Provide argument for at least one (and only one) of the following: file, url"
    )
    if file is None and url is None:

        raise WallsyLoadError(error_msg)

    if file is not None and url is not None:

        raise WallsyLoadError(error_msg)

    """set destination path for where the image should be stored. 
    images are intended to be modified so input paths shouldn't be 
    used as the destination path as doing so will modify the original input.
    in the future maybe allow this to be specified as an option to 
    modify the input file. e.g. --no-save"""

    dest_path = Path(os.environ["WALLSY_MEDIA_DIR"])

    """
    FILE option
    """
    if file:

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
            print(f"Copied {file.name} to {dest_path}")
        except SameFileError:
            print(f"{file.name} is already located at {dest_path}")

    """
    URL option
    """
    if url:

        # let's try to prevent as many obviously invalid requests from getting through
        # as is realistically possible.

        # if there is no path component to the url, the provided url is
        # (almost) certainly not a direct link to an image resource.
        # e.g. https://example.com/  -> path is ""
        #      https://example.com/mycat.jpg  -> path is /mycat.jpg
        if urlparse(url).path in ("", "/"):
            raise WallsyLoadError(
                "Please specify a link directly to an image resource."
            )

        file_name = Path(urlparse(url).path).name

        try:
            print(f"Grabbing an image from {url}...")
            dest_path = image_handler.download_image(
                url=url, file_path=dest_path / file_name
            )
            print(f"Downloaded image to {dest_path}")
        except image_handler.ImageDownloadError as error:
            raise WallsyLoadError(str(error))
        except image_handler.InvalidImageError as error:
            raise WallsyLoadError(str(error))
        except Exception as error:
            raise WallsyLoadError(f"Something unexpected happened: {error}")

    # if we get this far, we should have a validated image. make the path available to other
    # subcommands by storing in the click context's object attribute (which is designed for this purpose)

    return dest_path


def generate_config(config_dir):
    """Create a new config file at appropriate location if one is not detected"""

    # storage for user generated wallsy media
    wallsy_media = Path("~/wallsy").expanduser()

    # save location for wallpapers when updating desktop wallpapers
    wallpaper_location = Path("~/.local/share/backgrounds").expanduser()

    with open(config_dir / "config.json", "w") as config:

        config_data = {
            "paths": {
                "WALLSY_CONFIG_DIR": str(config_dir),
                "WALLSY_MEDIA_DIR": str(wallsy_media),
                "WALLSY_WALLPAPER_DIR": str(wallpaper_location),
                "WALLSY_EFFECTS_DIR": str(wallsy_media / "effects"),
            }
        }

        config_json = json.dump(config_data, config)


@cli.command()
def reset():
    """remove wallsy folders and files from the config directory as part of an uninstall"""

    load_config()
    shutil.rmtree(os.environ["WALLSY_CONFIG_DIR"])


"""
DECORATORS
"""


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
        def wrapper(*fargs, **fkwargs):
            new_func = partial(func, *args, **kwargs)
            return new_func(*fargs, **fkwargs)

        return wrapper

    return callback


def require_file(func):
    """
    Decorator for callbacks that require a filename to be explicitly passed in order to perform
    desired action. This decorator abstracts checking for this parameter and raises the necessary exception.
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
