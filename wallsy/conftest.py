"""
conftest.py

Test configuration for wallsy tests.

Defines Pytest fixtures for supplying test data to tests across the entire
test suite. Fixtures used within only a single module are defined 
directly in that module. Conftest.py should only be used for universal
fixtures to avoid unnecessary performance hit. 
"""

from pathlib import Path
from itertools import cycle

import pytest


@pytest.fixture(scope="package")
def cycle_test_images() -> cycle:
    """
    Return cycle (like an infinitely repeating generator) that collects all available test images
    (Path objects pointing to location in test directory) so that we can iterate through them for testing.
    Note that Pytest fixture scope is set to 'module' so that this fixture (and thus, the image generator)
    is not torn down after each test.
    """

    # rglob is glob but appends **/ so we don't worry about relative pathing from execution dir and test_data
    # from pathlib docs: ** means recursively search across current and all subdirectories
    return cycle(Path().rglob("test_data/**/*.jpg"))


@pytest.fixture(scope="package")
def test_image(cycle_test_images) -> Path:
    """
    Returns the next Path object representing an image in the test_data folder.
    """

    return next(cycle_test_images)
