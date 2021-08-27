import os
import sys
import json
import shutil
from pathlib import Path
from stat import S_ISFIFO
from pathlib import Path
from shutil import copy2, SameFileError
from functools import wraps
from inspect import getcallargs
from urllib.parse import urlparse

import click

import wallsy.image_handler as image_handler


@click.group()
def cli():
    pass


def get_stdin() -> Path:

    # S_ISFIFO determines if the mode (file type and permissions) of a given file descriptor refers to a pipe.
    # 0 is the FD for std in, 1 = stdout, 2 = stderr
    if S_ISFIFO(os.stat(0).st_mode):

        file = Path(sys.stdin.read().strip())
        click.echo(f"Read file from standard input: {file.name}")

        return Path(file)

    raise OSError("Stdin check: no pipeline detected for standard input.")


def init():
    """initialize the wallsy CLI app"""

    settings = load_config()

    # check for existence of wallsy folder in home dir and create if does not exist
    wallsy_location = Path(settings["WALLSY_CONFIG_DIR"])
    if not wallsy_location.exists():
        wallsy_location.mkdir(parents=True, exist_ok=False)

    return settings


def load_config():
    """Get configuration settings for Wallsy."""

    config_dir = Path("~/.config/wallsy").expanduser()

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=False)
        generate_config(config_dir)

    try:
        with open(config_dir / "config.json", "r") as config:
            settings = json.load(config)
            for item in settings:
                os.environ[item] = settings[item]
            return settings

    except Exception as error:
        raise click.ClickException(error)


def load_file(file=None, url=None) -> Path:
    """
    Retrieve a new image from either local filesystem or URL (must point directly to an accessible image resource).
    """

    # Catch usage errors immediately on invocation.
    # At least one (but not both) of --file or --url are required.
    if file is None and url is None:
        msg = """Wallsy requires either a file path or url pointing to an image. Please provide either --file or --url options. 
        
        file: wallsy load --file="/path/to/my/photo.jpg"
        url:  wallsy load --url="https://www.example.com/myphoto.jpg"
        """
        raise click.ClickException(msg)

    if file is not None and url is not None:
        msg = """Wallsy received conflicting options: --file and --url. Please choose one option and try again. 
        """

        raise click.UsageError(msg)

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
        file = Path(file)
        dest_path = dest_path / file.name

        # validate that the input file is a valid image.
        try:
            image_handler.validate_image(file)

        except image_handler.InvalidImageError as error:
            raise click.BadParameter(str(error))

        # copy the file contents to destination
        try:
            # Note that copy2 attempts to preserve metedata, other copy funcs in shutil do not
            copy2(file, dest_path)
            click.echo(f"Copied {file.name} to {dest_path}")
        except SameFileError:
            click.echo(f"{file.name} is already located at {dest_path}")

    """
    URL option
    """
    if url:

        file_name = Path(urlparse(url).path).name

        try:
            dest_path = image_handler.download_image(
                url=url, file_path=dest_path / file_name
            )
            click.echo(f"Downloaded image to {dest_path}")
        except image_handler.ImageDownloadError as error:
            raise click.ClickException(str(error))
        except image_handler.InvalidImageError as error:
            raise click.BadParameter(str(error))

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
            "WALLSY_CONFIG_DIR": str(config_dir),
            "WALLSY_MEDIA_DIR": str(wallsy_media),
            "WALLSY_WALLPAPER_DIR": str(wallpaper_location),
        }

        config_json = json.dump(config_data, config)


@cli.command()
def reset():
    """remove wallsy folders and files from the config directory as part of an uninstall"""

    load_config()
    shutil.rmtree(os.environ["wallsy_config_location"])

def require_filename(func):
    """
    Decorator for callbacks that require a filename to be explicitly passed in order to perform
    desired action. This decorator abstracts checking for this parameter and raises the necessary exception. 
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_args = getcallargs(func, *args, **kwargs)
        if func_args.get('filename') is None:
            raise click.ClickException(f"{func.__name__} did not receive a filename as part of pipeline. Did you run 'load' or 'random' to source an image?")
        return func(*args, **kwargs)

    return wrapper