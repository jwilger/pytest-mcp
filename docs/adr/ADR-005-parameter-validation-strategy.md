# ADR-005: Parameter Validation Strategy

**Status**: accepted

**Date**: October 3, 2025 (Accepted: October 3, 2025)

**Project**: pytest-mcp

## Context

The pytest-mcp MCP server receives structured JSON-RPC requests from AI agents with parameters for test discovery and execution operations. As a security-focused interface replacing arbitrary shell access, we must validate all input parameters to prevent:

1. **Invalid pytest arguments** that cause confusing errors or unexpected behavior
2. **Path traversal attacks** accessing files outside intended project directories
3. **Command injection** through improperly escaped subprocess arguments
4. **Resource exhaustion** through unbounded parameter values
5. **Configuration conflicts** from incompatible parameter combinations

Given our subprocess integration (ADR-004), validation happens at the **MCP server boundary** before invoking pytest. Parameters flow: AI Agent → JSON-RPC → MCP Server → Validation → Subprocess pytest.

Key considerations:

1. **Validation Location**: Should validation occur at deserialization time (Pydantic models) or business logic time (manual checks)?

2. **Type Safety vs Runtime Validation**: What balance between compile-time type checking and runtime validation?

3. **Error Response Quality**: How do we provide actionable error messages to AI agents when validation fails?

4. **pytest Compatibility**: Must our validation rules match pytest's own validation semantics?

5. **Security Boundaries**: Which validations are security-critical (MUST enforce) vs convenience (SHOULD enforce)?

## Decision

**We will use Pydantic for declarative parameter validation at MCP request boundaries, enforcing type safety, constraint validation, and security rules before pytest invocation.**

Specifically:
- Define Pydantic models for all MCP tool parameters
- Use Pydantic validators for constraint checking (path validation, marker syntax, etc.)
- Enforce security boundaries (path traversal prevention, argument injection prevention) via Pydantic
- Provide structured error responses with field-specific validation failures
- Let pytest handle pytest-specific validation (marker semantics, plugin options)

## Rationale

### Why Pydantic at Boundaries?

1. **Declarative Validation**: Pydantic models serve as executable documentation of parameter contracts. Validation rules live with type definitions.

2. **Type Safety + Runtime Validation**: Combines mypy/pyright static checking with runtime constraint enforcement. Type errors caught at development time, constraint violations caught at runtime.

3. **Structured Error Responses**: Pydantic validation errors map naturally to JSON-RPC error responses with field-level detail:
   ```python
   # Pydantic error
   ValidationError([
     {"loc": ["markers"], "msg": "Invalid marker syntax", "type": "value_error"}
   ])

   # Maps to JSON-RPC error
   {"code": -32602, "message": "Invalid params",
    "data": {"field": "markers", "detail": "Invalid marker syntax"}}
   ```

4. **Security by Default**: Pydantic validators enforce security boundaries before subprocess invocation:
   - Path validation prevents traversal attacks
   - Argument whitelisting prevents command injection
   - Length limits prevent resource exhaustion

5. **Separation of Concerns**: MCP server validates MCP-level concerns (types, security, basic constraints). pytest validates pytest-level concerns (marker semantics, plugin compatibility).

### Why NOT Manual Validation?

**Alternative: Manual if/raise Checks**
- **Rejected**: Scatters validation logic across codebase; hard to audit security boundaries
- Validation rules separated from parameter definitions; documentation drift risk
- No automatic error response generation; must manually construct JSON-RPC errors
- Cannot leverage static type checking; runtime-only validation

**Alternative: Validation at Business Logic Layer**
- **Rejected**: Validation occurs too late; invalid data already deserialized into business objects
- Harder to provide structured error responses with field locations
- Mixes validation concerns with business logic; reduces testability

### Validation Layers

**Layer 1: Pydantic Schema (MCP Boundary)**
- Type correctness (strings, integers, booleans, lists)
- Required vs optional fields
- Enums and literal types for controlled vocabularies
- Basic constraints (string lengths, numeric ranges)
- Security boundaries (path validation, argument whitelisting)

**Layer 2: pytest Execution (pytest Boundary)**
- Marker expression semantics (pytest evaluates marker boolean expressions)
- Plugin option compatibility (pytest validates plugin-specific args)
- Test node ID validity (pytest checks if nodes exist during collection)
- Configuration file resolution (pytest handles pytest.ini, pyproject.toml)

**Rationale**: MCP server validates what it CAN know (types, security, syntax). pytest validates what it MUST know (semantics, project-specific configuration).

### Security Validation Examples

**Path Traversal Prevention:**
```python
class ExecuteTestsParams(BaseModel):
    path: Optional[Path] = None

    @validator('path')
    def validate_path_safety(cls, v):
        if v and '..' in v.parts:
            raise ValueError("Path traversal not allowed")
        if v and not v.is_relative_to(Path.cwd()):
            raise ValueError("Path must be within project directory")
        return v
```

**Marker Syntax Validation:**
```python
class ExecuteTestsParams(BaseModel):
    markers: Optional[str] = None

    @validator('markers')
    def validate_marker_syntax(cls, v):
        if v and not _is_valid_marker_expression(v):
            raise ValueError("Invalid marker expression syntax")
        return v
```

## Consequences

### Positive Outcomes

1. **Security Confidence**: Path traversal, command injection, and resource exhaustion attacks blocked at boundary before subprocess invocation.

2. **Excellent Error Messages**: AI agents receive structured field-specific validation errors, enabling self-correction without human intervention.

3. **Type Safety**: Static type checkers validate parameter usage; reduces integration bugs between MCP server components.

4. **Maintainability**: Validation rules documented in code via Pydantic models; easy to audit security boundaries.

5. **Testability**: Validation logic isolated in Pydantic validators; straightforward unit testing without pytest integration.

6. **Automatic JSON Schema Generation**: Pydantic models can generate JSON Schema for MCP tool descriptions, improving AI agent integration.

### Negative Outcomes / Constraints

1. **Pydantic Dependency**: Adds Pydantic as required dependency; version compatibility responsibility.
   - **Trade-off**: Pydantic is widely used, stable, and well-maintained; dependency risk low.

2. **Validation Duplication**: Some validation occurs both in Pydantic (syntax) and pytest (semantics).
   - **Example**: Marker expression syntax validated by Pydantic; marker semantics validated by pytest.
   - **Trade-off**: Duplication acceptable; MCP server catches obvious errors early; pytest handles project-specific validation.

3. **Custom Validator Complexity**: Complex validation rules (marker syntax, node ID format) require custom Pydantic validators.
   - **Mitigation**: Keep validators focused on security and syntax; defer semantics to pytest.

4. **Error Message Mapping**: Must translate Pydantic ValidationErrors to JSON-RPC error format.
   - **Implementation Overhead**: Straightforward mapping; Pydantic errors contain field paths and messages.

### Future Decisions Enabled

- **ADR-006**: Validated parameters enable rich result structuring without worry about data quality
- **ADR-007**: Security validation establishes trust boundary for error handling decisions
- **ADR-008**: Path validation and argument whitelisting form foundation of security model

### Future Decisions Constrained

- Committed to Pydantic for validation; cannot switch to alternative frameworks without significant refactoring
- Validation rules become part of API contract; changes require careful versioning
- Must maintain Pydantic validators alongside pytest argument evolution

## Alternatives Considered

### Alternative 1: Manual Validation with if/raise Checks
**Why Rejected**:
- Validation logic scattered across codebase; hard to audit
- No declarative documentation of parameter contracts
- Manual JSON-RPC error construction; error-prone
- No static type checking benefits

### Alternative 2: Validation at Business Logic Layer
**Why Rejected**:
- Validation occurs too late; invalid data already in system
- Harder to provide structured error responses
- Mixes validation concerns with business logic
- Reduces testability (must mock pytest for validation testing)

### Alternative 3: Defer All Validation to pytest
**Why Rejected**:
- No early validation; must invoke subprocess to detect basic errors
- pytest error messages not structured for JSON-RPC responses
- Cannot prevent security issues (path traversal, injection) before subprocess invocation
- Poor AI agent experience (subprocess failures instead of clear parameter errors)

### Alternative 4: JSON Schema Validation (No Pydantic)
**Why Rejected**:
- JSON Schema provides type validation but not custom constraint validation
- No Python type safety integration; separate schema definition from code
- Must manually implement constraint validators; duplicates Pydantic functionality
- Cannot leverage Pydantic ecosystem (FastAPI integration, automatic schema generation)

## Implementation Notes

### Pydantic Model Structure

```python
from pydantic import BaseModel, validator, Field
from pathlib import Path
from typing import Optional, List

class ExecuteTestsParams(BaseModel):
    """Parameters for execute_tests MCP tool."""

    # Test selection
    node_ids: Optional[List[str]] = Field(None, description="Specific test node IDs")
    path: Optional[Path] = Field(None, description="Path to tests directory")
    pattern: Optional[str] = Field(None, pattern=r"^[\w*?.-]+$", description="Test file pattern")

    # Filtering
    markers: Optional[str] = Field(None, description="Marker expression")
    keywords: Optional[str] = Field(None, description="Keyword expression")

    # Execution control
    verbosity: int = Field(0, ge=0, le=3, description="Verbosity level 0-3")
    failfast: bool = Field(False, description="Stop on first failure")

    # Security validators
    @validator('path')
    def validate_path_safety(cls, v):
        # Path traversal prevention
        # Absolute path rejection
        # Project boundary enforcement
        ...

    @validator('markers')
    def validate_marker_syntax(cls, v):
        # Basic syntax validation
        # Defer semantics to pytest
        ...
```

### Validation Error Mapping

```python
from pydantic import ValidationError
from typing import Dict, Any

def pydantic_error_to_jsonrpc(exc: ValidationError) -> Dict[str, Any]:
    """Convert Pydantic ValidationError to JSON-RPC error response."""
    errors = exc.errors()
    return {
        "code": -32602,  # Invalid params
        "message": "Invalid parameters",
        "data": {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in errors
            ]
        }
    }
```

## References

- ADR-001: MCP Protocol Selection (establishes JSON-RPC request/response context)
- ADR-002: Stateless Architecture (validation occurs per-request, no session state)
- ADR-004: pytest Subprocess Integration (validation before subprocess invocation)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [JSON-RPC Error Codes](https://www.jsonrpc.org/specification#error_object)
- REQUIREMENTS_ANALYSIS.md: FR-1.1 (Complete CLI argument support requires parameter validation)
- EVENT_MODEL.md: Workflow 2 MCP Protocol Wireframes show parameter validation in sequence diagrams
