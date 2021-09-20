"""
WallsyStream 

This module defines the WallsyStream dataclass, which is a wrapper around a 'stream' iterator
that is used as the input stream for image processing and other subcommands in Wallsy. The 
WallsyStream defines other metadata related specifically to the stream that subcommands can
use to customize their actions. For example, the 'every' command uses 'repeat' to signal 
to the callback processor that callback sequence should be repeated.
"""

from dataclasses import dataclass
from collections.abc import Iterable


@dataclass
class WallsyStream:
    """
    Used to store application data for purpose of passing around subcommands. Currently stores the
    existing config settings (contains common directories) and the initial input file stream.
    """

    stream: Iterable = ()  # empty iterator
    repeat: bool = False
