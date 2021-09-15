"""
wallsy - update Gnome background wallpaper with beautiful Unsplash photos

wallsy allows users to refresh their wallpaper with random photos from Unsplash
that can be filtered by curated topics. Users can also schedule wallpapers
to auto update on a recurring interval. 

This module controls command line "routes" for interacting with the application.
"""

from random import sample
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import ParseResult
from shutil import copy2
from io import StringIO
from itertools import chain
from itertools import cycle
from collections.abc import Iterable
from functools import singledispatch
from collections.abc import Generator
from time import sleep

import click

from . import image_handler
from . import wallpaper_handler
from . import unsplash_handler

from .console import console
from .console import warn
from .console import describe
from .console import confirm_success

from .config import WallsyConfig
from .config import init

from .utils import WallsyData
from .utils import yield_stdin
from .utils import load

from .decorators import require_file
from .decorators import make_callback
from .decorators import make_cycle
from .decorators import make_generator
from .decorators import catch_errors
from .decorators import extend_stream


"""
Wallsy CLI

This module contains the Wallsy CLI app specification and command callback function definitions.

"""


@click.group(
    chain=True
)  # default behavior is to pass --help automatically if no subcommand provided
@catch_errors
@click.pass_context
@click.option(
    "--file",
    "-f",
    "files",
    multiple=True,  # if opt not provided the arg defaults to ()
    type=click.Path(
        path_type=Path
    ),  # make sure that file paths are always Path objects.
    help="Load an image from file path. Ensures image is valid and stores a copy of the image in the Wallsy folder",
)
@click.option(
    "--url",
    "-u",
    "urls",
    multiple=True,  # argument is now a tuple of str or an empty tuple
    type=str,
    help="Load an image directly via url. Must link directly to an image resource, e.g. www.example.com/image.jpg",
)
@click.option(
    "--verbose",
    "verbosity",
    flag_value="verbose",
    default=True,
    help="Print all output to stdout or the terminal",
)
@click.option(
    "--quiet",
    "verbosity",
    flag_value="quiet",
    help="Silence all output printed to the stdout or the terminal.",
)
@click.version_option()  # reads version from setup.cfg metadata
def cli(
    ctx: click.Context, files, urls, verbosity
):  # named cli by convention in the click docs
    """
    Wallsy

    create beautiful images, effects, and desktop wallpapers through composable edits on the command line.


    ====================
    Quickstart
    ====================

    Change your desktop wallpaper with a random featured photo from Unsplash:

        $ wallsy random desktop

    Add an effect (e.g. posterize or noir) to your current desktop wallpaper

        $ wallsy desktop posterize desktop


    ====================
    Usage:
    ====================

    Wallsy is designed to chain commands together into powerful one-line expressions to collect, edit, and compose images with a
    focus on use in personal applications like wallpapers, background images for streaming/creative applications, etc.

    - Specify an input image or grab a random image either online or locally, e.g.

        get a random image from Unsplash Source and display it:

            $ wallsy random show

        get a random image from your ~/wallsy folder:

            $ wallsy random --local show

        add a new image to your ~/wallsy folder:

            $ wallsy --file myphoto.jpeg show

        grab an image from a url:

            $ wallsy --url https://example.com/myphoto.jpg show


    - Apply effects to an image in a fully composable way, e.g.


        create a poster effect of a photo of your dog:

            $ wallsy --file "mydog.jpeg" posterize show

        blur a random "nature" image from Unsplash Source:

            $ wallsy random --keyword "nature" blur show

        add blur and noir effects to a random 4k image of Tokyo:

            $ wallsy random --keyword "tokyo" --size 3840 2160 blur noir show


    - Desktop wallpaper support - automatically update your desktop or use your current
    desktop image as input, e.g.

        generate a custom image and update your desktop wallpaper:

            $ wallsy random --keyword="new york city" --keyword="skyline" noir desktop

        use your current wallpaper as input for some cool effects then save it back to your wallpaper

            $ wallsy desktop blur noir posterize desktop


    ====================
    Fine Grained Controls:
    ====================

    Wallsy tries to provide sensible defaults for simple usage but expose enough controls
    to allow you to tweak edits to get the results you want. Most effect commands allow
    you to vary the level of the effect, e.g.

        apply a 20px blur to a photo and add a posterization effect reducing to 16 colors:

            wallsy --file myfile.jpg blur --radius=20px posterize colors=16 show


    ====================
    Help
    ====================

    To see what's available and for detailed help text add --help to the specified command, e.g.

        $ wallsy random --help

        $ wallsy posterize --help


    Have fun with Wallsy!
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

    streams = [
        (load(Path(file)) for file in yield_stdin() if file),
        (load(Path(file)) for file in files),
        (load(urlparse(url)) for url in urls),
    ]

    stream = (file for file in chain(*streams))
    ctx.obj.stream = stream
    return stream


@cli.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(
        path_type=Path
    ),  # make sure that file paths are always Path objects.
    help="Load an image from file path. Ensures image is valid and stores a copy of the image in the Wallsy folder.",
)
@click.option("--url", "-u", type=str)
@make_callback
@extend_stream
@catch_errors
def add(file_from_pipeline: Path = None, file: Path = None, url: str = None):
    """
    Add a copy of image to the Wallsy folder. Useful for things like random --local and image management. Use as part of a pipeline
    or specify a file / url manually.
    """

    # if file_from_pipeline:
    #     file: Path = load_file(file=file_from_pipeline)

    if file:
        file: Path = load(file)

    elif url:
        file: Path = load(urlparse(url))

    else:
        raise click.UsageError(
            "'add' recieved nothing from pipeline and no file or url specified."
        )

    confirm_success(
        f":floppy_disk-emoji: 'add' loaded '{file.name}' from {file.parent}"
    )
    return file


@cli.command(name="random")
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
@extend_stream
@catch_errors
@click.pass_obj
def random(obj: WallsyData, file_from_pipeline, keyword, dimensions, local):
    """
    Generate a random image from source (default: Unsplash).
    """

    """
    Note: file_from_pipeline is the only argument passed to the callback function in the process_pipeline stage. This argument is
    used by nearly all commands to operate on the currently active image. The random command, however, is intended to generate
    new filenames for use by subsequent commands on the pipeline. If random is specified somewhere in the middle of a chain
    of commands, the current behavior is to "ignore" input all previous commands and generate a new file as usual.
    While probably unintended usage, this could have limited utility in the case a user wants to perform processing on a small
    finite number of files in a single line on the terminal.
    """

    # if file_from_pipeline:
    #     warn(
    #         f"'random' received a file from a previous command. Ignoring that file and generating a new random image..."
    #     )

    file = None

    if local:

        img_set = list(obj.config.WALLSY_MEDIA_DIR.iterdir())
        file = sample(img_set, 1)[0].resolve()
        confirm_success(
            f":game_die-emoji: 'random' grabbed '{file.name}' from {obj.config.WALLSY_MEDIA_DIR}"
        )

    else:
        url = unsplash_handler.random_featured_photo(
            keywords=keyword if keyword else None,
            dimensions=dimensions if dimensions else None,
        )
        file = load(urlparse(url))

    return file


@cli.command(name="blur")
@click.option(
    "--radius",
    default=5,
    show_default=True,
    help="Specify the pixel radius for blur effect.",
)  # note that click options are passed to the decorated command as keyword arguments. so should be specified after positional in the signature
@make_callback
@make_generator
@catch_errors
@click.pass_obj
@require_file
def blur(obj: WallsyData, file: Path, radius):
    """
    Apply a Gaussian blur effect to image. Default pixel radius for blur is 5.

    Note that Click handles exceptions in cases where invalid input is provided for radius (default value and type provided).
    """

    describe(
        f":blue_circle-emoji: 'blur' applying blur to '{file.name}' with radius {radius}.."
    )

    file = image_handler.blur(
        file,
        radius=int(radius),
        dest_path=Path(obj.config.WALLSY_EFFECTS_DIR) / file.name,
    )

    confirm_success(
        f":floppy_disk-emoji: 'blur' saved image as '{file.name}' in {file.parent}"
    )

    return file


@cli.command(name="noir")
@make_callback
@make_generator
@catch_errors
@click.pass_obj
@require_file
def noir(obj, file):
    """Apply a noir effect to the image. Currently this only converts image to greyscale. May add
    additional enhancements (e.g. increase contrast) in the future.
    """
    describe(f":detective-emoji:  'noir' applying noir effect to '{file.name}'")

    file = image_handler.greyscale(
        img_path=file,
        path_modifier="noir",
        dest_path=Path(obj.config.WALLSY_EFFECTS_DIR) / file.name,
    )

    confirm_success(
        f":floppy_disk: 'noir' saved image as '{file.name}' in {file.parent}"
    )

    return file


@cli.command()
@click.option(
    "--colors",
    default=32,
    show_default=True,
    help="Specify the number of colors to reduce the image to (range 1-255)",
)
@make_callback
@make_generator
@catch_errors
@require_file
def posterize(file: Path, colors: int):
    """
    Apply a posterization effect to the image.
    """

    describe(f":sparkler-emoji: 'poster' applying poster effect to '{file.name}'...")
    file = image_handler.quantize(file, path_modifier="posterize", colors=colors)
    confirm_success(
        f":floppy_disk-emoji: 'poster' saved image as '{file.name}' in {file.parent}"
    )
    return file


@cli.command()
@make_callback
def desktop(stream):
    """
    Set your desktop background or use your current desktop as a source image.
    """

    """
    The desktop command supports two modes: operating on the current stream (setting 
    the desktop background as a side effect) or supplying additional image(s) to the 
    stream (retrieving the filepath of the current desktop background). 

    This is made possible by evaluating the state of the generator represented by the stream
    and determining if the generator is both empty and never supplied any items. We are sort 
    of abusing the StopIteration behavior of generators to accomplish this because there is not
    a simple "is empty" style function call to get the state of the underlying iterator.

    In a future refactor, we might be able to assess this without the try/except block by
    making a call to inspect.getgeneratorlocals() and seeing if the dict that is returned as
    the first argument is empty. 

    For now, we check the state of a variable holding Path items retrieved from the stream generator
    to determine our condition. If StopIteration is raised no items were pulled from the generator
    then we execute the version of the desktop command that supplies additional items to the stream for 
    use in subsequent subcommands. 

    The dispatching logic is greatly simplified (read: abstracted partly away from this Click controller)
    by the functools @singledispatch decorator. Rather than doing this by hand, the logic here purely pertains 
    to how to determine the appropriate condition and then passing a variable argument type (either 
    a single Path object or the generator itself) to the dispatcher.

    Note that the inspect.getgeneratorstate(<generator_object...>) is insanely helpful for debugging 
    code that works with generators.
    """

    file = None

    try:
        while file := next(stream):
            yield _desktop(file)

    except StopIteration:
        if file is None:
            yield from _desktop(stream)


@singledispatch
def _desktop(arg):
    """
    Callback for the desktop command. This function is a dispatcher that
    calls out to different helper functions depending on the argument type
    retrieved. Passing in a Path object should set the desktop background.
    Passing in a Generator object should extend the iterator by including the
    retrieving the current desktop wallpaper path and appending it to the
    iterator items.
    """

    raise UserWarning(f"Invalid argument received for {__name__}: {arg}")


@_desktop.register
@click.pass_obj
def _set_desktop(obj, file: Path):
    """
    Called by _desktop dispatcher to set the desktop wallpaper.
    """

    wallpaper_dir = obj.config.WALLSY_WALLPAPER_DIR

    if not Path(wallpaper_dir / file.name).exists():

        # note: copy2 attempts to preserve file metadata. other copy functions in shutil do not do so
        copy2(file, wallpaper_dir / file.name)
        describe(
            f":desktop_computer-emoji:  'desktop' added a copy of '{file.name}' to {wallpaper_dir}"
        )

    else:
        warn(f"'{file.name}' is already located at {wallpaper_dir}")

    wallpaper_handler.update_wallpaper(img_path=wallpaper_dir / file.name)
    confirm_success(
        f":white_check_mark-emoji: 'desktop' updated wallpaper to {wallpaper_dir / file.name}"
    )

    return file


@_desktop.register
def _get_desktop(stream: Generator):
    """
    Called by _desktop dispatcher to retrive the current wallpaper and extend the
    provided generator with the Path of the wallpaper.
    """

    file = wallpaper_handler.get_current_wallpaper()
    describe(
        f":desktop_computer-emoji: 'desktop' retrieved current background '{file}'"
    )
    file = load(file)
    return (img for img in chain(stream, [file]))


@cli.command()
@make_callback
@make_generator
@catch_errors
@require_file
def show(file: Path):
    """Show the current image using default image viewer."""

    click.launch(str(file))
    return file


@cli.command(name="every")
@make_callback
@make_generator
@click.pass_obj
@click.argument("interval", type=int)
def repeat(obj: WallsyData, file, interval):
    """Set wallsy to repeat this action on an interval"""

    obj.repeat = True
    obj.interval = interval
    confirm_success(f"Waiting {interval}s...")

    return file


@cli.result_callback()
@click.pass_obj
# @catch_errors
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

    def process_stream():

        stream: Iterable = obj.stream

        for callback in callbacks:
            stream = callback(stream)

        for _ in stream:
            pass

        sleep(obj.interval) if obj.interval else ...

    # do at least once, then bail out if no cycle
    process_stream()
    while obj.repeat:
        process_stream()


if __name__ == "__main__":
    pass
