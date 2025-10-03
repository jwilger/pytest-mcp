"""Tests for main module."""

from pytest import CaptureFixture

from pytest_mcp.main import main


def test_main_prints_hello_world(capsys: CaptureFixture[str]) -> None:
    """Verify main() prints Hello, world."""
    main()
    captured = capsys.readouterr()
    assert captured.out == "Hello, world\n"
