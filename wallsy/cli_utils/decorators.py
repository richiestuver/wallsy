"""
wallsy Decorators

Use these decorators for converting simple functions that perform image manipulations
or other common operations into properly formed Wallsy subcommands. In general a candidate function
to use as a subcommand should accept a file path argument (and possibly other arguments) and return a file
path. In both cases the type of both the input arg and the return are pathlib.Path objects. The body of the
function should perform whatever image processing or other manipulation you want without worrying about
any other pipeline logic. 

The decorators provided here will convert these basic functions into proper pipeline processors on your
behalf. All functions that operate on an input path argument should use @make_generator to allow the 
function to operate on a stream of inputs. 

A function that by some means generates additional input (for example, calling an API 
or otherwise sourcing an image) should follow the same basic pattern  of accepting an input 
and returning an output. Call @extend_stream to transform this basic function into one that 
appends its new output to the existing input stream for the pipeline. 

Finally, all functions should use @make_callback to wrap the function in a new layer that will return
the original funtion as a callable for later invocation. 

Here's a sample of how this would look for a function that add a "sparkle" effect to images:

    @cli.command()
    @make_callback
    @make_generator
    def sparkle(file):
        '''Make the image sparkle'''

        file = make_it_sparkle(file, sparkle_amount=9000)
        return file

the above registers a new subcommand to the 'cli' group called 'sparkle' with no options. The 
command will process all files provided as input and add a sparkle effect:

    $ wallsy --file myfile1.jpg --file myfile2.jpg sparkle
    
"""

from stat import S_ISFIFO
from itertools import chain
from itertools import cycle
from functools import wraps
from functools import partial
from inspect import getcallargs

from wallsy.WallsyStream import WallsyStream
from wallsy.cli_utils.console import fail


def stream(func):
    """
    Take a function that generates output(s) (or passes through new input(s) directly as an output)
    and extend an existing stream to include these new outputs. This allows functions that don't operate
    on received input to instead provide new inputs to a pipeline.
    """

    @wraps(func)
    def wrapper(stream: WallsyStream, *args, **kwargs):
        @wraps(func)
        def inner():
            return (file for file in func(*args, **kwargs))

        stream.stream = (file for file in chain(stream.stream, inner()))
        return stream

    return wrapper


def generator(func):
    """
    Take a function that accepts and returns a single input parameter and convert it into
    a function that accepts an input stream and yields the return value of the original function.
    """

    @wraps(func)
    def wrapper(stream: WallsyStream, *args, **kwargs):

        stream.stream = (func(file, *args, **kwargs) for file in stream.stream)
        return stream

    return wrapper


def callback(func):
    """
    Receive a function (presumably, that does not itself return a function) and convert it into a new function that returns the
    original function as a callback function.

    The Wallsy CLI is built on a callback architecture. Subcommands are invoked on the command line, each of which return a callback function
    immediately upon invocation. Once all subcommands have been invoked, a separate "process callbacks" function iterates over each of the callback
    function objects and executes them. When a function is decorated with make_callback, the callback itself will have the
    same signature and behave exactly as the original function. The invoking the origianl function name, on the otherhand, merely returns the callback
    which now must be invoked to actually execute the original function body.

    It is possible to achieve the same behavior by manually defining an inner function within each subcommand function definition. Similar to:

        def my_command(cli_args):  # any args received from command line invocation

            # any actions that would be performed immediately upon command invocation here

            def my_callback(callback_args)  # any args required for callback but not supplied directly on command line

                # body of command logic in here, processed by callback processor at a later time

                return whatever_you_need_to_for_other_command_callbacks_etc

            return my_callback

    However, the benefit to using the callback factory pattern here is that it eliminates all of the boilerplate code for doing so and reduces the
    function body to only the logic necessary for performing the desired action of the command itsef.
    """

    @wraps(func)
    def _callback(*args, **kwargs):
        @wraps(func)
        def wrapper(*fargs, **fkwargs):
            new_func = partial(func, *args, **kwargs)
            return new_func(*fargs, **fkwargs)

        return wrapper

    return _callback


def require_file(func):
    """
    Decorator for callbacks that require a filename to be explicitly passed in order to perform
    desired action. This decorator abstracts checking for this parameter and raises the necessary exception.

    NOTE: getcallargs is deprecated, need to move to signature() call instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_args = getcallargs(func, *args, **kwargs)
        if func_args.get("file") is None:
            raise Exception(
                f"Command '{func.__name__}' did not receive a filename as part of pipeline. Did you run 'add' or 'random' to source an image?"
            )
        return func(*args, **kwargs)

    return wrapper


def catch_errors(func):
    """
    Catch and format errors with the "fail" console template and gracefully
    exit the application with an error code.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            fail(str(error))
            exit(1)

    return wrapper
