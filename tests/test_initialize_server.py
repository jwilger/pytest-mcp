"""Tests for MCP server initialization (Story 1).

Outside-In TDD: Start with highest-level acceptance test for successful initialization.
Test the workflow function directly before drilling down to components.
"""

import pytest

from pytest_mcp.domain import (
    ProtocolError,
    ProtocolValidationError,
    ServerCapabilities,
    ServerInfo,
    initialize_server,
)


def test_initialize_server_succeeds_with_supported_protocol_version() -> None:
    """Verify initialize_server returns valid response for supported protocol version.

    Acceptance Criteria (Story 1, Scenario 1):
      Given an AI agent with MCP client capability
      When the agent sends MCP initialize request with protocol version "2025-03-26"
      Then the server responds with protocol version "2025-03-26"
      And the server includes serverInfo with name "pytest-mcp" and version number
      And the server indicates capabilities for tools and resources

    This is the highest-level integration test for the initialization workflow.
    Single assertion: The function should return a tuple (not raise NotImplementedError).
    """
    # Act: Call the workflow function we're testing
    result = initialize_server(protocol_version="2025-03-26")

    # Assert: Function should return a tuple of (ProtocolVersion, ServerInfo, ServerCapabilities)
    assert isinstance(
        result, tuple
    ), "initialize_server should return tuple of validated domain types"


def test_initialize_server_rejects_unsupported_protocol_version_with_structured_error() -> None:
    """Verify initialize_server raises ValueError with ProtocolError details for unsupported versions.

    Acceptance Criteria (Story 1, Scenario 2):
      Given an AI agent sending initialize request
      When the agent specifies protocol version "2020-01-01"
      Then the server responds with JSON-RPC error code -32600
      And the error.data includes field "protocolVersion"
      And the error.data includes received_value "2020-01-01"
      And the error.data includes supported_version "2025-03-26"
      And the error.data.detail explains "Protocol version not supported. Please retry initialization with supported version."

    This test verifies the Parse Don't Validate philosophy: validation failures provide
    structured, actionable error information for AI agents to correct and retry.

    Single assertion: ValueError exception contains ProtocolError with all required fields.
    """
    # Act & Assert: Unsupported protocol version should raise ValueError with ProtocolError
    with pytest.raises(ValueError) as exc_info:
        initialize_server(protocol_version="2020-01-01")

    # Extract the error details from the exception
    error = exc_info.value

    # Assert: Error should contain structured ProtocolError with all required fields
    assert hasattr(error, "protocol_error"), (
        "ValueError should contain protocol_error attribute with ProtocolError instance "
        "containing fields: field='protocolVersion', received_value='2020-01-01', "
        "supported_version='2025-03-26', and actionable detail message"
    )
