"""
Gnome Wallpaper Handler

This module handles updates to the Gnome desktop background by interfacing with the 
settings XML for org.gnome.desktop.background exposed by the GObject API.

Python has available a third-party package PyGObject which provides an interface
for  GTK/Gnome/GIO entities. More information can be found at:
https://pygobject.readthedocs.io/en/latest/ 

Settings for desktop backgrounds are defined under the schema: org.gnome.desktop.background
More information on this schema can be found at: 
https://github.com/GNOME/gsettings-desktop-schemas/blob/master/schemas/org.gnome.desktop.background.gschema.xml.in 
"""

from pathlib import Path
import imghdr  # use to determine if image is valid
import subprocess
from collections import OrderedDict


class WallpaperUpdateError(Exception):
    """
    Raised when an attempt to update Gnome desktop background fails.
    """

    pass


def get_current_wallpaper() -> Path:
    """
    Retrieve the current wallpaper from the Gnome settings for desktop background. This is done
    by dropping into the gsettings shell command.
    """

    get_desktop_background = OrderedDict(
        [
            ("cmd", "/usr/bin/gsettings"),
            ("subcmd", "get"),
            ("schema", "org.gnome.desktop.background"),
            ("key", "picture-uri"),
        ]
    )

    try:

        process = subprocess.run(
            " ".join(get_desktop_background.values()),
            shell=True,
            # capture_output=True,
            text=True,
            check=True,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    except (subprocess.CalledProcessError) as error:
        raise WallpaperUpdateError(f"Could not retrieve current background: {error}")

    # the output we get from stdout is not cleanly formatted. for encoding reasons
    # I have not fully grasped yet. Cleanse the string by removing secret whitespace
    # and extraneous quote chars.

    wallpaper: Path = Path(
        process.stdout.strip()
        .removeprefix("'")
        .removeprefix("file://")
        .removesuffix("'")
    )

    return wallpaper


def update_wallpaper(img_path: Path, options=None) -> None:
    """
    Update the background image to the one specified by file_path. Raise BackgroundUpdateError if issues encountered
    during attempt to update background.
    """

    """
    check that path exists before update. if not, raise error and notify user
    following code returns false for empty string "" and invalid rel or abs paths
    NOTE: os.path.exists accepts integers (open file descriptors). This won't catch
    invalid types for our purposes. Additional check should be used.

    make sure to use the absolute path so resource is locatable when accessed from schema
    XML schema is read directly, there is no path validation done by Gnome desktop
    """

    img_path = Path(str(img_path).removeprefix("file:"))

    wallpaper_location = Path(img_path).expanduser().resolve().absolute()

    # subsequent operations will fail if path does not exist or is not a file, so catch this.
    if not wallpaper_location.exists() or not wallpaper_location.is_file():
        raise WallpaperUpdateError(
            f"Invalid path provided for image location: {img_path} does not exist."
        )

    # what() returns None if no matching image type is determined for a given file path.
    # See list of valid image types at https://docs.python.org/3/library/imghdr.html
    if imghdr.what(wallpaper_location) is None:
        raise WallpaperUpdateError(
            f"Invalid image type provided. {wallpaper_location.name} is not a valid"
            " image."
        )

    """
    Drop into gsettings CLI to efficiently update the desktop background without expensive dependencies.
    Gsettings only exists for GNOME desktop environments so in future be sure to check for platform before 
    trying to use this command. 

    subprocess.CalledProcessError is raised by the run method call if a non-zero exit status is returned. This
    is your main way of determining if an issue has been encountered during the subprocess run. 
    """

    # ordered dict is used here for clarity and to preserve sequence for command arguments. there's
    # probably a better structure to use but this is good for now
    set_desktop_background = OrderedDict(
        [
            ("cmd", "/usr/bin/gsettings"),
            ("subcmd", "set"),
            ("schema", "org.gnome.desktop.background"),
            ("key", "picture-uri"),
            ("value", f"{wallpaper_location}"),
        ]
    )

    print(set_desktop_background)
    try:

        result = subprocess.run(
            " ".join(set_desktop_background.values()),
            shell=True,
            # capture_output=True,
            check=True,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        print(result.returncode, result.stdout, result.stderr)

    except (subprocess.CalledProcessError) as error:
        raise WallpaperUpdateError(f"Could not set desktop background: {error}")
