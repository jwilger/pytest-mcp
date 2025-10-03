"""Domain types for pytest-mcp server.

This module defines workflow functions and minimal nominal types following
the Parse Don't Validate philosophy. Types make illegal states unrepresentable
at the domain boundary.
"""

from pydantic import BaseModel, Field, field_validator


class ProtocolVersion(BaseModel):
    """MCP protocol version identifier.

    Validates protocol version strings match supported format and version.
    Parse Don't Validate: Only valid protocol versions can be constructed.
    """

    value: str = Field(description="Protocol version in YYYY-MM-DD format")

    @field_validator("value")
    @classmethod
    def validate_supported_version(cls, v: str) -> str:
        """Ensure protocol version is supported."""
        supported = "2024-11-05"
        if v != supported:
            msg = f"Protocol version {v} not supported. Supported version: {supported}"
            raise ValueError(msg)
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


# Workflow function signatures (Story 1 scope only)
# Implementation deferred to TDD phase (N.7)


def initialize_server(protocol_version: str) -> tuple[ProtocolVersion, ServerInfo, ServerCapabilities]:
    """Initialize MCP server connection with protocol version validation.

    Parse Don't Validate: Returns validated domain types or raises ValueError
    with ProtocolError details for unsupported protocol versions.

    Args:
        protocol_version: Protocol version string from AI agent

    Returns:
        Tuple of validated protocol version, server info, and capabilities

    Raises:
        ValueError: When protocol version is unsupported (includes ProtocolError details)
    """
    raise NotImplementedError("TDD implementation pending")
