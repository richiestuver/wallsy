import os
import sys
import json
import shutil
from pathlib import Path
from stat import S_ISFIFO
from pathlib import Path
from shutil import copyfile

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
