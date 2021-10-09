"""
wallsy console utilities

This module provides application-wide access to a Rich Console object for
handling writing to stdout and stderr. Themes are defined and may be more deeply
integrated into console output in future versions of wallsy.
"""

from sys import exit
from functools import wraps

from rich.console import Console
from rich.theme import Theme

wallsy_theme = Theme(
    {"warning": "orange_red1", "fail": "bold red", "confirm": "", "describe": ""}
)

console = Console(theme=wallsy_theme)
error_console = Console(theme=wallsy_theme, stderr=True)
log_console = Console(theme=wallsy_theme)
machine_console = Console(theme=wallsy_theme)


"""
Formatting helpers
"""


def warn(msg: str):
    """
    Format msg and print to stderr.
    """

    error_console.print(
        f":exclamation_mark-emoji: [bold]warning: [/] {msg}", style="warning"
    )


def describe(msg: str, **kwargs):
    """
    Format descriptive msg and print to stdout.
    """

    console.print(f"{msg}", style="describe", **kwargs)


def confirm_success(msg: str, **kwargs):
    """
    Format confirmation msg and print to stdout. Accept any additional kwargs that console.print from
    rich module exposes.
    """

    console.print(f"{msg}", style="confirm", **kwargs)


def fail(msg: str):
    """
    Format failure msg and print to stdout.
    """

    error_console.print(f":x-emoji: failed. {msg}", style="fail")


def log(msg: str):
    """
    Format msg and print to stdout or log file (default: stdout)
    """

    raise NotImplementedError
