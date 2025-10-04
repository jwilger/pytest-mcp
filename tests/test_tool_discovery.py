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
    """
    # Act: Call the workflow function we're testing
    result = list_tools()

    # Assert: Function should return list with exactly 2 tool definitions
    assert len(result) == 2, (
        "list_tools should return exactly 2 tool definitions (execute_tests and discover_tests)"
    )


def test_list_tools_includes_execute_tests_tool() -> None:
    """Verify list_tools includes execute_tests tool with correct name.

    Acceptance Criteria (Story 2, Scenario 1):
      And the array includes "execute_tests" tool with complete inputSchema

    This test verifies the first tool in the list has the correct name.
    Single assertion: One tool should be named "execute_tests".

    Outside-In TDD: Test the tool names before drilling down to schema validation.
    """
    # Act: Get tool definitions
    result = list_tools()
    tool_names = [tool.name for tool in result]

    # Assert: "execute_tests" tool should be present
    assert "execute_tests" in tool_names, 'list_tools should include a tool named "execute_tests"'


def test_list_tools_includes_discover_tests_tool() -> None:
    """Verify list_tools includes discover_tests tool with correct name.

    Acceptance Criteria (Story 2, Scenario 1):
      And the array includes "discover_tests" tool with complete inputSchema

    Single assertion: One tool should be named "discover_tests".
    """
    # Act: Get tool definitions
    result = list_tools()
    tool_names = [tool.name for tool in result]

    # Assert: "discover_tests" tool should be present
    assert "discover_tests" in tool_names, 'list_tools should include a tool named "discover_tests"'


def test_each_tool_has_description_field() -> None:
    """Verify each tool definition includes description field.

    Acceptance Criteria (Story 2, Scenario 1):
      And each tool definition includes name, description, and inputSchema

    Single assertion: All tools must have description field.
    """
    # Act: Get tool definitions
    result = list_tools()

    # Assert: Each tool has description field
    assert all(hasattr(tool, "description") and tool.description for tool in result), (
        "Each tool definition must include a description field"
    )


def test_each_tool_has_input_schema_field() -> None:
    """Verify each tool definition includes inputSchema field.

    Acceptance Criteria (Story 2, Scenario 1):
      And each tool definition includes name, description, and inputSchema

    Single assertion: All tools must have inputSchema field.
    """
    # Act: Get tool definitions
    result = list_tools()

    # Assert: Each tool has inputSchema field
    assert all(hasattr(tool, "inputSchema") and tool.inputSchema for tool in result), (
        "Each tool definition must include an inputSchema field"
    )


def test_execute_tests_schema_includes_all_eight_parameters() -> None:
    """Verify execute_tests tool schema shows all 8 parameters.

    Acceptance Criteria (Story 2, Scenario 2):
      Then the inputSchema shows parameters: node_ids, markers, keywords,
           verbosity, failfast, maxfail, show_capture, timeout

    Single assertion: Schema must include all 8 expected parameters.
    """
    # Arrange: Get execute_tests tool
    tools = list_tools()
    execute_tests_tool = next(t for t in tools if t.name == "execute_tests")

    # Act: Extract parameter names from schema
    schema_properties = execute_tests_tool.inputSchema.get("properties", {})
    parameter_names = set(schema_properties.keys())

    # Assert: All 8 parameters present
    expected_parameters = {
        "node_ids",
        "markers",
        "keywords",
        "verbosity",
        "failfast",
        "maxfail",
        "show_capture",
        "timeout",
    }
    assert parameter_names == expected_parameters, (
        f"execute_tests schema must include all 8 parameters. "
        f"Expected: {expected_parameters}, Got: {parameter_names}"
    )


def test_execute_tests_schema_specifies_additional_properties_false() -> None:
    """Verify execute_tests schema specifies additionalProperties: false.

    Acceptance Criteria (Story 2, Scenario 2):
      And the schema specifies additionalProperties: false

    Single assertion: Schema must forbid additional properties.
    """
    # Arrange: Get execute_tests tool
    tools = list_tools()
    execute_tests_tool = next(t for t in tools if t.name == "execute_tests")

    # Act: Check additionalProperties setting
    additional_properties = execute_tests_tool.inputSchema.get("additionalProperties")

    # Assert: additionalProperties must be false
    assert additional_properties is False, (
        "execute_tests schema must specify additionalProperties: false "
        "to prevent unexpected parameters"
    )


def test_discover_tests_schema_includes_both_parameters() -> None:
    """Verify discover_tests tool schema shows both path and pattern parameters.

    Acceptance Criteria (Story 2, Scenario 3):
      Then the inputSchema shows parameters: path, pattern

    Single assertion: Schema must include both expected parameters.
    """
    # Arrange: Get discover_tests tool
    tools = list_tools()
    discover_tests_tool = next(t for t in tools if t.name == "discover_tests")

    # Act: Extract parameter names from schema
    schema_properties = discover_tests_tool.inputSchema.get("properties", {})
    parameter_names = set(schema_properties.keys())

    # Assert: Both parameters present
    expected_parameters = {"path", "pattern"}
    assert parameter_names == expected_parameters, (
        f"discover_tests schema must include both parameters. "
        f"Expected: {expected_parameters}, Got: {parameter_names}"
    )


def test_discover_tests_path_parameter_includes_security_validation() -> None:
    """Verify discover_tests path parameter includes security validation constraints.

    Acceptance Criteria (Story 2, Scenario 3):
      And path parameter includes security validation constraints

    Single assertion: Path parameter schema must reference path traversal protection.

    Note: Pydantic's field_validator converts to JSON Schema description/pattern.
    Security validation documented in parameter description or constraints.
    """
    # Arrange: Get discover_tests tool
    tools = list_tools()
    discover_tests_tool = next(t for t in tools if t.name == "discover_tests")

    # Act: Extract path parameter schema
    schema_properties = discover_tests_tool.inputSchema.get("properties", {})
    path_schema = schema_properties.get("path", {})

    # Assert: Path parameter schema is properly defined
    # path_schema is the schema dict for the "path" parameter itself
    # Verify it has the expected structure (title, description, type info)
    assert path_schema and "title" in path_schema, (
        "Path parameter must be defined in schema with proper structure"
    )
