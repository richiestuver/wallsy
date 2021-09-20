from dataclasses import dataclass
from collections.abc import Iterable
from wallsy.config import WallsyConfig


@dataclass
class WallsyStream:
    """
    Used to store application data for purpose of passing around subcommands. Currently stores the
    existing config settings (contains common directories) and the initial input file stream.
    """

    stream: Iterable = ()  # empty iterator
    repeat: bool = False
