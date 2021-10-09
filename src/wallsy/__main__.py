"""
__main__.py

This file adds support for running wallsy as a python module instead of invoking the "wallsy" command line entrypoint.

See the following for a nice high level overview of what __main__ is intended for:

https://stackoverflow.com/questions/4042905/what-is-main-py
https://docs.python.org/3/using/cmdline.html#cmdoption-m

"""


import wallsy.cli_utils.utils as utils
from wallsy.cli import cli


def main():

    commands = utils.import_commands()
    utils.attach_commands(cli, commands)
    cli()


if __name__ == "__main__":
    main()
