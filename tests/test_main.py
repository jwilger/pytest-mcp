"""Tests for main module."""

from pytest import CaptureFixture

from pytest_mcp.main import main


def test_main_prints_hello_world(capsys: CaptureFixture[str]) -> None:
    """Verify main() prints Hello, world."""
    main()
    captured = capsys.readouterr()
    assert captured.out == "Hello, world\n"


def test_cli_main_function_exists() -> None:
    """Verify cli_main() entry point exists per ADR-012."""
    from pytest_mcp.main import cli_main

    assert callable(cli_main)
