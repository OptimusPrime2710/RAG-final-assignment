from rag_framework import __version__
from rag_framework.cli import main


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_foundation(capsys) -> None:
    assert main([]) == 0
    assert "usage:" in capsys.readouterr().out
