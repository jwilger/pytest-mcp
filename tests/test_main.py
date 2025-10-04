"""Tests for main module."""

import tomllib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_mcp.main import main


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


@patch("pytest_mcp.main.stdio_server")
@patch("pytest_mcp.main.server.run", new_callable=AsyncMock)
def test_main_uses_stdio_server_lifecycle(
    mock_server_run: AsyncMock,
    mock_stdio_server: MagicMock,
) -> None:
    """Verify main() uses stdio_server() lifecycle per ADR-011."""
    import asyncio

    # Mock stdio_server context manager
    mock_read_stream = MagicMock()
    mock_write_stream = MagicMock()
    mock_stdio_server.return_value.__aenter__.return_value = (
        mock_read_stream,
        mock_write_stream,
    )

    # Call main()
    asyncio.run(main())

    # Verify stdio_server was used
    mock_stdio_server.assert_called_once()

    # Verify server.run was called
    mock_server_run.assert_called_once()
    call_args = mock_server_run.call_args[0]
    assert call_args[0] == mock_read_stream
    assert call_args[1] == mock_write_stream
    # Third arg is InitializationOptions - just verify it's not None
    assert call_args[2] is not None
