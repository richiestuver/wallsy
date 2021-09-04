"""
console.py - provide application level access to a Rich Console object for
handling writing to stdout and stderr. 
"""

from rich.console import Console

console = Console()
error_console = Console(stderr=True, style="red")
