"""MCP server entry point for pytest-mcp.

This module provides the MCP server initialization and main entry point.
Domain types and workflow functions are defined in the domain module.
"""

from pytest_mcp import domain  # noqa: F401 - imported for type availability


def main() -> None:
    """Start the MCP server.

    Server initialization workflow implemented in domain.initialize_server.
    Full implementation deferred to TDD phase.
    """
    print("Hello, world")  # noqa: T201 - temporary skeleton output


if __name__ == "__main__":
    main()
