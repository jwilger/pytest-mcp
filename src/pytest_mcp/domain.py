"""Domain types for pytest-mcp server.

This module defines workflow functions and minimal nominal types following
the Parse Don't Validate philosophy. Types make illegal states unrepresentable
at the domain boundary.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class ProtocolError(BaseModel):
    """Validation error details for unsupported protocol versions.

    Follows STYLE_GUIDE.md validation error pattern (lines 628-669).
    Provides actionable information for AI agents to correct and retry.
    """

    field: str = Field(description="Parameter name that failed validation")
    received_value: str = Field(description="Value that failed validation")
    supported_version: str = Field(description="Version the server supports")
    detail: str = Field(description="Actionable message for correction")

    model_config = {"frozen": True}


class ProtocolValidationError(ValueError):
    """ValueError subclass carrying structured ProtocolError details.

    Enables Parse Don't Validate philosophy: validation failures provide
    actionable, structured error information for AI agents to correct and retry.

    Follows STYLE_GUIDE.md validation error pattern by attaching field-level
    validation details to exceptions.
    """

    def __init__(self, protocol_error: ProtocolError) -> None:
        """Create validation error with structured protocol error details.

        Args:
            protocol_error: Structured error with field, value, and correction guidance
        """
        self.protocol_error = protocol_error
        super().__init__(protocol_error.detail)


class ProtocolVersion(BaseModel):
    """MCP protocol version identifier.

    Validates protocol version using Pydantic field_validator per ADR-005.
    Parse Don't Validate: Only valid protocol versions can be constructed.
    """

    value: str = Field(description="Protocol version in YYYY-MM-DD format")

    @field_validator("value")
    @classmethod
    def validate_supported_version(cls, v: str) -> str:
        """Validate protocol version against supported version.

        Raises:
            ValueError: When protocol version is not supported
        """
        supported = "2025-03-26"
        if v != supported:
            raise ValueError(
                f"Protocol version {v} not supported. "
                f"Please retry initialization with supported version {supported}."
            )
        return v

    model_config = {"frozen": True}


class ServerInfo(BaseModel):
    """Server metadata included in initialization response.

    Contains server name and version number for AI agent compatibility checking.
    """

    name: str = Field(description="Server name identifier")
    version: str = Field(description="Server version number")

    model_config = {"frozen": True}


class ServerCapabilities(BaseModel):
    """Capabilities advertised by the server during initialization.

    Indicates which MCP features are available (tools, resources, prompts, etc.).
    """

    tools: bool = Field(default=True, description="Server supports tool invocation")
    resources: bool = Field(default=True, description="Server supports resource access")

    model_config = {"frozen": True}


# Story 2: MCP Tool Discovery Domain Types


class Tool(BaseModel):
    """MCP tool definition with name, description, and JSON Schema.

    Represents a discoverable MCP tool with its parameter schema.
    Parse Don't Validate: Only valid tool definitions can be constructed.

    Follows STYLE_GUIDE.md tool discovery pattern.
    """

    name: str = Field(description="Tool name identifier")
    description: str = Field(description="Tool purpose description")
    inputSchema: dict[str, Any] = Field(  # noqa: N815 (MCP spec requires camelCase)
        description="JSON Schema for parameters"
    )

    model_config = {"frozen": True}


class ExecuteTestsParams(BaseModel):
    """Parameters for execute_tests MCP tool.

    Validates pytest execution parameters with security constraints.
    Parse Don't Validate: Only valid parameter combinations can be constructed.

    Follows STYLE_GUIDE.md tool specification (lines 364-417).
    """

    node_ids: list[str] | None = Field(
        default=None,
        description="Specific test node IDs to execute (e.g., 'tests/test_user.py::test_login')",
    )
    markers: str | None = Field(
        default=None,
        description="Pytest marker expression for filtering (e.g., 'not slow and integration')",
    )
    keywords: str | None = Field(
        default=None,
        description="Keyword expression for test name matching (e.g., 'test_user')",
    )
    verbosity: int | None = Field(
        default=None,
        description="Output verbosity level: -2 (quietest) to 2 (most verbose)",
        ge=-2,
        le=2,
    )
    failfast: bool | None = Field(
        default=None,
        description="Stop execution on first failure",
    )
    maxfail: int | None = Field(
        default=None,
        description="Stop execution after N failures",
        ge=1,
    )
    show_capture: bool | None = Field(
        default=None,
        description="Include captured stdout/stderr in test output",
    )
    timeout: int | None = Field(
        default=None,
        description="Execution timeout in seconds",
        ge=1,
    )

    @model_validator(mode="after")
    def validate_failfast_maxfail_exclusive(self) -> "ExecuteTestsParams":
        """Validate that failfast and maxfail are mutually exclusive.

        Raises:
            ValueError: When both failfast and maxfail are specified
        """
        if self.failfast is not None and self.maxfail is not None:
            raise ValueError(
                "Parameters 'failfast' and 'maxfail' are mutually exclusive. "
                "Specify only one to control test execution stopping behavior."
            )
        return self

    model_config = {"frozen": True, "extra": "forbid"}


class DiscoverTestsParams(BaseModel):
    """Parameters for discover_tests MCP tool.

    Validates test discovery parameters with path traversal protection.
    Parse Don't Validate: Only safe path specifications can be constructed.

    Follows STYLE_GUIDE.md tool specification (lines 442-485).
    """

    path: str | None = Field(
        default=None,
        description="Directory or file path to discover tests within (default: project root)",
    )
    pattern: str | None = Field(
        default=None,
        description="Test file pattern (default: 'test_*.py' or '*_test.py')",
    )

    @field_validator("path")
    @classmethod
    def validate_no_path_traversal(cls, v: str | None) -> str | None:
        """Validate path does not contain directory traversal sequences.

        Security constraint: Prevent path traversal attacks via '..' sequences.

        Raises:
            ValueError: When path contains '..' directory traversal
        """
        if v is None:
            return v

        # Check for directory traversal attempts
        if ".." in Path(v).parts:
            raise ValueError(
                f"Path traversal not allowed: '{v}' contains '..' sequences. "
                "Specify paths within the project boundary only."
            )
        return v

    model_config = {"frozen": True, "extra": "forbid"}


# Workflow function signatures
# Implementation deferred to TDD phase (N.7)


def list_tools() -> list[Tool]:
    """List all available MCP tools with their parameter schemas.

    Returns tool definitions for pytest execution and discovery capabilities.

    Returns:
        List of Tool definitions with names, descriptions, and JSON schemas
    """
    return [
        Tool(
            name="execute_tests",
            description="Execute pytest tests with filtering and output options",
            inputSchema=ExecuteTestsParams.model_json_schema(),
        ),
        Tool(
            name="discover_tests",
            description="Discover available tests in the project",
            inputSchema=DiscoverTestsParams.model_json_schema(),
        ),
    ]


def initialize_server(
    protocol_version: str,
) -> tuple[ProtocolVersion, ServerInfo, ServerCapabilities]:
    """Initialize MCP server connection with protocol version validation.

    Parse Don't Validate: Returns validated domain types or raises
    ProtocolValidationError with structured ProtocolError details for
    unsupported protocol versions.

    Args:
        protocol_version: Protocol version string from AI agent

    Returns:
        Tuple of validated protocol version, server info, and capabilities

    Raises:
        ProtocolValidationError: When protocol version is unsupported
            (subclass of ValueError with protocol_error attribute)
    """
    try:
        # Pydantic validation happens here (ADR-005 compliance)
        validated_version = ProtocolVersion(value=protocol_version)
    except ValidationError:
        # Extract validation error and wrap in domain exception
        protocol_error = ProtocolError(
            field="protocolVersion",
            received_value=protocol_version,
            supported_version="2025-03-26",
            detail=(
                "Protocol version not supported. "
                "Please retry initialization with supported version."
            ),
        )
        raise ProtocolValidationError(protocol_error) from None

    server_info = ServerInfo(name="pytest-mcp", version="0.1.0")
    capabilities = ServerCapabilities(tools=True, resources=True)
    return (validated_version, server_info, capabilities)
