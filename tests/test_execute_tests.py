"""Tests for test execution with parameter support (Story 4).

Outside-In TDD: Start with highest-level acceptance test for test execution.
Test the workflow function directly before drilling down to components.
"""

from pytest_mcp.domain import ExecuteTestsParams, ExecuteTestsResponse, execute_tests


def test_execute_tests_with_no_parameters_returns_execution_response() -> None:
    """Verify execute_tests returns ExecuteTestsResponse for all tests.

    Acceptance Criteria (Story 4, Scenario 1):
      Given a project with passing pytest tests
      When the agent calls execute_tests with no parameters
      Then the server executes pytest for entire suite
      And the response includes exit_code 0
      And summary shows all tests passed with total count and duration
      And tests array includes minimal details for each passing test

    This is the highest-level integration test for the test execution workflow.
    Single assertion: The function should return an ExecuteTestsResponse object.

    Expected to FAIL: execute_tests workflow function does not exist yet.
    Compiler will demand we create it in domain.py.
    """
    # Act: Call the workflow function we're testing
    params = ExecuteTestsParams()
    result = execute_tests(params)

    # Assert: Function should return ExecuteTestsResponse object
    assert isinstance(result, ExecuteTestsResponse), (
        "execute_tests should return an ExecuteTestsResponse object"
    )
