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


def test_discover_tests_filters_by_path() -> None:
    """Verify discover_tests filters tests by specified path.

    Acceptance Criteria (Story 3, Scenario 2):
      Given a project with tests in tests/unit/ and tests/integration/
      When the agent calls discover_tests with path "tests/unit/"
      Then the server responds with tests only from tests/unit/ directory
      And tests from tests/integration/ are not included
      And the count reflects only unit tests

    Adaptation for current structure:
      Using existing test files, verify that path parameter filters to
      specific file. When path="tests/test_test_discovery.py", only tests
      from this file should be discovered.

    Single assertion: All discovered tests should be from the specified path.

    Expected to PASS: Implementation already passes path to pytest command.
    """
    # Act: Discover tests from specific file
    params = DiscoverTestsParams(path="tests/test_test_discovery.py")
    result = discover_tests(params)

    # Assert: All discovered tests should be from the specified file
    assert all(
        test.file == "tests/test_test_discovery.py" for test in result.tests
    ), "All discovered tests should be from the specified path"


def test_discover_tests_filters_by_pattern() -> None:
    """Verify discover_tests filters tests by specified pattern.

    Acceptance Criteria (Story 3, Scenario 3):
      Given a project with test files matching pattern *_spec.py
      When the agent calls discover_tests with pattern "*_spec.py"
      Then the server discovers tests from *_spec.py files
      And test_*.py files are not included
      And the response includes all matching test functions

    Test Strategy:
      Since we only have test_*.py files in this project (no *_spec.py files),
      we test pattern filtering by specifying a non-matching pattern.
      When pattern="*_spec.py", NO tests should be discovered because we
      don't have any files matching that pattern.

    Single assertion: count should be 0 when pattern doesn't match any files.

    Expected to FAIL: Implementation doesn't use pattern parameter yet.
    Currently ignores pattern and discovers all test_*.py files.
    """
    # Act: Discover tests with pattern that doesn't match our test files
    params = DiscoverTestsParams(pattern="*_spec.py")
    result = discover_tests(params)

    # Assert: Should find NO tests because pattern doesn't match our files
    assert result.count == 0, (
        "discover_tests should find 0 tests when pattern '*_spec.py' doesn't "
        "match any files (we only have test_*.py files)"
    )
