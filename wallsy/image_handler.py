"""
Image Handler

Utilities for downloading and manipulating images. 

Downloading images: Supports only requests directly for network requests for image files specified
by URL, with no expectation of authentication or other API 
requests (searching for images on a service, etc). Such activities should be 
performed by the specific source handler.

Image manipulation: is intended only to support limited use cases
related to creating backgrounds/wallpapers for video streaming or 
desktop environment use. Other analogous use cases are welcome
but this is not intended to be a comprehensive photo manipulation program.
"""

from pathlib import Path
import io

from PIL import Image, ImageFilter, UnidentifiedImageError
import requests


class InvalidImageError(Exception):
    """
    Raised when a provided binary input file is not an image. Wrapper around the PIL
    UnidentifiedImageError for better identification of errors during debugging
    and custom error messaging.
    """

    pass


class ImageDownloadError(Exception):
    """
    Raised when an image download is unsuccessful.
    """

    pass


def validate_image(input) -> str:
    """
    Determine whether input is a valid image. PIL open method accepts a Path object, string, or file object (buffered stream).
    Uses PIL to attempt to open the file. The PIL method reads the content header to determine file type but doesn't
    actually load any of the contents in memory, so it should be safe to use as a validation method.
    See the PIL docs on identifying images for more info: https://pillow.readthedocs.io/en/stable/handbook/tutorial.html?highlight=identify#identify-image-files
    """

    try:
        with Image.open(input) as image:

            return image.format

    except UnidentifiedImageError:
        raise InvalidImageError(f"Input {str(input)} does not appear to be an image.")


def download_image(url: str, file_path: str) -> Path:
    """
        Download an image at specified url. This is an API agnostic function that does not
        take an API key for a particular service. Expectation is that resource is generally
        accesssible.
    .
        Attempt to save image at target file path. If file path does not exist, it will be created.
        Default location is user's home directory. Returns the location on filesystem where image was saved.

        If downloading image fails for one of various reasons, will raise an appropriate error instead of
        failing silently.

        If file already exists, do not overwrite.
    """

    destination_path = Path(file_path).expanduser().resolve()

    # prevent overwriting an existing file. this is a design decision to prevent unintentional deletions

    if not destination_path.exists():
        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            raise FileExistsError(f"Error trying to create {str(destination_path)}.")

    else:
        raise FileExistsError(f"File already exists at {destination_path}.")

    # now for the good stuff. get the raw image content and use the imaging library to save to file.
    # two main error conditions: bad http request or trying to access something that's not an image.

    try:

        """
        The get method from Requests automatically follows redirects (status codes 3XX) on your behalf and
        stores the intermediary responses in the response.history attribute. This is extremely
        useful for our use case where the typical source url won't be directly an image resource
        but rather include a redirect to the ultimate image. In other words we are getting
        redirect handling "out of the box" but have the ability to manage or inspect redirects
        later if we needed to. Note that passing "allow_redirects=False" to get() will disable this behavior.
        More info: https://docs.python-requests.org/en/latest/user/quickstart/#redirection-and-history
        """

        # TODO: implement timeout handling from requests module. default behavior is infinite (no timeout)

        r = requests.get(url)

    except requests.exceptions.RequestException as error:
        raise ImageDownloadError(str(error))

    # successful request but received a bad response from the server.
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ImageDownloadError(
            f"Download error: something went wrong trying to access {url} (status code {r.status_code})"
        )

    # successful request but did not get back image data as the response.
    try:
        with Image.open(io.BytesIO(r.content)) as image:

            if destination_path.suffix == "":
                destination_path = Path(f"{destination_path}.{image.format.lower()}")
            image.save(destination_path)

    except UnidentifiedImageError:
        raise ImageDownloadError(
            f"Download error: the target resource at {url} does not appear to be an image."
        )

    return destination_path


def blur(img_path: Path, value=50, blur_func=ImageFilter.GaussianBlur) -> Path:
    """
    Apply a gaussian blur to a given image. Original image is unmodified.

    blur_func accepts either ImageFilter.GaussianBlur or ImageFilter.BoxBlur
    """

    with Image.open(img_path) as image:
        blur_effect = blur_func(radius=value)
        # blur_effect = ImageFilter.BLUR
        img_blur = image.filter(filter=blur_effect)
        out = Path(f"{img_path.parent / img_path.stem}-blur{img_path.suffix}")
        img_blur.save(out)

        return out

def greyscale(img_path: Path, path_modifier: str = "greyscale") -> Path:
    """
    Convert image to greyscale. Image is not modified in place. A new image is written out to file.
    """

    with Image.open(img_path) as image:
        img_greyscale = image.convert(mode='L')  # 'L' corresponds to 8-bit greyscale
        out = Path(f"{img_path.parent / img_path.stem}-{path_modifier}{img_path.suffix}")
        img_greyscale.save(out)

        return out


def quantize(img_path: Path, path_modifier: str = "quanitize", colors:int = 16) -> Path:
    """
    Helper function wraps the PIL quantization method. Opens image and writes image and saves
    new quantized image at img_path with the addition of the path_modifier to identify the new file.

    This is most useful for "posterization" effect by reducing the color space down to a small number.
    According to this article from Adobe the human eye can most distinguish the effect when colors 
    are reduced to the range 1-35. https://www.adobe.com/creativecloud/photography/discover/posterize-photo.html
    
    Another simple overview of posterization: https://www.cambridgeincolour.com/tutorials/posterization.htm
    """

    with Image.open(img_path) as image:
        # Note: max coverage seems to get the most interesting results. need to read
        # about quantization methods to really understand the options better. See Pillow docs.
        img_quantized = image.quantize(colors=colors, method=Image.MAXCOVERAGE)
        # after quantization our mode is "P" which has an alpha layer, not supported by jpg. Force to save as png.
        out = Path(f"{img_path.parent / img_path.stem}-{path_modifier}{colors}.png")
        img_quantized.save(out)
    
        return out