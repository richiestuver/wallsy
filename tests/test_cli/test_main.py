from subprocess import run


def test_launch_as_command_success(test_image):

    result = run(f"wallsy --file {test_image} _test".split(" "))
    assert result.returncode == 0


def test_launch_as_module_success(test_image):

    # make sure to provide a valid wallsy command or the return code won't be zero
    result = run(f"python3 -m wallsy --file {test_image} _test".split(" "))
    assert result.returncode == 0
