"""Tests for MCP server initialization (Story 1).

Outside-In TDD: Start with highest-level acceptance test for successful initialization.
Test the workflow function directly before drilling down to components.
"""

import pytest

from pytest_mcp.domain import ServerCapabilities, ServerInfo, initialize_server


def test_initialize_server_succeeds_with_supported_protocol_version() -> None:
    """Verify initialize_server returns valid response for supported protocol version.

    Acceptance Criteria (Story 1, Scenario 1):
      Given an AI agent with MCP client capability
      When the agent sends MCP initialize request with protocol version "2024-11-05"
      Then the server responds with protocol version "2024-11-05"
      And the server includes serverInfo with name "pytest-mcp" and version number
      And the server indicates capabilities for tools and resources

    This is the highest-level integration test for the initialization workflow.
    Single assertion: The function should return a tuple (not raise NotImplementedError).
    """
    # Act: Call the workflow function we're testing
    result = initialize_server(protocol_version="2024-11-05")

    # Assert: Function should return a tuple of (ProtocolVersion, ServerInfo, ServerCapabilities)
    assert isinstance(
        result, tuple
    ), "initialize_server should return tuple of validated domain types"
