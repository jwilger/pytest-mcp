# ADR-001: MCP Protocol Selection for pytest Integration

**Status**: accepted

**Date**: October 3, 2025 (Friday, accepted)

**Project**: pytest-mcp

## Context

AI assistants frequently execute pytest during development workflows, particularly in AI-assisted TDD scenarios. Currently, this occurs through generic shell execution tools (Bash tool, arbitrary command execution), creating several challenges:

1. **Inconsistent Execution Patterns**: AI agents invoke pytest with varying command patterns and argument combinations, leading to unpredictable behavior and confusing results.

2. **Security Concerns**: Generic shell access grants AI agents arbitrary command execution capabilities far beyond test running needs, violating the principle of least privilege.

3. **Lack of Structure**: Shell command outputs are unstructured text requiring fragile parsing, making AI interpretation error-prone and inconsistent.

4. **No Standardization**: Without a common interface, different AI assistants may interact with pytest differently, reducing reliability and user trust.

The Model Context Protocol (MCP) provides a standardized approach for AI-to-tool communication via structured JSON-RPC interfaces with explicit tool definitions and parameter schemas.

## Decision

**We will implement pytest integration as an MCP server rather than a traditional CLI tool, shell wrapper, or pytest plugin.**

The system will expose pytest functionality through MCP tools (`execute_tests`, `discover_tests`) with validated parameter schemas, replacing ad-hoc shell command invocations with a structured, predictable protocol.

## Rationale

### Why MCP Protocol?

1. **Standardization**: MCP is Anthropic's emerging standard for AI-tool communication, providing a common protocol that AI assistants understand natively without custom integration work.

2. **Structured Interface**: MCP's JSON-RPC foundation with explicit parameter schemas enables:
   - Type-safe parameter validation before execution
   - Predictable, parseable response formats
   - Self-documenting tool capabilities through protocol discovery

3. **Security Through Constraint**: MCP tool definitions create an opinionated interface that constrains AI behavior to safe, predictable pytest operations. AI agents can ONLY execute defined tools with validated parameters - no arbitrary command injection possible.

4. **Native AI Assistant Support**: AI assistants (Claude, etc.) speak MCP natively, eliminating custom integration code and providing consistent behavior across different AI platforms.

5. **Future-Proof**: MCP is designed for AI-tool interaction patterns, aligning with the direction of AI-assisted development rather than retrofitting traditional interfaces.

### Why NOT Alternative Approaches?

**Alternative: Enhanced pytest Plugin**
- **Rejected**: Plugins still require shell command invocation; doesn't solve arbitrary command execution concern
- AI agents must still access shell to run `pytest --plugin-options`
- No standardized AI-to-tool protocol; requires custom integration per AI assistant

**Alternative: REST API Server**
- **Rejected**: Adds unnecessary network layer for local development tool
- Requires persistent server management (lifecycle, port allocation, authentication)
- MCP already provides JSON-RPC protocol without network overhead

**Alternative: CLI Tool with JSON Output**
- **Rejected**: Still requires shell access for invocation
- No parameter validation before execution (arguments parsed at runtime)
- No standardized discovery mechanism for AI assistants to learn available options

**Alternative: Language Server Protocol (LSP) Extension**
- **Rejected**: LSP designed for code intelligence (completion, navigation), not execution
- Semantic mismatch: test execution is operational, not code analysis
- MCP explicitly designed for tool execution patterns

## Consequences

### Positive Outcomes

1. **Consistent AI Behavior**: All AI agents execute pytest identically through standardized MCP interface, eliminating execution variability.

2. **Enhanced Security**: AI agents no longer require broad shell access; they can ONLY execute predefined pytest operations with validated parameters.

3. **Better Developer Experience**: Structured responses optimize AI parsing, leading to more accurate test result interpretation and better assistance quality.

4. **Reduced Integration Work**: AI assistants supporting MCP require zero custom integration code; protocol discovery handles tool exposure automatically.

5. **Maintainability**: Single protocol implementation serves all MCP-compatible AI assistants; no per-assistant customization needed.

### Negative Outcomes / Constraints

1. **MCP Ecosystem Dependency**: Requires MCP-compatible AI assistants; non-MCP tools cannot use this interface (though they can still use pytest directly).

2. **Protocol Evolution Risk**: MCP specification changes may require adaptation, though protocol versioning mitigates breaking changes.

3. **Learning Curve**: Developers unfamiliar with MCP must understand the protocol to contribute, though the Python MCP SDK abstracts most complexity.

4. **Additional Dependency**: Introduces MCP SDK dependency beyond core pytest requirement.

### Future Decisions Enabled

- **ADR-003**: MCP selection constrains pytest integration to programmatic API usage (not subprocess invocation with shell parsing)
- **ADR-004**: MCP's JSON-RPC foundation enables Pydantic parameter validation at tool boundaries
- **ADR-005**: Structured MCP responses drive result serialization design

### Future Decisions Constrained

- Cannot support non-MCP AI assistants without adding alternative interface (e.g., REST API, CLI tool)
- Must follow MCP protocol conventions for tool definitions and parameter schemas
- Response formats must serialize to JSON (MCP protocol constraint)

## Alternatives Considered

See "Why NOT Alternative Approaches?" section in Rationale above for detailed analysis of:
- Enhanced pytest plugin
- REST API server
- CLI tool with JSON output
- Language Server Protocol (LSP) extension

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- REQUIREMENTS_ANALYSIS.md: FR-1.1 through FR-1.4 (pytest execution requirements)
- EVENT_MODEL.md: Workflow 1 (Test Discovery), Workflow 2 (Test Execution), Workflow 3 (Capability Discovery)
