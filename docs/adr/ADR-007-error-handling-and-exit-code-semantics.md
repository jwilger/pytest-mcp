# ADR-007: Error Handling and Exit Code Semantics

**Status**: accepted

**Date**: October 3, 2025 (Friday) - Accepted October 3, 2025

**Project**: pytest-mcp

## Context

The pytest-mcp MCP server executes pytest as a subprocess and must distinguish between multiple failure modes:

1. **Test Failures**: Tests executed successfully but assertions failed (expected development workflow)
2. **Collection Errors**: pytest could not collect tests due to import errors, syntax errors, or missing files
3. **System Errors**: Subprocess failures, timeouts, or pytest crashes
4. **Usage Errors**: Invalid pytest arguments or configuration issues
5. **Internal Errors**: MCP server bugs or unexpected conditions

pytest uses exit codes to signal different outcomes:
- **0**: All tests passed
- **1**: Some tests failed (assertions)
- **2**: Test execution interrupted by user
- **3**: Internal pytest error occurred
- **4**: pytest command line usage error
- **5**: No tests collected

The MCP protocol expects tools to:
- Return successful JSON-RPC responses for successful tool executions
- Return error responses with appropriate error codes for failures

Key design tensions:

1. **Test Failure vs Tool Failure**: Should test failures be MCP errors (tool failed) or successful responses containing failure details (tool succeeded at running tests)?

2. **Exit Code Semantics**: How should each pytest exit code map to MCP responses?

3. **Error Context**: How much diagnostic information should error responses include?

4. **Timeout Handling**: What happens when pytest subprocess exceeds time limits?

5. **Crash Recovery**: How to handle subprocess crashes or signals?

## Decision

**Test failures are NOT tool failures. The MCP tool succeeds when pytest executes successfully, regardless of test outcomes.**

Specifically:

### Exit Code Mapping

| pytest Exit Code | Condition | MCP Response Type | Rationale |
|-----------------|-----------|-------------------|-----------|
| 0 | All tests passed | Success | Tool executed successfully |
| 1 | Some tests failed | Success | Tool executed successfully; failures in result data |
| 2 | Execution interrupted | Error (-32000) | User/system intervention prevented completion |
| 3 | Internal pytest error | Error (-32000) | pytest internal failure |
| 4 | Usage error | Error (-32602) | Invalid parameters (our validation should prevent this) |
| 5 | No tests collected | Success | Tool executed successfully; zero tests is valid outcome |

### Subprocess Failure Handling

**Timeout**:
- MCP Error Code: -32000 (Server Error)
- Message: "pytest execution exceeded timeout of {N} seconds"
- Data: Include partial stdout/stderr if available

**Crash/Signal**:
- MCP Error Code: -32000 (Server Error)
- Message: "pytest subprocess terminated with signal {signal_name}"
- Data: Include stdout/stderr and signal details

**Spawn Failure**:
- MCP Error Code: -32000 (Server Error)
- Message: "Failed to spawn pytest subprocess: {error_details}"
- Data: Include environment and configuration details

### MCP Error Response Format

```python
{
  "code": -32000,  # Server error
  "message": "pytest execution failed: {brief_description}",
  "data": {
    "error_type": "timeout" | "crash" | "pytest_internal" | "interrupted",
    "exit_code": int | null,
    "signal": str | null,
    "stdout": str,
    "stderr": str,
    "command": [str],  # Full pytest command for debugging
    "duration": float | null
  }
}
```

### Success Response with Test Failures

When pytest exits with code 1 (test failures):
- MCP Response: Success (200 OK)
- Response data: Full result structure from ADR-006
- Exit code field in response: 1
- Failed test details in `tests` array

**Rationale**: The tool successfully executed pytest and returned structured results. Test failures are part of normal development workflow, not tool malfunctions.

### Internal MCP Server Errors

For bugs or unexpected conditions in the MCP server itself (not pytest):
- MCP Error Code: -32603 (Internal Error)
- Message: "Internal server error: {brief_description}"
- Data: Include traceback and diagnostic information

## Rationale

### Why Test Failures Are Not Tool Failures

1. **Tool Semantics**: The tool's job is "execute pytest and return results," not "make tests pass." Test failures are valid, expected outcomes.

2. **AI Agent Workflow**: Agents need test failure details to fix code. Treating failures as errors hides crucial debugging information in error responses.

3. **Developer Experience**: Developers expect test failures during TDD. Errors should signal "something went wrong with execution," not "your tests failed."

4. **Protocol Alignment**: MCP tools return structured data. Test results (pass/fail) are data, not execution status.

### Why Exit Code 5 (No Tests Collected) Is Success

1. **Valid Outcome**: Empty test suites or filtered test selection may legitimately collect zero tests.

2. **Clear Signaling**: Response data shows `summary.total: 0`, making the situation obvious to AI agents.

3. **Non-Error Condition**: No tests collected is not a malfunction—pytest executed successfully and found no tests matching criteria.

### Why Exit Code 2/3/4 Are Errors

**Exit Code 2 (Interrupted)**:
- Execution did not complete; results are incomplete
- Agent cannot trust partial results
- Requires re-execution to get complete outcome

**Exit Code 3 (Internal Error)**:
- pytest itself malfunctioned
- Results unreliable or unavailable
- Requires investigation of pytest installation or configuration

**Exit Code 4 (Usage Error)**:
- Should be prevented by ADR-005 parameter validation
- If it occurs, indicates MCP server bug or validation gap
- Maps to MCP "Invalid params" error code

### Timeout vs Interrupt Distinction

**Timeout** (our constraint):
- MCP server imposes execution time limit
- Clean subprocess termination
- Error type: "timeout"

**Interrupt** (external):
- User Ctrl+C or system signal
- pytest reports exit code 2
- Error type: "interrupted"

Both are errors (incomplete execution) but have different causes.

### Error Context Philosophy

**Maximum Diagnostic Information**:
- Include full stdout/stderr in error responses
- Include subprocess command for reproducibility
- Include timing information for timeout analysis
- Trade-off: Larger error payloads BUT complete debugging context

**Why**: When execution fails, agents need comprehensive information to diagnose issues without re-running failed commands.

## Consequences

### Positive Outcomes

1. **Clear Semantics**: Test failures clearly distinguished from execution failures.

2. **Rich Failure Context**: AI agents get detailed test failure information in normal success responses.

3. **Debugging Efficiency**: Comprehensive error data enables diagnosis without re-execution.

4. **Developer Alignment**: Error conditions match developer expectations (errors = execution problems, not test failures).

5. **Protocol Compliance**: Proper MCP error codes for different failure modes.

6. **Crash Resilience**: Subprocess crashes handled gracefully with diagnostic information.

### Negative Outcomes / Constraints

1. **Exit Code 1 Ambiguity**: AI agents must check `exit_code` field in response data to detect test failures.
   - **Mitigation**: Clear documentation; `exit_code` field explicit in response schema.

2. **Timeout False Positives**: Very slow test suites may hit timeout limits.
   - **Mitigation**: Configurable timeout (future enhancement); default should accommodate most test suites.

3. **Error Response Size**: Including full stdout/stderr in errors creates large payloads.
   - **Acceptable**: Error cases are exceptional; complete information worth token cost.

4. **Exit Code 4 Should Never Happen**: Indicates validation failure.
   - **Benefit**: If it occurs, signals MCP server bug to fix.

### Future Decisions Enabled

- Configurable timeout limits per request
- Progressive timeout strategies (warn before kill)
- Retry logic for transient failures
- Subprocess resource limit enforcement

### Future Decisions Constrained

- Committed to "test failures are data, not errors" semantics
- Error response schema becomes API contract
- Exit code mapping table must remain stable

## Alternatives Considered

### Alternative 1: Test Failures As Errors

**Approach**: Return MCP error when any test fails (exit code 1)

**Why Rejected**:
- Conflates "tool failed" with "tests failed"
- Hides test failure details in error responses
- Forces AI agents to parse error messages for test outcomes
- Violates principle that tool's job is "run tests," not "pass tests"
- Poor developer UX (errors imply something broken)

### Alternative 2: All Non-Zero Exit Codes As Errors

**Approach**: Only exit code 0 returns success; all others return errors

**Why Rejected**:
- No tests collected (exit code 5) is valid outcome, not error
- Test failures (exit code 1) are expected development workflow
- Loses distinction between execution failures and test outcomes
- Makes AI agents parse errors for normal test failure information

### Alternative 3: Warnings For Test Failures

**Approach**: Success response with "warnings" field for failed tests

**Why Rejected**:
- Test failures are not warnings—they are primary outcomes
- Adds unnecessary indirection (`warnings` field vs `tests` array)
- "Warning" semantics suggest optional/ignorable; test failures are critical
- ADR-006 result structure already clearly shows failures in `tests` array

### Alternative 4: Separate Success Response Types

**Approach**: Different response schemas for "all passed" vs "some failed"

**Why Rejected**:
- Adds complexity to response parsing (agents must handle multiple schemas)
- exit_code field already distinguishes outcomes
- Unified schema simpler for AI agents to consume
- No benefit over single schema with explicit exit_code

### Alternative 5: No Timeout Enforcement

**Approach**: Let pytest run indefinitely; no subprocess timeout

**Why Rejected**:
- Infinite loops or hung tests could block MCP server forever
- AI agents need predictable execution bounds
- Resource exhaustion risk in production environments
- Timeout with clear error messaging better than indefinite hang

**Revisit**: Timeout should be configurable; default provides safety net

### Alternative 6: Minimal Error Context

**Approach**: Error responses only include brief message, no stdout/stderr

**Why Rejected**:
- Insufficient information for diagnosing execution failures
- Forces re-execution to gather diagnostic information
- Token savings minimal in error cases (which are exceptional)
- Complete context enables one-shot debugging

## Implementation Notes

### Exit Code Handling Function

```python
def handle_pytest_exit_code(
    exit_code: int,
    stdout: str,
    stderr: str,
    duration: float,
    json_report_path: Path | None,
    command: list[str]
) -> dict[str, Any]:
    """Map pytest exit code to appropriate MCP response."""

    # Success cases: return structured results
    if exit_code in (0, 1, 5):
        if json_report_path and json_report_path.exists():
            return serialize_pytest_results(
                exit_code=exit_code,
                json_report_path=json_report_path,
                text_output=stdout
            )
        else:
            # Fallback if JSON report missing
            return {
                "exit_code": exit_code,
                "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": duration},
                "tests": [],
                "json_report": {},
                "text_output": stdout,
                "collection_errors": []
            }

    # Error cases: raise MCP error
    error_mapping = {
        2: ("interrupted", "Test execution was interrupted"),
        3: ("pytest_internal", "pytest internal error occurred"),
        4: ("usage_error", "Invalid pytest arguments (validation failure)")
    }

    error_type, brief_msg = error_mapping.get(
        exit_code,
        ("unknown", f"pytest exited with unexpected code {exit_code}")
    )

    raise McpError(
        code=-32000,
        message=f"pytest execution failed: {brief_msg}",
        data={
            "error_type": error_type,
            "exit_code": exit_code,
            "signal": None,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
            "duration": duration
        }
    )
```

### Timeout Handling

```python
import subprocess
import signal

def execute_with_timeout(
    command: list[str],
    timeout_seconds: float
) -> tuple[int, str, str, float]:
    """Execute command with timeout; raise McpError on timeout."""

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        duration = time.time() - start_time
        return result.returncode, result.stdout, result.stderr, duration

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        raise McpError(
            code=-32000,
            message=f"pytest execution exceeded timeout of {timeout_seconds} seconds",
            data={
                "error_type": "timeout",
                "exit_code": None,
                "signal": None,
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "",
                "command": command,
                "duration": duration
            }
        )
```

### Signal Handling

```python
def handle_subprocess_signal(
    returncode: int,
    stdout: str,
    stderr: str,
    command: list[str],
    duration: float
) -> None:
    """Check if subprocess terminated by signal; raise McpError if so."""

    # Negative return codes indicate signal termination (Unix)
    if returncode < 0:
        signal_num = -returncode
        signal_name = signal.Signals(signal_num).name

        raise McpError(
            code=-32000,
            message=f"pytest subprocess terminated with signal {signal_name}",
            data={
                "error_type": "crash",
                "exit_code": None,
                "signal": signal_name,
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
                "duration": duration
            }
        )
```

## References

- ADR-001: MCP Protocol Selection (JSON-RPC error codes and responses)
- ADR-002: Stateless Architecture (no retry state; each execution independent)
- ADR-004: pytest Subprocess Integration (subprocess execution produces exit codes)
- ADR-005: Parameter Validation Strategy (should prevent exit code 4)
- ADR-006: Result Structuring and Serialization (success response format)
- [pytest Exit Codes](https://docs.pytest.org/en/stable/reference/exit-codes.html)
- [MCP Error Codes](https://spec.modelcontextprotocol.io/specification/basic/errors/)
- REQUIREMENTS_ANALYSIS.md: FR-1.2 (Proper error handling and reporting)
- EVENT_MODEL.md: Error handling flows in execute_tests workflow
