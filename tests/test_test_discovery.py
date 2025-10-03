"""Tests for test discovery without execution (Story 3).

Outside-In TDD: Start with highest-level acceptance test for test discovery.
Test the workflow function directly before drilling down to components.
"""

from pytest_mcp.domain import DiscoverTestsResponse, discover_tests


def test_discover_tests_returns_response_object() -> None:
    """Verify discover_tests returns DiscoverTestsResponse object.

    Acceptance Criteria (Story 3, Scenario 1):
      Given a Python project with pytest tests in tests/ directory
      When the agent calls discover_tests with default parameters
      Then the server responds with array of discovered tests
      And each test includes node_id, module, class, function, file, and line
      And the response includes total count of discovered tests
      And collection_errors array is empty when discovery succeeds

    This is the highest-level integration test for the test discovery workflow.
    Single assertion: The function should return a DiscoverTestsResponse object.

    Expected to FAIL: discover_tests workflow function does not exist yet.
    Compiler will demand we create it in domain.py.
    """
    # Act: Call the workflow function we're testing
    result = discover_tests()

    # Assert: Function should return DiscoverTestsResponse object
    assert isinstance(result, DiscoverTestsResponse), (
        "discover_tests should return a DiscoverTestsResponse object"
    )
