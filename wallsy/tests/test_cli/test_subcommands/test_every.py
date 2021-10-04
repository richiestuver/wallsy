from click.testing import CliRunner
from wallsy.cli import cli

runner = CliRunner()


# def test_every(test_image):

#     result = runner.invoke(cli, ["--file", str(test_image), "_test", "every", "2"])
#     print(result.stdout)
#     assert result.exit_code == 0
