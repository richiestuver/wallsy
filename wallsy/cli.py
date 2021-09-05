"""
wallsy - update Gnome background wallpaper with beautiful Unsplash photos

wallsy allows users to refresh their wallpaper with random photos from Unsplash
that can be filtered by curated topics. Users can also schedule wallpapers
to auto update on a recurring interval. 

This module controls command line "routes" for interacting with the application.
"""

import os
from typing import Optional
from random import sample
from pathlib import Path
from shutil import copy2, SameFileError
from functools import wraps, update_wrapper
from io import StringIO

import click
from rich import print

from . import image_handler
from . import wallpaper_handler
from . import unsplash_handler

from .console import console
from .console import error_console
from .console import warn
from .console import fail
from .console import describe
from .console import confirm

from .config import WallsyConfig
from .config import init

from .utils import WallsyData
from .utils import get_stdin
from .utils import load
from .utils import WallsyLoadError
from .utils import require_file
from .utils import make_callback
from .utils import printer_factory


"""
Wallsy CLI

This module contains the Wallsy CLI app specification and command callback function definitions.

"""

# TODO: documentation - make sure everything has docstrings, every click.option has "help" kwarg
#          every action has a print() explanation and error handling is transparent and documented
# TODO: handle specifying a target file name for saves and what to do when a conflict occurs
#           Prompt user for a new file name, don't create one?
# TODO: implement scheduler!!!!
# TODO: how to initialize? on app invocation or on install somehow?
# TODO: prevent non image files from getting picked up by random --local
# TODO: refactor std out messaging architecture
# TODO: rearchitecture - effects should become their own subcommands
# TODO  add --prompt option to desktop
# TODO: moar effects - darken and lighten, and warhol effects
# TODO: add --overwrite option to disable saving each sub image
# TODO: refactor occurrences of os.path to pathlib.Path across app.
# TODO: notifications to user about save and retrieval
# TODO: fix issue where mode after posterize is incompatible with other effects like blur (ValueError)
# TODO: unit testing
# FUTURE: Support streams of input and not single images.


@click.group(
    chain=True
)  # default behavior is to pass --help automatically if no subcommand provided
@click.pass_context
@click.option(
    "--file",
    "-f",
    type=click.Path(
        path_type=Path
    ),  # make sure that file paths are always Path objects.
    help="Load an image from file path. Ensures image is valid and stores a copy of the image in the Wallsy folder.",
)
@click.option(
    "--url",
    "-u",
    help="Load an image directly via url. Must link directly to an image resouce, not an API endpoint. e.g. www.example.com/image.jpg",
)
@click.option("--verbose", "-v", "verbosity", flag_value="verbose", default=True)
@click.option(
    "--quiet",
    "verbosity",
    flag_value="quiet",
)
@click.version_option()  # reads version from setup.cfg metadata
def cli(
    ctx: click.Context, file: Path, url: str, verbosity
) -> Optional[Path]:  # named cli by convention in the click docs
    """
    The best image modifier for custom wallpapers.

    Usage:

    Wallsy is designed to chain commands together into powerful one-line expressions to collect, edit, and use images.

    1) (Required) specify an input image using either 'new' or 'random' commands (e.g. $ wallsy new --file="photo.jpg" ...)

    2) (Optional) apply desired image manipulations using 'effects' command (e.g. $ wallsy ... effects --blur=20 ...)

    3) (Optional) save image or set the resulting image as a new desktop background using 'save' or 'desktop' commands
    (e.g. $ wallsy ... save --name="myphoto" ...)

    Examples:

    1) Update desktop background with a random wallpaper

        $ wallsy random background

    2) Add a blur to an image and set it as the desktop background
        $ wallsy --file="my-wallpaper.jpg" effects --blur=20 background

    3) Convert random "mountain" image to grayscale and save as "myphoto" to the 'documents' directory

        $ wallsy random -q="mountain" effects --noir save --dest="~/documents" --name="myphoto"

    For detailed help text run the --help modifier with the specified command, e.g.

    $ wallsy background --help
    """

    """
    INVOCATION METHOD 1: Receive a file path through standard input as part of a pipeline
                         Note that 'file' argument takes precedence over standard input
    
    Support receiving a file path from standard input instead of as a command line argument. This is really
    cool and delves a bit deep into the Python standard library. The OS module allows us to query a file descriptor
    and return information from the operating system about that file, such as ownership, size, etc. We can use the 
    stat module to deconstruct and query the resulting stat object that os.stat provides, and in our case use the IS_FIFO
    method to determine if the file descriptor is a UNIX pipe or not. Major kudos to the following SO article and the 
    Python OS and Stat module documentation:

    https://stackoverflow.com/questions/35247817/is-there-a-way-for-a-python-script-to-know-if-it-is-being-piped-to
    https://docs.python.org/3/library/stat.html
    https://docs.python.org/3/library/os.html#os.stat_result
    """

    # Initialize the wallsy app by loading variables from a config file. Used to customize
    # things like default directories for saving and retrieving files, effects styles etc.

    config: WallsyConfig = init()
    ctx.obj = WallsyData(config=config)

    # if verbosity is set to quiet, capture all std_out and std_err to a junk stream.
    if verbosity == "quiet":
        console.file = StringIO()

    # Check if wallsy is being used as part of a command pipeline, by checking if
    # there is a value for standard input.

    try:
        file: Path = get_stdin()

    except OSError:
        pass

    """
    INVOCATION METHOD 2: If standard input is not part of a pipe, path should be specified by user in file or url option. 
    There are some subcommands which act as a source for file path input for later commands, so wallsy should not fail at this 
    stage. As a result, it is necessary for each subcommand that explicitly requires a file path to apply the 
    @require_file decorator to make sure that necessary inputs are handled and raise relevant errors when missing.
    """

    dest_path = None

    if file is not None or url is not None:

        try:
            dest_path = load(file, url)
        except WallsyLoadError as error:
            error_console.print(f"There was an error trying to load the file: {error}")
            raise click.ClickException(message=None)

        """
        make dest_path available to the result callback via the Click Context object.
        it does not appear that the return value of this group function is available in return_callback.
        While click options are passed automatically into result_callback, standard input is collected
        within the command itself and so will not appear as an argument to that function. The only way 
        to ensure our input file path arrives is through the context object. 
        """

        ctx.obj.file = dest_path

    return dest_path


@cli.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(
        path_type=Path
    ),  # make sure that file paths are always Path objects.
    help="Load an image from file path. Ensures image is valid and stores a copy of the image in the Wallsy folder.",
)
@click.option("--url", "-u")
@make_callback
def add(file_from_pipeline: Path, file: str = None, url: str = None):
    """
    Add an image to Wallsy pipeline and save to Wallsy folder.
    """

    if file_from_pipeline:
        return load(file=file_from_pipeline)

    elif file:
        return load(file=file)

    elif url:
        return load(url=url)

    else:
        raise click.UsageError("no file or url specified.")


@cli.command(name="random")
@click.pass_obj
@click.option(
    "--keyword",
    "-q",
    multiple=True,
    help="Specify keyword to refine random results. Can use multiple times e.g. random -q pizza -q lemon",
)
@click.option(
    "--size",
    "-s",
    "dimensions",
    type=(int, int),
    help="(--online only) specify dimensions of the image to retrieve, e.g. -s 1920 1080",
)
@click.option(
    "--local/--online",
    is_flag=True,
    show_default=True,
    default=False,
    help="Grab an image from Unsplash or locally from your wallsy folder.",
)
@make_callback
@printer_factory(enter="Grabbing a random image...")
def random(obj: WallsyData, file_from_pipeline, keyword, dimensions, local):
    """
    Generate a random image from source (default: Unsplash).

    Note: file_from_pipeline is the only argument passed to the callback function in the process_pipeline stage. This argument is
    used by nearly all commands to operate on the currently active image. The random command, however, is intended to generate
    new filenames for use by subsequent commands on the pipeline. If random is specified somewhere in the middle of a chain
    of commands, the current behavior is to "ignore" input all previous commands and generate a new file as usual.
    While probably unintended usage, this could have limited utility in the case a user wants to perform processing on a small
    finite number of files in a single line on the terminal.
    """

    if file_from_pipeline:
        error_console.print(
            f"Warning: {__name__} received a file from a previous command. Ignoring that file and generating a new random image."
        )

    file = None

    if local:
        img_set = list(obj.config.WALLSY_MEDIA_DIR.iterdir())
        file = sample(img_set, 1)[0].resolve()
        console.print(f"Grabbed {file.name} from {obj.config.WALLSY_MEDIA_DIR}")

    else:
        file = load(
            url=unsplash_handler.random_featured_photo(
                keywords=keyword if keyword else None,
                dimensions=dimensions if dimensions else None,
            )
        )

    return file


@cli.command(name="blur")
@click.pass_obj
@click.option(
    "--radius",
    default=5,
    show_default=True,
    help="Specify the pixel radius for blur effect.",
)  # note that click options are passed to the decorated command as keyword arguments. so should be specified after positional in the signature
@make_callback
@require_file
def blur(obj: WallsyData, file: Path, radius):
    """
    Apply a Gaussian blur effect to image. Default pixel radius for blur is 5.

    Note that Click handles exceptions in cases where invalid input is provided for radius (default value and type provided).
    """

    console.print(f"blurring {file.name} with radius {radius}..")

    file = image_handler.blur(
        file,
        radius=int(radius),
        dest_path=Path(obj.config.WALLSY_MEDIA_DIR) / file.name,
    )

    console.print(f"saved new image as {file.name} in directory {file.parent}")

    return file


@cli.command(name="noir")
@make_callback
@require_file
def noir(file):
    """Apply a noir effect to the image. Currently this only converts image to greyscale. May add
    additional enhancements (e.g. increase contrast) in the future.
    """
    console.print(f"Applying noir effect to {file.name}")
    file = image_handler.greyscale(img_path=file, path_modifier="noir")
    console.print(f"Saved new image as {file.name}")

    return file


@cli.command()
@click.option(
    "--colors",
    default=32,
    show_default=True,
    help="Specify the number of colors to reduce the image to (range 1-255)",
)
@make_callback
@require_file
def posterize(file: Path, colors: int):
    """
    Apply a posterization effect to the image.
    """

    console.print(f"Applying poster effect to {file.name}...")
    file = image_handler.quantize(file, path_modifier="posterize", colors=colors)
    console.print(f"Saved new image as {file.name}")
    return file


@cli.command(name="desktop")
@make_callback
@click.pass_obj
def update_desktop_wallpaper(obj: WallsyData, file):
    """
    Update the desktop background with the specified image.
    """

    if file:
        wallpaper_dir = obj.config.WALLSY_WALLPAPER_DIR

        try:
            # note: copy2 attempts to preserve file metadata. other copy functions in shutil do not do so
            copy2(file, wallpaper_dir / file.name)
            console.print(f"Added a copy of {file.name} to {wallpaper_dir}")
        except SameFileError:
            error_console.print(f"{file.name} is already located at {wallpaper_dir}")

        wallpaper_handler.update_wallpaper(img_path=wallpaper_dir / file.name)
        console.print(f"Desktop wallpaper updated to {wallpaper_dir / file.name}")

    else:  # retrieve the currently set desktop wallpaper and use that as input for the pipeline
        file = wallpaper_handler.get_current_wallpaper()
        file = load(file=file)

    return file


@cli.command()
@make_callback
@require_file
def show(file: Path):
    """Show the current image using the default application for the OS."""

    click.launch(str(file))
    return file


@cli.result_callback()
@click.pass_obj
def process_pipeline(obj: WallsyData, callbacks, *args, **kwargs):
    """
    The result_callback decorator supplies this function with an argument containing all of the return values from
    the invoked subcommands, as well as all of the arguments supplied to the main group() function itself. By returning an inner function from each subcommand, we can control the order of execution
    and process the results of the pipeline arbitrarily. This is useful when the inner function is an iterator or generator that
    yields and there is a good example of processing input text streams this way in the Click documentation.

    However, in our case we will use it to chain subcommands in such a way that we can execute an entire image processing
    user flow in a single line on the command line, e.g. download -> apply effect -> update background
    Note that this flow would entail retrieving an image, modifying that image, then updating the wallpaper to retrieve
    from the corresponding file path.
    """

    """
    Subcommand clobbering. If conflicting subcommands are provided, e.g. "add" and "random" which
    both output a filepath pointing toward a valid image, the one specified later in the pipeline
    will overwrite the results of the previous. 
    
    Theoretically should be able to do cool things like stream of multiple images, but save 
    that for a later date. 
    """

    """
    Pipeline ordering

    Image processing follows this general flow: 
    1) get an image -> 2) perform actions on image -> 3) peform actions on system (e.g. desktop background)
    
    1) must come first because all other actions require a valid image and existing filepath in order to 
    execute successfully. 
    """

    """
    all callbacks either act on a file, return a file, or both. 
    callbacks that return a file but ignore filenames provided as input 
    are generally those used to source an image for processing, e.g. "load" or "random"
    """

    file = obj.file

    for callback in callbacks:
        console.print(callback)
        file = callback(file)


if __name__ == "__main__":
    pass
