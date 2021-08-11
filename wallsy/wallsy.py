"""
wallsy - update Gnome background wallpaper with beautiful Unsplash photos

wallsy allows users to refresh their wallpaper with random photos from Unsplash
that can be filtered by curated topics. Users can also schedule wallpapers
to auto update on a recurring interval. 

This module controls command line operations for interacting with the application.
"""

import click

import wallsy.image_handler as image_handler


@click.version_option()  # reads version from setup.cfg metadata
@click.group(
    chain=True
)  # default behavior is to pass --help automatically if no subcommand provided
def cli():  # named cli by convention in the click docs
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

        $ wallsy new --file="my-wallpaper.jpg" effects --blur=20 background

    3) Convert random "mountain" image to grayscale and save as "myphoto" to the 'documents' directory

        $ wallsy random -q="mountain" effects --grayscale save --dest="~/documents" --name="myphoto"

    For detailed help text run the --help modifier with the specified command, e.g.

    $ wallsy background --help
    """

    pass


@cli.command()
@click.option("--file", "-f")
@click.option("--url", "-u")
def new(file, url):
    """
    Retrieve a new image from either local filesystem or URL (must point directly to an accessible image resource).
    """

    # Handle usage errors outside of the callback so that these are caught immediately on invocation.
    # At least one (but not both) of --file or --url are required.

    if file is None and url is None:
        msg = """"new" requires either a file path or url pointing to an image. Please provide either --file or --url options. 
        
        file: wallsy new --file="/path/to/my/photo.jpg"
        url:  wallsy new --url="https://www.example.com/myphoto.jpg"
        """
        raise click.UsageError(msg)

    if file is not None and url is not None:
        msg = """"new" received conflicting options: --file and --url. Please choose one option and try again. 
        """

        raise click.UsageError(msg)

    def _get_new_image():
        """
        Callback for the new image subcommand.
        """

        if url:
            dest_path = "~/wallsy_test/my_img.jpg"
            try:
                image_handler.download_image(url, file_path=dest_path)
            except image_handler.ImageDownloadError as error:
                raise click.ClickException(str(error))

        return file or dest_path

    return _get_new_image


@cli.command(name="random")
@click.option("--query", "-q")
def random(query):
    """
    Generate a random image from source (default: Unsplash)
    """

    def _random():
        return "This is random"

    return _random


@cli.command(name="effect")
def apply_effects():
    """
    Apply one or more effects to the image.
    """

    def _apply_effects():
        """Callback for the effect subcommand"""
        return "effect "

    return _apply_effects


@cli.command(name="desktop")
def update_desktop_background():
    """
    Update the desktop background with the specified image.
    """

    def _update_desktop_background():
        """Callback for the background subcommand"""
        return "background "

    return _update_desktop_background


@cli.result_callback()
def process_pipeline(callbacks):
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
    check for incompatible subcommand combinations. incompatible subcommands are the following:
        RANDOM and NEW:
            both subcommands are designed to provide a filepath and ensure that a valid
            image exists at that path.
    """

    "TODO: perform subcommand compatibility check"

    """
    Pipeline ordering

    Image processing follows this general flow: 
    1) get an image -> 2) perform actions on image -> 3) peform actions on system (e.g. desktop background)
    
    1) must come first because all other actions require a valid image and existing filepath in order to 
    execute successfully. 
    """

    "TODO: setup pipeline ordering in an iterable then use this to execute callback functions in specified order"

    for callback in callbacks:
        print(callback.__name__)
        x = callback()
        print(x)
