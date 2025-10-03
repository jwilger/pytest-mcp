# ADR-004: pytest Integration via Subprocess Invocation

**Status**: accepted

**Date**: October 3, 2025 (Friday) - Accepted: October 3, 2025

**Project**: pytest-mcp

**Supersedes**: ADR-003 (pytest Integration via Programmatic API)

## Context

The pytest-mcp MCP server needs to execute pytest operations (test discovery and test execution) on behalf of AI agents. We must decide how to integrate with pytest itself.

Given our stateless architecture (ADR-002), each MCP tool invocation will trigger an independent pytest operation. ADR-003 proposed using pytest's programmatic API but was rejected due to two critical requirements:

1. **Process Isolation is Mandatory**: pytest must run in a separate process from the MCP server to prevent crashes or misbehaving plugins from affecting server stability.

2. **Version Independence Required**: Each project must use its own pytest version from its own virtual environment. The MCP server cannot dictate or constrain project pytest versions.

Key considerations:

1. **Integration Approaches Available**:
   - Subprocess invocation: Shell out to `pytest` command-line executable
   - Programmatic API: Import and invoke pytest as a Python library (REJECTED in ADR-003)
   - Hybrid: Mix of both depending on operation type

2. **Structured Data Requirement**: We need structured test results, not just text output parsing.

3. **Performance**: Stateless design means no session reuse; each invocation starts fresh.

4. **Error Handling**: Must distinguish pytest failures (tests failed) from integration failures (pytest crashed).

5. **Plugin Compatibility**: pytest's plugin ecosystem is core value; integration must respect project plugin configurations.

## Decision

**We will integrate with pytest via subprocess invocation of the project's pytest executable, capturing structured output through pytest's JSON report plugin.**

Specifically:
- Use `subprocess.run()` to invoke `pytest` from the project's virtual environment
- Use pytest's `--json-report` plugin (or similar) for structured output capture
- Parse JSON results for structured MCP responses
- Map pytest exit codes to operation outcomes
- Capture stdout/stderr for diagnostic information
- Provide fallback text parsing if JSON plugin unavailable

## Rationale

### Why Subprocess Invocation?

1. **Process Isolation**: pytest runs in separate process; crashes or hangs cannot affect MCP server stability. Server remains available even if pytest misbehaves.

2. **Version Independence**: Each project uses its own pytest installation from its own virtual environment. No version conflicts or coupling between server and projects.

3. **Environment Isolation**: Project's dependencies, plugins, and configuration remain completely isolated. No risk of dependency conflicts with server.

4. **Robust Error Handling**: Process exit codes provide clear separation:
   - Exit 0: Tests passed
   - Exit 1: Tests failed
   - Exit 2: pytest error (configuration, collection failure)
   - Exit >128: Signal termination (crash, timeout)

5. **Plugin Compatibility**: Project's pytest plugins automatically loaded from project environment. No special plugin discovery needed.

6. **Security Boundary**: Subprocess execution provides security isolation; untrusted project code cannot directly access server internals.

### How We Address Structured Data Needs

1. **JSON Report Plugin**: Use `pytest-json-report` or similar plugin via `--json-report` flag
   - Produces machine-readable JSON output with test results, durations, failures
   - Well-established plugin with structured schema
   - Fallback: Use `--tb=short -v` and parse pytest's structured text output

2. **Exit Code Mapping**: Combine exit codes with JSON results for complete picture
   - Exit code provides high-level outcome
   - JSON report provides test-level detail

3. **Output Streams**: Capture both stdout and stderr
   - stdout: Test output and progress
   - stderr: pytest warnings and errors
   - Both streams useful for diagnostics

### Why NOT Programmatic API? (ADR-003 Rejection Reasons)

**Critical Flaws of In-Process Integration:**
1. **No Process Isolation**: pytest crash crashes MCP server; unacceptable for production
2. **Version Coupling**: Forces all projects to use MCP server's pytest version; violates project autonomy
3. **Dependency Conflicts**: Server and project dependencies share same Python process; conflict risk high
4. **Security Risk**: Untrusted project code runs in server process; no security boundary

### Performance Considerations

**Subprocess Overhead:**
- Process spawn: ~10-50ms overhead per invocation
- **Trade-off Accepted**: Isolation and version independence worth the milliseconds
- Stateless design already prevents session reuse optimizations
- Real performance bottleneck is test execution time, not process spawn

## Consequences

### Positive Outcomes

1. **Server Stability**: pytest crashes isolated to subprocess; server remains available and responsive.

2. **Project Autonomy**: Each project controls its own pytest version, plugins, and configuration. No MCP server constraints.

3. **Security Isolation**: Untrusted project code cannot compromise server process.

4. **Plugin Freedom**: Projects can use any pytest plugins without server compatibility concerns.

5. **Environment Flexibility**: Projects can use any Python environment (venv, conda, etc.); MCP server adapts.

6. **Robust Error Handling**: Exit codes provide clear signal semantics; easier to diagnose failures.

### Negative Outcomes / Constraints

1. **JSON Plugin Dependency**: Optimal experience requires `pytest-json-report` or similar plugin installed in project.
   - **Mitigation**: Provide fallback text parsing for projects without JSON plugin
   - **Documentation**: Recommend JSON plugin for best results
   - Plugin installation is user choice, not requirement

2. **Output Parsing Complexity**: Must parse either JSON or text output; more complex than direct API objects.
   - **Trade-off**: Complexity worth the isolation and version independence benefits
   - JSON parsing is straightforward with well-defined schema
   - Text parsing fallback handles projects without JSON plugin

3. **Process Spawn Overhead**: 10-50ms overhead per pytest invocation.
   - **Acceptable**: Isolation benefits outweigh milliseconds
   - Test execution time dominates; spawn overhead negligible

4. **Environment Detection**: Must correctly identify and activate project's Python environment.
   - **Implementation**: Use environment variable hints, path resolution, or explicit configuration
   - Standard patterns exist for virtualenv detection

### Future Decisions Enabled

- **ADR-005**: JSON report schema enables rich MCP response structures with test metadata
- **ADR-006**: Environment isolation enables supporting multiple Python versions per project
- **ADR-007**: Process isolation enables timeout and resource limit enforcement

### Future Decisions Constrained

- Must maintain JSON parsing logic; cannot rely on pytest API's typed objects
- Committed to subprocess model; cannot switch to in-process without violating isolation requirements
- Environment detection complexity cannot be eliminated (inherent in subprocess model)

## Alternatives Considered

### Alternative 1: Programmatic API (ADR-003 - REJECTED)
**Why Rejected**:
- No process isolation (crashes affect server)
- Version coupling (forces projects to use server's pytest version)
- Dependency conflicts (server and project share Python process)

See ADR-003 for full analysis of programmatic API approach and why it was rejected.

### Alternative 2: Hybrid Approach (API for discovery, subprocess for execution)
**Why Rejected**:
- Inconsistent: Two integration mechanisms with different error models
- Partial isolation: Discovery crashes still affect server
- Version coupling: Still requires compatible pytest for API usage
- Complexity: Maintaining two integration paths without clear benefit

### Alternative 3: gRPC/HTTP Server Wrapper
**Why Rejected**:
- Over-engineered: Adds network layer complexity for no isolation benefit beyond subprocess
- Performance: Network serialization slower than subprocess IPC
- Deployment: Requires additional server component; complicates setup
- Maintenance: More moving parts to maintain and version

## Implementation Notes

### Environment Detection Strategy
```
1. Check for VIRTUAL_ENV environment variable (activated virtualenv)
2. Check for .venv, venv, .virtualenv directories in project root
3. Use `python -m pytest` to respect project's Python environment
4. Allow explicit pytest path configuration via MCP arguments
```

### JSON Report Integration
```
pytest --json-report --json-report-file=<temp_file> <other_args>
```

### Exit Code Handling
```python
result = subprocess.run(["pytest", ...])
if result.returncode == 0:
    # Tests passed
elif result.returncode == 1:
    # Tests failed (expected failure)
elif result.returncode == 2:
    # pytest error (collection failure, invalid config)
else:
    # Unexpected error (crash, signal, timeout)
```

## References

- ADR-001: MCP Protocol Selection (establishes MCP tool invocation context)
- ADR-002: Stateless Architecture (each invocation is independent, no session reuse)
- ADR-003: pytest Integration via Programmatic API (REJECTED - superseded by this ADR)
- [pytest Exit Codes](https://docs.pytest.org/en/stable/reference/exit-codes.html)
- [pytest-json-report Plugin](https://pypi.org/project/pytest-json-report/)
- REQUIREMENTS_ANALYSIS.md: FR-1.1 (Complete CLI argument support requires subprocess invocation)
- EVENT_MODEL.md: Test Discovery and Test Execution workflows show structured request/response patterns
