"""
Unsplash Source API - URL Builder

This module is a wrapper around the Unsplash Source public unauthenticated API (supports only GET requests to fetch images). 
These functions build appropriately formatted URLs and pass to the download_image function in the image handler.
The download_image function handles all of the request and imag validation and keeps this file limited
to constructing well-formed GET requests.

The source.unsplash.com API supports only GET requests on a limited number of endpoints. When the endpoint is hit, 
client is redirected to an image resource. 
"""

from urllib.parse import quote_plus
from functools import wraps
from inspect import signature
from collections import namedtuple


def base_url(func):
    """
    Use this decorator to inject the base url into each get method. That way should the url change in the future
    it can be done in one place.
    """

    base_url = "https://source.unsplash.com"

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(base_url=base_url, *args, **kwargs)

    return wrapper


def url_path(url_path: str):
    """
    Use this decorator to inject the correct path component for the intended endpoint.
    """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            return func(url_path=url_path, *args, **kwargs)

        return inner

    return wrapper


def query(func):
    """
    Use this decorator to inject a string of comma separated keywords as the query string to include in GET request. Functions decorated with query must specify a 'keywords' keyword argument as a list of strs for use in
    building a query string.The Unsplash Source API does not use key value pairs for this purpose and instead just a comma separated list so
    we build the query string manually and pass it into the download image function as a pre-built url.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        arguments: dict = signature(func).bind(*args, **kwargs).arguments
        keywords: list = arguments.get("keywords")

        query_string = ""
        if keywords is not None:
            query_string = quote_plus(
                "?" + ",".join(keywords), safe="/,?"
            )  # format required by Unsplash Source API

        return func(query=query_string, *args, **kwargs)

    return wrapper


def size(func):
    """This decorator grabs the dimensions of a photo as supplied in the function signature as a tuple
    and converts these to the proper string representation for the Unsplash Source endpoint."""

    @wraps(func)
    def wrapper(*args, **kwargs):

        arguments = signature(func).bind(*args, **kwargs).arguments

        dimensions = arguments.get("dimensions")

        size = ""
        if dimensions:
            size = quote_plus(f"{dimensions[0]}x{dimensions[1]}", safe="/")
        return func(size=size, *args, **kwargs)

    return wrapper


def make_unsplash_url(path_components: list[str], query: str = "") -> str:
    return "".join(["/".join(path_components).removesuffix("/"), query])


@base_url
@url_path("random")
@query
@size
def random_photo(
    keywords: list[str] = None, dimensions: tuple[int, int] = None, *args, **kwargs
) -> str:
    """
    Request a random image from Unsplash. Search terms can be used to filter results.
    """

    base_url: str = kwargs.get("base_url")
    path: str = kwargs.get("url_path")
    query: str = kwargs.get("query")
    size: str = kwargs.get("size")

    return make_unsplash_url(path_components=[base_url, path, size], query=query)


@base_url
@url_path("featured")
@query
@size
def random_featured_photo(
    keywords: list[str] = None, dimensions: tuple[int, int] = None, *args, **kwargs
) -> str:

    base_url: str = kwargs.get("base_url")
    path: str = kwargs.get("url_path")
    query: str = kwargs.get("query")
    size: str = kwargs.get("size")

    # should end up with something like "https://source.unsplash.com/featured/1920x1080?water,lightning"
    # url = "".join(["/".join([base_url, path, size]).removesuffix('/'), query])
    return make_unsplash_url(path_components=[base_url, path, size], query=query)


@base_url
@url_path("user")
@size
def random_from_user(user_id: str, dimensions: tuple[int, int] = None, *args, **kwargs):

    base_url: str = kwargs.get("base_url")
    path: str = kwargs.get("url_path")
    size: str = kwargs.get("size")

    return make_unsplash_url(
        path_components=[base_url, path, quote_plus(user_id), size]
    )


@base_url
@url_path("collection")
@size
def random_from_collection(
    collection_id: str, dimensions: tuple[int, int] = None, *args, **kwargs
):
    base_url: str = kwargs.get("base_url")
    path: str = kwargs.get("url_path")
    size: str = kwargs.get("size")

    return make_unsplash_url(
        path_components=[base_url, path, quote_plus(collection_id), size]
    )


@base_url
@size
def specific_photo(photo_id: str, dimensions: tuple[int, int] = None, *args, **kwargs):
    base_url: str = kwargs.get("base_url")
    size: str = kwargs.get("size")

    return make_unsplash_url(path_components=[base_url, quote_plus(photo_id), size])


if __name__ == "__main__":
    print(random_photo())
    print()
    print(random_photo(keywords=["pizza", "donkey"]))
    print()
    print(random_photo(dimensions=(1920, 1080)))
    print()
    print(random_photo(keywords=["pizza", "donkey"], dimensions=(1920, 1080)))
    print()
    print(random_featured_photo())
    print()
    print(random_featured_photo(keywords=["water", "earth", "fire", "air"]))
    print()

    print(random_featured_photo(dimensions=(3, 4)))
    print()
    print(
        random_featured_photo(
            keywords=["water", "earth", "fire", "air"], dimensions=(3, 4)
        )
    )

    print(random_from_user(user_id="timmy"))
    print(random_from_collection(collection_id="12345"))
    print(specific_photo(photo_id="ashgavdwe"))

    print(random_from_user(user_id="timmy", dimensions=(100, 100)))
    print(random_from_collection(collection_id="12345", dimensions=(100, 100)))
    print(specific_photo(photo_id="ashgavdwe", dimensions=(100, 100)))

    print(
        random_featured_photo(
            keywords=["water", "earth", "fire", "air", "; DROP TABLES;"]
        )
    )
