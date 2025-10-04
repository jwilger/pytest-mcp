"""Tests for test execution with parameter support (Story 4).

Outside-In TDD: Start with highest-level acceptance test for test execution.
Test the workflow function directly before drilling down to components.
"""

from pytest_mcp.domain import ExecuteTestsParams, ExecuteTestsResponse, execute_tests


def test_execute_tests_with_no_parameters_returns_execution_response() -> None:
    """Verify execute_tests returns ExecuteTestsResponse for all tests.

    Acceptance Criteria (Story 4, Scenario 1):
      Given a project with passing pytest tests
      When the agent calls execute_tests for fixture tests
      Then the server executes pytest for specified tests
      And the response includes exit_code 0
      And summary shows all tests passed with total count and duration
      And tests array includes minimal details for each passing test

    This is the highest-level integration test for the test execution workflow.
    Single assertion: The function should return an ExecuteTestsResponse object.
    """
    # Act: Call the workflow function targeting fixture tests
    params = ExecuteTestsParams(node_ids=["tests/fixtures/sample_tests/"])
    result = execute_tests(params)

    # Assert: Function should return ExecuteTestsResponse object
    assert isinstance(result, ExecuteTestsResponse), (
        "execute_tests should return an ExecuteTestsResponse object"
    )


def test_execute_tests_summary_total_reflects_actual_test_count() -> None:
    """Verify summary.total matches actual number of tests executed.

    Acceptance Criteria (Story 4, Scenario 1):
      Given a project with pytest tests (both passing and failing)
      When the agent calls execute_tests for fixture tests
      Then summary shows total count matching all tests executed

    TDD Round 2: Verify summary contains accurate test count from pytest output.
    The fixture directory tests/fixtures/sample_tests/ contains exactly 3 tests:
      - test_passing (passes)
      - test_another_passing (passes)
      - test_failing (fails)

    Single assertion: summary.total should equal 3 (the actual test count).
    """
    # Arrange: Create parameters for executing fixture tests
    params = ExecuteTestsParams(node_ids=["tests/fixtures/sample_tests/"])

    # Act: Execute tests
    result = execute_tests(params)

    # Assert: Result is success response (not error)
    assert isinstance(result, ExecuteTestsResponse)

    # Assert: Summary total should match all 3 fixture tests
    assert result.summary.total == 3, (
        f"Expected summary.total to be 3 (matching fixture test count), "
        f"but got {result.summary.total}"
    )

    # Assert: Summary should reflect 2 passed, 1 failed
    assert result.summary.passed == 2, (
        f"Expected summary.passed to be 2, but got {result.summary.passed}"
    )
    assert result.summary.failed == 1, (
        f"Expected summary.failed to be 1, but got {result.summary.failed}"
    )


def test_execute_tests_filters_by_node_ids() -> None:
    """Verify node_ids parameter filters which tests execute.

    Acceptance Criteria (Story 4, Scenario 2):
      Given a project with multiple pytest tests
      When the agent calls execute_tests with specific node_ids
      Then only the specified tests execute
      And summary.total reflects only the filtered test count

    TDD Round 3: Verify execute_tests respects node_ids parameter filtering.
    The fixture directory tests/fixtures/sample_tests/ contains exactly 2 tests:
      - test_passing
      - test_another_passing

    When node_ids specifies only test_passing, exactly 1 test should execute.

    Single assertion: summary.total should equal 1 (only the specified test).
    """
    # Arrange: Create parameters targeting only one specific test
    params = ExecuteTestsParams(
        node_ids=["tests/fixtures/sample_tests/test_sample.py::test_passing"]
    )

    # Act: Execute tests with node_ids filter
    result = execute_tests(params)

    # Assert: Result is success response (not error)
    assert isinstance(result, ExecuteTestsResponse)

    # Assert: Summary total should be 1 (only the specified test executed)
    assert result.summary.total == 1, (
        f"Expected summary.total to be 1 when filtering by node_ids=['test_passing'], "
        f"but got {result.summary.total}. "
        "The execute_tests implementation should pass node_ids to pytest command "
        "instead of executing all tests in the hardcoded directory."
    )


def test_execute_tests_captures_failed_test_details() -> None:
    """Verify failed tests include traceback and message.

    Acceptance Criteria (Story 4, Scenario 2):
      Given a project with a failing pytest test
      When the agent calls execute_tests for that specific failing test
      Then the response includes exit_code 1
      And summary shows failed count
      And tests array includes traceback and message for the failed test

    TDD Round 4: Verify execute_tests captures failure details for AI agents.
    This is CRITICAL for the core TDD use case - AI agents need failure information
    to understand what went wrong and how to fix it.

    The fixture test_failing intentionally fails with assertion error.

    Single assertion: Failed test should have a non-None message field.
    """
    # Arrange: Create parameters targeting the specific failing test
    params = ExecuteTestsParams(
        node_ids=["tests/fixtures/sample_tests/test_sample.py::test_failing"]
    )

    # Act: Execute the failing test
    result = execute_tests(params)

    # Assert: Result is success response (not error - pytest ran successfully)
    assert isinstance(result, ExecuteTestsResponse), (
        "execute_tests should return ExecuteTestsResponse even when tests fail"
    )

    # Assert: Exit code should be 1 (pytest exit code for test failures)
    assert result.exit_code == 1, (
        f"Expected exit_code 1 for failed test, but got {result.exit_code}"
    )

    # Assert: Summary should reflect the failure
    assert result.summary.failed == 1, (
        f"Expected summary.failed to be 1, but got {result.summary.failed}"
    )

    # Assert: Should have exactly one test in results array
    assert len(result.tests) == 1, f"Expected 1 test in results, but got {len(result.tests)}"

    # Assert: Failed test should have error message (MAIN ASSERTION)
    failed_test = result.tests[0]
    assert failed_test.outcome == "failed", (
        f"Expected outcome 'failed', but got '{failed_test.outcome}'"
    )
    assert failed_test.message is not None, (
        "Failed test should have error message for AI agent debugging. "
        f"Test: {failed_test.node_id}, Message: {failed_test.message}"
    )
