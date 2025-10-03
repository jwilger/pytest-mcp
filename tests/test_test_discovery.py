"""Tests for test discovery without execution (Story 3).

Outside-In TDD: Start with highest-level acceptance test for test discovery.
Test the workflow function directly before drilling down to components.
"""

from pytest_mcp.domain import DiscoverTestsParams, DiscoverTestsResponse, discover_tests


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
    params = DiscoverTestsParams()
    result = discover_tests(params)

    # Assert: Function should return DiscoverTestsResponse object
    assert isinstance(result, DiscoverTestsResponse), (
        "discover_tests should return a DiscoverTestsResponse object"
    )


def test_discover_tests_finds_existing_tests() -> None:
    """Verify discover_tests finds actual tests in project.

    Acceptance Criteria (Story 3, Scenario 1):
      Given a Python project with pytest tests in tests/ directory
      When the agent calls discover_tests with default parameters
      Then the server responds with array of discovered tests

    This test itself exists in tests/ so discover_tests should find at least
    the tests in this file. Single assertion: count should be greater than zero.

    Expected to FAIL: Currently discover_tests returns count=0, but real pytest
    --collect-only should discover at least the tests in this file.
    """
    # Act: Call discover_tests to discover tests in the project
    params = DiscoverTestsParams()
    result = discover_tests(params)

    # Assert: Should find at least one test in the project
    assert result.count > 0, (
        "discover_tests should find at least one test in the project "
        "(this test file exists in tests/)"
    )
