"""
console.py - provide application level access to a Rich Console object for
handling writing to stdout and stderr. 
"""

from rich.console import Console
from rich.theme import Theme

wallsy_theme = Theme(
    {"warning": "orange_red1", "fail": "bold red", "confirm": "bold", "describe": ""}
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

    error_console.print(f":warning-emoji:  {msg}", style="warning")


def describe(msg: str):
    """
    Format descriptive msg and print to stdout.
    """

    console.print(f"{msg}", style="describe")


def confirm(msg: str):
    """
    Format confirmation msg and print to stdout.
    """

    console.print(f":white_check_mark-emoji: {msg}", style="confirm")


def fail(msg: str):
    """
    Format failure msg and print to stdout.
    """

    error_console.print(f":x-emoji: {msg}", style="fail")


def log(msg: str):
    """
    Format msg and print to stdout or log file (default: stdout)
    """

    pass


if __name__ == "__main__":

    warn("this is a test warning.")
    fail("this is a total failure.")
    confirm("this one works")
    describe("this is a description")
