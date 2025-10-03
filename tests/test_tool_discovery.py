"""Tests for MCP tool discovery (Story 2).

Outside-In TDD: Start with highest-level acceptance test for tool listing.
Test the workflow function directly before drilling down to components.
"""

from pytest_mcp.domain import list_tools


def test_list_tools_returns_array_with_two_tool_definitions() -> None:
    """Verify list_tools returns array containing execute_tests and discover_tests tools.

    Acceptance Criteria (Story 2, Scenario 1):
      Given an initialized MCP connection
      When the agent sends tools/list request
      Then the server responds with array of tool definitions
      And the array includes "execute_tests" tool with complete inputSchema
      And the array includes "discover_tests" tool with complete inputSchema

    This is the highest-level integration test for the tool discovery workflow.
    Single assertion: The function should return a list with exactly 2 tool definitions.

    Expected to FAIL: list_tools workflow function does not exist yet.
    Compiler will demand we create it in domain.py.
    """
    # Act: Call the workflow function we're testing
    result = list_tools()

    # Assert: Function should return list with exactly 2 tool definitions
    assert len(result) == 2, (
        "list_tools should return exactly 2 tool definitions "
        "(execute_tests and discover_tests)"
    )
