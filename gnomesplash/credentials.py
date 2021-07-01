"""
Unsplash Credentials Handler

Handle API key retrieval from OS environment. Uses a .env file located in top level of project
directory in order to store and retrieve user's API key. 
"""

import os

from dotenv import load_dotenv


def retrieve_api_key() -> str:
    """
    Attempt to get the user's API key from environment.
    """

    load_dotenv()


def set_api_key() -> None:
    """
    Set the api_key to value specified by user. API key is written to UNSPLASH_KEY in .env file.
    """

    pass


def require_api_key():
    """
    Decorator function passes in the API key to a wrapped function containing an API call. If API
    key is not set, raise error.
    """

    pass
