"""
wallsy Configuration Management

This file handles utitilities related to generating and loading variables from a configuration file.
WallsyConfig should be loaded at startup in some kind of initialization procedure performed before 
any attempt at command processing is done. Raise a WallsyConfigError for any issues that arise in 
processing or retrieving these configuration variables.

The configuration file is "config.json" and for Ubuntu (current development target) this is saved
at ~/.config/wallsy/config.json as per modern Linux app development conventions (compare to 
~/.wallsy/config.json which is still a relatively prevalent pattern). 
"""

import json
import os
from dataclasses import dataclass
from dataclasses import asdict
from pathlib import Path, PosixPath


class WallsyConfigError(Exception):
    """Raise when an issue occurs with handling Wallsy configuration."""

    pass


class PathEncoder(json.JSONEncoder):
    """
    custom encoder adds support for serializing pathlib objects as strings
    """

    def default(self, o):
        if isinstance(o, PosixPath):
            return str(o)

        else:
            return json.JSONEncoder.default(self, o)


@dataclass
class WallsyConfig:
    """
    Dataclass to represent configuration variables for wallsy. Provides a namespace and identifiers
    for directories on the filesystem that are frequently used by Wallsy.

    The pattern applied is to instantiate a WallsyConfig by supplying variadic keyword arguments from
    a deserialized json object. That way wallsy application code can reference the identifiers in the
    WallsyConfig dataclass without ever touching brittle dictionary keys or directly referencing
    filesystem paths. For simplicity the json object should be fully flat and avoid nested data structures
    as much as possible.
    """

    WALLSY_CONFIG_DIR: Path = Path("~/.config/wallsy").expanduser().resolve()
    WALLSY_MEDIA_DIR: Path = Path("~/wallsy").expanduser().resolve()
    WALLSY_WALLPAPER_DIR: Path = (
        Path("~/.local/share/backgrounds").expanduser().resolve()
    )
    WALLSY_EFFECTS_DIR: Path = WALLSY_MEDIA_DIR / "effects"

    def __post_init__(self):
        """
        Handle the case where a new WallsyConfig is created from JSON, which cannot
        deserialize a str into a Path.

        __post_init__ is called automatically by the generated __init__ method created
        when the dataclass is constructed.
        """

        # note: do we need to add check for path type here? that returns PosixPath and not Path usually.

        self.WALLSY_CONFIG_DIR = Path(self.WALLSY_CONFIG_DIR)
        self.WALLSY_MEDIA_DIR = Path(self.WALLSY_MEDIA_DIR)
        self.WALLSY_WALLPAPER_DIR = Path(self.WALLSY_WALLPAPER_DIR)
        self.WALLSY_EFFECTS_DIR = Path(self.WALLSY_EFFECTS_DIR)

    def generate_config_json(self) -> Path:
        """
        Write the WallsyConfig to file, serializing to JSON. Returns filepath of written
        config.json file which *should* be located at WALLSY_CONFIG_DIR.

        Warning: will overwrite any existing config file for Wallsy, by design.
        """

        # serialize to json and report any errors

        try:
            to_json = json.dumps(
                asdict(self), sort_keys=True, indent=4, cls=PathEncoder
            )

        except TypeError as error:
            raise WallsyConfigError(
                f"There was an error trying to write serialize config data to JSON: {error}"
            )

        # make sure that directory structure exists, but we don't care
        # if there is already a config file here. Assume user calling generate_config
        # wants to create a new config file.
        try:
            self.WALLSY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        except FileExistsError:
            pass

        try:

            dest_file = self.WALLSY_CONFIG_DIR / "config.json"
            with open(dest_file, "w") as file:

                file.write(to_json)

        except OSError as error:
            raise WallsyConfigError(
                f"There was an error saving the configuration file: {error}."
            )

        return dest_file


def init() -> WallsyConfig:
    """initialize the wallsy CLI app"""

    try:
        config: WallsyConfig = load_config()

    except WallsyConfigError:

        try:
            config: WallsyConfig = WallsyConfig()
            config_path: Path = config.generate_config_json()

        except WallsyConfigError as error:

            raise WallsyConfigError(
                f"There was an issue trying to load config file for wallsy: {error}"
            )

    return config


def load_config() -> WallsyConfig:
    """
    Load a config.json from environment variable WALLSY_CONFIG_DIR or alternatively ~/.config/wallsy and instantiate variables as a WallsyConfig dataclass.
    Raise WallsyConfigError if a config file can't be found at that location.
    """

    # default config source should be ~/.config/wallsy/config.json
    config_src = Path("~/.config/wallsy/config.json").expanduser()

    # try to retrieve config directory from environment
    try:
        config_src = Path(os.environ["WALLSY_CONFIG_DIR"]) / "config.json"

    except KeyError:
        pass

    try:
        with config_src.open("r") as file:

            from_json = json.loads(file.read())
            config = WallsyConfig(**from_json)

    except json.JSONDecodeError as error:
        raise WallsyConfigError(f"There was an issue reading the config: {error}")

    except FileNotFoundError as error:
        raise WallsyConfigError(f"There was an issue opening the config: {error}")

    return config


config = init()
