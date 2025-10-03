# ADR-003: pytest Integration via Programmatic API

**Status**: rejected

**Date**: October 3, 2025 (Friday)

**Rejected**: October 3, 2025

**Rejection Reason**: Process isolation is mandatory. Projects must not be tied to the same pytest version as the MCP server. The programmatic API approach violates these critical requirements by running pytest in-process with the server and creating tight version coupling.

**Project**: pytest-mcp

## Context

The pytest-mcp MCP server needs to execute pytest operations (test discovery and test execution) on behalf of AI agents. We must decide how to integrate with pytest itself.

Given our stateless architecture (ADR-002), each MCP tool invocation will trigger an independent pytest operation. The question is: **How should we invoke pytest?**

Key considerations:

1. **Integration Approaches Available**:
   - Subprocess invocation: Shell out to `pytest` command-line executable
   - Programmatic API: Import and invoke pytest as a Python library
   - Hybrid: Mix of both depending on operation type

2. **Control Requirements**: We need to capture structured test results, not just parse text output.

3. **Performance**: Stateless design means no session reuse; each invocation starts fresh.

4. **Error Handling**: Must distinguish pytest failures (tests failed) from integration failures (pytest crashed).

5. **Plugin Compatibility**: pytest's plugin ecosystem is core value; integration must support user plugins.

## Decision

**We will integrate with pytest via its programmatic Python API (`pytest.main()` and collection hooks), NOT through subprocess invocation.**

Specifically:
- Use `pytest.main()` for test execution with custom result collection plugin
- Use pytest's collection API (`pytest.main(["--collect-only"])`) for test discovery
- Execute pytest within the same Python process as the MCP server
- Capture structured results through pytest plugin hooks, not text parsing

## Rationale

### Why Programmatic API?

1. **Structured Data by Design**: pytest plugin hooks provide direct access to test objects, results, and metadata as Python objects. No text parsing required.

2. **Precise Error Handling**: Can distinguish pytest internal errors from test failures through exception handling and result object inspection.

3. **Performance**: Eliminates subprocess overhead (process spawning, IPC, serialization). While stateless design prevents session reuse, in-process execution is still faster per invocation.

4. **Plugin Compatibility**: pytest plugins install into the Python environment and work automatically when using programmatic API. No plugin discovery issues.

5. **Type Safety**: pytest API provides typed interfaces; can leverage mypy/pyright for correctness verification.

6. **Simpler Implementation**: Direct Python API calls simpler than subprocess management, stdout/stderr parsing, and exit code interpretation.

### Why NOT Subprocess Invocation?

**Alternative: Shell Out to `pytest` Command**
- **Rejected**: Requires text parsing of pytest output, which is fragile and loses structured information
- Exit codes are coarse-grained (0/1/2); don't provide test-level detail
- Subprocess management adds complexity (timeouts, signal handling, zombie processes)
- Must serialize parameters to command-line arguments, then deserialize pytest's text output
- Plugin compatibility depends on correct environment variable and path setup

**Alternative: Hybrid Approach (API for discovery, subprocess for execution)**
- **Rejected**: Introduces inconsistency; two different integration mechanisms to maintain
- No clear benefit since programmatic API works for both discovery and execution
- Complicates error handling (two different error paths to handle)

## Consequences

### Positive Outcomes

1. **Rich Result Structures**: Direct access to pytest result objects enables detailed, structured MCP responses with test names, durations, failure details, etc.

2. **Simpler Error Handling**: Python exceptions from pytest API are easier to handle than parsing stderr output and exit codes.

3. **Better Performance**: No subprocess overhead per invocation; in-process execution is fastest option for stateless design.

4. **Type-Safe Integration**: pytest API calls can be type-checked; reduces integration bugs.

5. **Plugin Ecosystem Works**: User pytest plugins automatically discovered and loaded when using programmatic API.

### Negative Outcomes / Constraints

1. **Process Isolation Loss**: pytest runs in same process as MCP server; poorly behaved pytest plugins could crash the server.
   - **Mitigation**: Server restarts are fast (stateless); MCP client will reconnect automatically.
   - Real-world risk low; pytest plugins rarely crash the process.

2. **pytest Version Coupling**: Server depends on specific pytest version as library dependency; version conflicts possible.
   - **Mitigation**: Declare pytest version dependency clearly; users install compatible pytest.

3. **Global State Risk**: pytest uses some global state (config, plugins); rapid concurrent invocations could theoretically conflict.
   - **Mitigation**: Stateless design means no long-lived pytest sessions; each `pytest.main()` call is independent.

4. **Output Capture Complexity**: Must use pytest plugin hooks to capture results, not just read stdout.
   - **Trade-off**: Slightly more complex than reading subprocess output, but yields structured data.

### Future Decisions Enabled

- **ADR-004**: Programmatic API enables rich parameter validation using pytest's config objects
- **ADR-005**: Direct access to pytest result objects enables detailed, structured MCP response schemas
- **ADR-006**: In-process execution enables potential performance optimizations (plugin caching, config reuse)

### Future Decisions Constrained

- Cannot switch to subprocess model without rewriting result capture and error handling
- Committed to pytest as library dependency; version compatibility becomes our responsibility
- Must handle pytest's global state implications if concurrency becomes important

## Alternatives Considered

See "Why NOT Subprocess Invocation?" section in Rationale above for detailed analysis of:
- Subprocess invocation of `pytest` command
- Hybrid approach (API + subprocess)

## References

- ADR-001: MCP Protocol Selection (establishes MCP tool invocation context)
- ADR-002: Stateless Architecture (each invocation is independent, no session reuse)
- [pytest Programmatic API Documentation](https://docs.pytest.org/en/stable/how-to/usage.html#calling-pytest-from-python-code)
- [pytest Plugin Hooks](https://docs.pytest.org/en/stable/reference/reference.html#hooks)
- REQUIREMENTS_ANALYSIS.md: FR-1.1 (Complete CLI argument support requires precise parameter mapping)
- EVENT_MODEL.md: Test Discovery and Test Execution workflows show structured request/response patterns
