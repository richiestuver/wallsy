"""
wallsy 

Create beautiful images, effects, and desktop wallpapers through composable edits on the command line.

This module defines the entry point to the wallsy CLI. It defines a 'cli' command group which 
collects input streams from standard input as well as any provided global options. 

A callback processor is passed a list of callbacks for each of the subcommands that are invoked. Each
callback accepts an input stream and wraps the stream in a new generator that, when later accessed, yields values from 
the input stream after having been processed by some image processing function defined internally.

After all of the callbacks have executed, we are left with a final "stream" generator-in-generator
that can be iterated over to trigger the image processing functions in succession. 
"""

from pathlib import Path
from urllib.parse import urlparse
from io import StringIO
from itertools import chain

import click

from wallsy.config import config

from wallsy.cli_utils.decorators import *
from wallsy.cli_utils.utils import *
from wallsy.cli_utils.console import *

from wallsy.WallsyStream import WallsyStream


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
def cli(ctx: click.Context, files, urls, verbosity):
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

    ctx.obj = WallsyStream()

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


@cli.result_callback()
@click.pass_obj
@catch_errors
def process_pipeline(obj: WallsyStream, callbacks, *args, **kwargs):
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
    Pipeline ordering

    Image processing follows this general flow: 
    1) get an image -> 2) perform actions on image -> 3) peform actions on system (e.g. desktop background)
    
    1) must come first because all other actions require a valid image and existing filepath in order to 
    execute successfully. 
    """

    """
    all callbacks act on a stream (generator) either by yielding a modification to each item in the iterable
    or extending the stream by chaining an additional iterable to the generator.
    """

    def process_stream(stream: WallsyStream):

        for callback in callbacks:
            stream = callback(stream)

        for _ in stream.stream:
            pass

    # do at least once, then bail out if no cycle
    stream: WallsyStream = obj
    process_stream(stream)

    while stream.repeat:
        process_stream(stream)


def main():

    commands = import_commands()
    attach_commands(cli, commands)
    cli()


if __name__ == "__main__":
    main()
