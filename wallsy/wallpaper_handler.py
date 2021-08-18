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

# see PyGObject API ref for Gio.Settings or >>> help(Gio.Settings) in REPL
from gi.repository import Gio


class WallpaperUpdateError(Exception):
    """
    Raised when an attempt to update Gnome desktop background fails.
    """

    pass

def get_wallpaper_location() -> Path:
    """
    Read the target wallpaper location from config. For Gnome DE this should be 
    set to "~/.local/share/backgrounds" if it's desirable that wallpapers appear
    in the desktop wallpaper GUI in Gnome settings.
    """

    pass

def set_wallpaper_location(file_path: str = "~/.local/share/backgrounds"):
    """
    Set the download and retrieval location for storing and accessing background images.
    This function takes the supplied url path string, convert it to a Path object, and create
    the directory if it does not already exist. Store the location in an environment variable.

    Note on default Gnome wallpaper behavior: the builtin Gnome desktop wallpaper GUI stores images that users add through the settings GUI to the directory
    /home/{user}/.local/share/backgrounds'. Images found in this directory will show up in
    the GUI so for management this is the ideal location to store as a default. Note that the
    popular Gnome Tweak Tool (not the built in settings app) does NOT save images to this location.
    """

    # since we expect the default dir to live in user's home directory, make sure this path is resolved correctly.
    # Expand user before making path absolute.
    wallpaper_location = Path(file_path).expanduser().resolve()
    if not wallpaper_location.exists():
        try:
            wallpaper_location.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            raise FileExistsError(f"Error trying to create {str(wallpaper_location)}.")

    # store path in environment variable


def update_wallpaper(img_path: str, options=None) -> None:
    """
    Update the background image to the one specified by file_path. Raise BackgroundUpdateError if issues encountered
    during attempt to update background.
    """

    """
    Gio Settings object provides Dict-like access to key-value pairs which in this case allow
    us to interact with the Gnome desktop background image settings.
    the target key for changing wallpapers is 'picture-uri' and takes a string representing
    a full path. No errors are thrown for invalid values. Instead, background is set 
    to not include an image. Note that this effect can be desirable for cases where
    a gradient or color is set to the background, but note that this is not currently
    supported by this application. 
    """

    gnome_background_settings = Gio.Settings(schema="org.gnome.desktop.background")

    # check that path exists before update. if not, raise error and notify user
    # following code returns false for empty string "" and invalid rel or abs paths
    # NOTE: os.path.exists accepts integers (open file descriptors). This won't catch
    # invalid types for our purposes. Additional check should be used.

    try:
        wallpaper_location = Path(img_path).expanduser().resolve()
    except TypeError:
        raise WallpaperUpdateError(
            f"Invalid parameter: {img_path} is not a valid Pathlike object."
        )

    # subsequent operations will fail if path does not exist or is not a file, so catch this.
    if not wallpaper_location.exists() or not wallpaper_location.is_file():
        raise WallpaperUpdateError(
            f"Invalid path provided for image location: {img_path} does not exist."
        )

    # what() returns None if no matching image type is determined for a given file path.
    # See list of valid image types at https://docs.python.org/3/library/imghdr.html
    if imghdr.what(wallpaper_location) is None:
        raise WallpaperUpdateError(
            f"Invalid image type provided. {wallpaper_location.name} is not a valid image."
        )

    # make sure to use the absolute path so resource is locatable when accessed from schema
    # XML schema is read directly, there is no path validation done by Gnome desktop
    gnome_background_settings["picture-uri"] = str(wallpaper_location)
