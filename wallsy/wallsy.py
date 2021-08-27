"""
wallsy - update Gnome background wallpaper with beautiful Unsplash photos

wallsy allows users to refresh their wallpaper with random photos from Unsplash
that can be filtered by curated topics. Users can also schedule wallpapers
to auto update on a recurring interval. 

This module controls command line "routes" for interacting with the application.
"""

import os
import sys
import json
import shutil
from random import sample
from urllib.parse import urlparse
from pathlib import Path
from stat import S_ISFIFO
from pathlib import Path
from shutil import copyfile

import click

import wallsy.image_handler as image_handler
import wallsy.wallpaper_handler as wallpaper_handler
import wallsy.utils as utils

"""
Wallsy CLI

This module contains the Wallsy CLI app specification and command callback function definitions.

The app 

"""

# TODO: realized that requests library automatically follows redirects. hell yes. online random image is unblocked
# TODO: write the unsplash handler to be a wrapper around the source.unsplash API
# TODO: write random commmand so that it is effectively same behavior as current "wallsy --url" command with url specified as unsplash
# TODO: make it so that running desktop pumps the current wallpaper into the pipeline!!!!
# TODO: code cleanup - this thing is a huge mess right now
# TODO: documentation - make sure everything has docstrings, every click.option has "help" kwarg
#          every action has a click.echo() explanation and error handling is transparent and documented
# TODO: rearchitecture - effects should become their own subcommands
# TODO: how to fix "stacking" of effects unintentionally. e.g. random grabs an image that is blurred and you blur it again
# TODO: is it possible to support an unauthenticated random image from url?
# TODO: refactor occurrences of os.path to pathlib.Path across app
# TODO: notifications to user about save and retrieval
# TODO: unit testing
# TODO: random and effects
# FUTURE: Support streams of input and not single images.


@click.version_option()  # reads version from setup.cfg metadata
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
@click.option("--url", "-u")
def cli(ctx, file, url):  # named cli by convention in the click docs
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
        $ wallsy load --file="my-wallpaper.jpg" effects --blur=20 background

    3) Convert random "mountain" image to grayscale and save as "myphoto" to the 'documents' directory

        $ wallsy random -q="mountain" effects --grayscale save --dest="~/documents" --name="myphoto"

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

    settings = utils.init()

    # Check if wallsy is being used as part of a command pipeline, by checking if
    # there is a value for standard input.

    try:
        file = utils.get_stdin()

    except OSError:
        pass

    ### If standard input is not part of a pipe, path must be specified by user in file or url option

    if file is not None or url is not None:
        dest_path = load_file(file, url)
        # make dest_path available to other commands using the context object.
        # does not appear that return value of group function is available in return_callback
        ctx.obj = dest_path
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
def add(file=None, url=None) -> Path:
    """
    Add an image to Wallsy pipeline and save to Wallsy folder.
    """

    def _add(filename, *args, **kwargs):

        if filename:
            return load_file(file=filename)
        
        elif file:
            return load_file(file=file)
        
        elif url:
            return load_file(url=url)

        else:
            raise click.UsageError("Add - No file or url specified ")
            
    return _add

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

    dest_dir = Path(os.environ["WALLSY_MEDIA_DIR"])

    """
    FILE option
    """
    if file:

        # if file is not a Path, (can also be str or TextIOBuffer), convert to Path
        file = Path(file)
        dest_path = dest_dir / file.name

        # validate that the input file is a valid image.
        try:
            image_handler.validate_image(file)

        except image_handler.InvalidImageError as error:
            raise click.BadParameter(str(error))

        # copy the file contents to destination
        try:
            copyfile(file, dest_path)
            click.echo(f"Copied {file.name} to {dest_path}")
        except Exception as error:
            raise click.ClickException(error)

    """
    URL option
    """
    if url:

        file_name = Path(urlparse(url).path).name

        try:
            dest_path = image_handler.download_image(
                url=url, file_path=dest_dir / file_name
            )
            click.echo(f"Downloaded image to {dest_path}")
        except image_handler.ImageDownloadError as error:
            raise click.ClickException(str(error))
        except image_handler.InvalidImageError as error:
            raise click.BadParameter(str(error))

    # if we get this far, we should have a validated image. make the path available to other
    # subcommands by storing in the click context's object attribute (which is designed for this purpose)

    return dest_path

@cli.command(name="random")
@click.option("--query", "-q")
def random(query):
    """
    Generate a random image from source (default: Unsplash)
    """

    def _random(*args, **kwargs):

        img_set = list(Path(os.getenv("WALLSY_MEDIA_DIR")).iterdir())
        random_img = sample(img_set, 1)[0].resolve()
        click.echo(f"Grabbed {random_img.name} from {os.getenv('WALLSY_MEDIA_DIR')}")
        return random_img

    return _random


@cli.command(name="effect")
@click.option("--blur", is_flag=False, flag_value=50, default=50)
@click.option("--blur", is_flag=False, flag_value=50, default=50)

def apply_effects(blur):
    """
    Apply one or more effects to the image.
    """

    def _apply_effects(filename, *args, **kwargs):
        """Callback for the effect subcommand"""

        if filename is None:
            raise click.UsageError(
                "Effect failed - no valid image provided. Did you run 'load' or 'random' to source an image?"
            )

        if blur:
            click.echo(f"Blurring {filename.name}...")
            filename = image_handler.blur(filename, value=int(blur))
            click.echo(f"Saved new image as {filename.name}")
        
        return filename

    return _apply_effects


@cli.command(name="desktop")
def update_desktop_wallpaper():
    """
    Update the desktop background with the specified image.
    """

    ###
    # perform any checks that should fail the pipeline entirely here, before
    # the inner function definition.
    ###

    def _update_desktop_wallpaper(filename, *args, **kwargs):
        """Callback for the background subcommand"""

        # desktop command should be passed in a filename from a prior subcommand.

        # TODO: make it so that running desktop pumps the current wallpaper into the pipeline!!!!

        if filename is None:
            raise click.UsageError(
                "Update desktop failed - no valid image provided. Did you run 'load' or 'random' to source an image?"
            )

        wallpaper_dir = Path(os.getenv("WALLSY_WALLPAPER_DIR"))
        shutil.copyfile(filename, wallpaper_dir / filename.name)
        click.echo(f"Added a copy of {filename.name} to {wallpaper_dir}")
        wallpaper_handler.update_wallpaper(img_path=wallpaper_dir / filename.name)
        click.echo(f"Desktop wallpaper updated to {wallpaper_dir / filename.name}")

        return filename

    return _update_desktop_wallpaper


@cli.result_callback()
@click.pass_context
def process_pipeline(ctx, callbacks, *args, **kwargs):
    """
    The result_callback decorator supplies this function with an argument containing all of the return values from
    the invoked subcommands. By returning an inner function from each subcommand, we can control the order of execution
    and process the results of the pipeline arbitrarily. This is useful when the inner function is an iterator or generator that
    yields and there is a good example of processing input text streams this way in the Click documentation.

    However, in our case we will use it to chain subcommands in such a way that we can execute an entire image processing
    user flow in a single line on the command line, e.g. download -> apply effect -> update background
    Note that this flow would entail retrieving an image, modifying that image, then updating the wallpaper to retrieve
    from the corresponding file path.
    """

    """
    Subcommand clobbering. If conflicting subcommands are provided, e.g. "load" and "random" which
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
    all callbacks either act on a filename, return a filename, or both. 
    callbacks that return a filename but ignore filenames provided as input 
    are generally those used to source an image for processing, e.g. "load" or "random"
    """

    filename = ctx.obj

    for callback in callbacks:
        filename = callback(filename)
