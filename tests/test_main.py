"""Tests for main module."""

import asyncio
from unittest.mock import MagicMock, patch

from pytest import CaptureFixture

from pytest_mcp.main import main


def test_main_prints_hello_world(capsys: CaptureFixture[str]) -> None:
    """Verify main() prints Hello, world."""
    asyncio.run(main())
    captured = capsys.readouterr()
    assert captured.out == "Hello, world\n"


def test_cli_main_function_exists() -> None:
    """Verify cli_main() entry point exists per ADR-012."""
    from pytest_mcp.main import cli_main

    assert callable(cli_main)


@patch("pytest_mcp.main.asyncio.run")
def test_cli_main_calls_asyncio_run_with_main(mock_asyncio_run: MagicMock) -> None:
    """Verify cli_main() calls asyncio.run(main()) per ADR-012."""
    from pytest_mcp.main import cli_main

    cli_main()

    assert mock_asyncio_run.called
