"""Tests for main module."""

import asyncio
import tomllib
from pathlib import Path
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


def test_console_script_entry_point_configured() -> None:
    """Verify pyproject.toml defines pytest-mcp console script per ADR-012."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    scripts = config.get("project", {}).get("scripts", {})
    assert "pytest-mcp" in scripts


def test_server_instance_exists() -> None:
    """Verify Server instance exists at module scope per ADR-011."""
    from mcp.server import Server

    from pytest_mcp.main import server

    assert isinstance(server, Server)
