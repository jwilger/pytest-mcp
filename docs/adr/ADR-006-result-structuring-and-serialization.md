# ADR-006: Result Structuring and Serialization

**Status**: accepted

**Date**: October 3, 2025 (Friday)

**Project**: pytest-mcp

## Context

The pytest-mcp MCP server executes pytest as a subprocess and must return structured results to AI agents via JSON-RPC. pytest produces multiple output formats:

1. **Text Output**: Human-readable ANSI-formatted console output with test names, progress indicators, failure details, and summaries
2. **JSON Report** (via pytest-json-report plugin): Machine-readable structured data with test outcomes, durations, error details, and metadata
3. **Exit Codes**: Integer status codes indicating success/failure/error conditions

AI agents consuming these results need:
- **Test Outcomes**: Which tests passed/failed/skipped and why
- **Error Context**: Detailed failure messages and tracebacks for debugging
- **Test Identity**: Clear test node IDs for re-execution or filtering
- **Performance Data**: Test durations for identifying slow tests
- **Collection Metadata**: Total test counts, collection errors, warnings

Key design tensions:

1. **Completeness vs Conciseness**: Should we include full pytest output (verbose but complete) or summarize key information (concise but potentially incomplete)?

2. **Text vs Structured Data**: Should we prioritize JSON report data (structured, parseable) or text output (human-readable, detailed)?

3. **Error Detail Granularity**: How much traceback/error context should we include for failures?

4. **Multiple Representation**: Should results include both JSON report AND text output, or just one?

5. **Token Efficiency**: AI agents have token budgets; how do we balance information density with token consumption?

## Decision

**We will return BOTH structured JSON report data AND pytest text output, using a hybrid format optimized for AI agent consumption.**

Specifically:
- **Primary Structure**: JSON response with typed fields for test outcomes, counts, and metadata
- **JSON Report Inclusion**: Full pytest-json-report data for programmatic parsing
- **Text Output Inclusion**: Complete pytest text output for detailed failure context
- **Exit Code Reporting**: Explicit exit code field for success/failure determination
- **Failure Focus**: Include detailed tracebacks and error context for failed tests
- **Concise Success**: Minimal detail for passing tests (node ID and duration only)

Result schema:
```python
{
  "exit_code": int,           # pytest exit code (0=success, 1=failures, 2=error, etc.)
  "summary": {
    "total": int,
    "passed": int,
    "failed": int,
    "skipped": int,
    "errors": int,
    "duration": float
  },
  "tests": [                  # Detailed test results
    {
      "node_id": str,
      "outcome": str,         # "passed" | "failed" | "skipped" | "error"
      "duration": float,
      "message": str | null,  # Failure message or skip reason
      "traceback": str | null # Full traceback for failures
    }
  ],
  "json_report": {...},       # Complete pytest-json-report data
  "text_output": str,         # Full pytest console output
  "collection_errors": [...]  # Any errors during test collection
}
```

## Rationale

### Why Hybrid Format (JSON + Text)?

1. **Best of Both Worlds**: Structured data enables programmatic parsing; text output provides detailed human-readable context.

2. **AI Agent Flexibility**: Agents can parse structured fields for decision-making OR analyze text output for detailed debugging context.

3. **Failure Debugging**: Text output includes rich ANSI-formatted failure context (assertion diffs, local variables) that JSON report may not capture fully.

4. **Progressive Enhancement**: Agents can start with summary fields for quick decisions, then drill into detailed fields or text output as needed.

### Why Include BOTH json_report AND text_output?

**json_report Advantages**:
- Structured, predictable schema
- Programmatic access to test metadata
- Includes pytest plugin data (coverage, markers, etc.)
- Easy to filter/query specific tests

**text_output Advantages**:
- Complete failure context with assertion introspection
- Human-readable format familiar to developers
- Includes pytest warnings and informational messages
- Shows collection output and plugin messages

**Combined**: AI agents can parse structured data for logic, reference text output for context. Trade-off: Larger payload, but comprehensive information.

### Why Failure-Focused Detail?

1. **Token Efficiency**: Passing tests need minimal detail (node ID + duration). Failed tests need maximum context for debugging.

2. **AI Agent Workflow**: When tests pass, agents move forward. When tests fail, agents need full context to diagnose and fix issues.

3. **Asymmetric Information Need**: Success is binary (test passed). Failure requires explanation (why it failed, what went wrong, how to fix).

### Result Structure Examples

**All Tests Pass:**
```json
{
  "exit_code": 0,
  "summary": {
    "total": 10,
    "passed": 10,
    "failed": 0,
    "skipped": 0,
    "errors": 0,
    "duration": 2.34
  },
  "tests": [
    {"node_id": "test_foo.py::test_addition", "outcome": "passed", "duration": 0.01, "message": null, "traceback": null},
    {"node_id": "test_foo.py::test_subtraction", "outcome": "passed", "duration": 0.01, "message": null, "traceback": null}
    // ... 8 more passing tests
  ],
  "json_report": {...},
  "text_output": "======================== test session starts =========================\n...",
  "collection_errors": []
}
```

**Test Failure:**
```json
{
  "exit_code": 1,
  "summary": {
    "total": 10,
    "passed": 9,
    "failed": 1,
    "skipped": 0,
    "errors": 0,
    "duration": 2.45
  },
  "tests": [
    {"node_id": "test_foo.py::test_addition", "outcome": "passed", "duration": 0.01, "message": null, "traceback": null},
    // ... 8 more passing tests
    {
      "node_id": "test_foo.py::test_division",
      "outcome": "failed",
      "duration": 0.03,
      "message": "AssertionError: assert 0.5 == 0.6\n +  where 0.5 = divide(1, 2)",
      "traceback": "def test_division():\n>       assert divide(1, 2) == 0.6\nE       AssertionError: assert 0.5 == 0.6\nE        +  where 0.5 = divide(1, 2)\n\ntest_foo.py:42: AssertionError"
    }
  ],
  "json_report": {...},
  "text_output": "======================== test session starts =========================\n...\nFAILED test_foo.py::test_division - AssertionError: ...",
  "collection_errors": []
}
```

**Collection Error:**
```json
{
  "exit_code": 2,
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": 1,
    "duration": 0.05
  },
  "tests": [],
  "json_report": {...},
  "text_output": "======================== test session starts =========================\n...\nERROR: test_foo.py - ImportError: cannot import name 'divide'",
  "collection_errors": [
    {
      "file": "test_foo.py",
      "message": "ImportError: cannot import name 'divide' from 'foo'",
      "traceback": "..."
    }
  ]
}
```

## Consequences

### Positive Outcomes

1. **AI Agent Effectiveness**: Comprehensive results enable agents to make informed decisions about test outcomes and required fixes.

2. **Debugging Efficiency**: Detailed tracebacks and error context allow agents to diagnose failures without re-running tests.

3. **Flexible Consumption**: Agents can parse structured fields OR analyze text output based on their capabilities.

4. **Token-Efficient Success**: Minimal detail for passing tests reduces payload size when everything works.

5. **Complete Failure Context**: Full tracebacks and error messages provide maximum debugging information.

6. **Exit Code Transparency**: Explicit exit code field enables agents to distinguish success/failure/error conditions.

### Negative Outcomes / Constraints

1. **Payload Size**: Including both JSON report and text output creates larger responses.
   - **Mitigation**: Acceptable trade-off; comprehensive information worth extra tokens.
   - **Future Optimization**: Could add verbosity parameter to control detail level.

2. **Duplication**: Some information appears in both structured fields and text output.
   - **Rationale**: Duplication serves different consumption patterns (parsing vs reading).

3. **JSON Report Dependency**: Requires pytest-json-report plugin installation.
   - **Mitigation**: Documented dependency; included in project requirements.

4. **Serialization Overhead**: Converting pytest output to JSON adds processing time.
   - **Impact**: Minimal; pytest execution dominates latency; serialization negligible.

5. **Schema Evolution**: Result schema becomes API contract; changes require careful versioning.
   - **Mitigation**: Design schema for forward compatibility (optional fields, extensible structure).

### Future Decisions Enabled

- **ADR-007**: Clear exit code semantics enable precise error handling strategies
- **Caching/Optimization**: Structured results enable intelligent caching based on test outcomes
- **Incremental Testing**: Test node IDs and outcomes enable test selection strategies
- **Performance Monitoring**: Duration data enables test performance analysis

### Future Decisions Constrained

- Committed to hybrid JSON+text format; agents must handle both representations
- Result schema becomes API contract; breaking changes require version negotiation
- Must maintain pytest-json-report compatibility across pytest versions

## Alternatives Considered

### Alternative 1: JSON Report Only

**Why Rejected**:
- JSON report may not capture all pytest output (warnings, plugin messages)
- Assertion introspection details richer in text output
- Loses human-readable context useful for AI agents debugging failures
- Trade-off: Smaller payload BUT incomplete information

### Alternative 2: Text Output Only

**Why Rejected**:
- Difficult to parse programmatically (ANSI codes, varied formats)
- No structured access to test metadata (durations, counts)
- AI agents must parse unstructured text instead of structured fields
- Trade-off: Simpler implementation BUT harder consumption

### Alternative 3: Summarized Results Only

**Example**: Only return pass/fail counts and failed test node IDs
**Why Rejected**:
- Insufficient context for debugging failures
- Agents must re-run tests with increased verbosity to diagnose issues
- Poor developer experience (multiple round-trips to understand failures)
- Trade-off: Minimal payload BUT incomplete information

### Alternative 4: Streaming Results

**Example**: Stream test results as they complete (SSE or WebSocket)
**Why Rejected**:
- MCP protocol based on JSON-RPC request/response (no streaming)
- Adds complexity for minimal benefit (pytest tests typically complete quickly)
- AI agents expect complete results, not incremental updates
- Trade-off: Real-time feedback BUT protocol incompatibility

### Alternative 5: Verbosity Parameter

**Example**: Let AI agents control result detail level (minimal/normal/verbose)
**Why Rejected** (for initial version):
- Adds complexity to parameter validation
- AI agents must guess appropriate verbosity level
- Failure-focused design already provides efficient token usage
- **Revisit**: Could add in future if payload size becomes problematic

## Implementation Notes

### Result Serialization Function

```python
from typing import Dict, Any, List
import json

def serialize_pytest_results(
    exit_code: int,
    json_report_path: Path,
    text_output: str
) -> Dict[str, Any]:
    """Serialize pytest results to MCP response format."""

    # Load JSON report
    with open(json_report_path) as f:
        json_report = json.load(f)

    # Extract summary
    summary = {
        "total": json_report["summary"]["total"],
        "passed": json_report["summary"].get("passed", 0),
        "failed": json_report["summary"].get("failed", 0),
        "skipped": json_report["summary"].get("skipped", 0),
        "errors": json_report["summary"].get("error", 0),
        "duration": json_report["summary"]["duration"]
    }

    # Build test results with failure focus
    tests = []
    for test in json_report["tests"]:
        result = {
            "node_id": test["nodeid"],
            "outcome": test["outcome"],
            "duration": test["duration"],
            "message": None,
            "traceback": None
        }

        # Include details for non-passing tests
        if test["outcome"] in ["failed", "error"]:
            result["message"] = test.get("call", {}).get("longrepr")
            result["traceback"] = _format_traceback(test)
        elif test["outcome"] == "skipped":
            result["message"] = test.get("call", {}).get("longrepr")

        tests.append(result)

    # Extract collection errors
    collection_errors = [
        {
            "file": err.get("nodeid", "unknown"),
            "message": err.get("longrepr"),
            "traceback": err.get("longrepr")
        }
        for err in json_report.get("collectors", [])
        if err.get("outcome") == "failed"
    ]

    return {
        "exit_code": exit_code,
        "summary": summary,
        "tests": tests,
        "json_report": json_report,
        "text_output": text_output,
        "collection_errors": collection_errors
    }
```

### Token Usage Estimation

**Typical Scenarios:**

1. **10 passing tests**: ~2-3K tokens (minimal detail per test)
2. **10 tests, 1 failure**: ~4-6K tokens (one detailed traceback)
3. **10 tests, 5 failures**: ~10-15K tokens (five detailed tracebacks)
4. **Collection error**: ~1-2K tokens (error message + traceback)

**Token Budget Considerations:**
- Most test suites have high pass rates → token-efficient in common case
- Failures front-load detailed information → debugging without re-execution
- Large test suites (100+ tests) still manageable due to minimal passing test detail

## References

- ADR-001: MCP Protocol Selection (JSON-RPC response format)
- ADR-002: Stateless Architecture (results returned immediately, no session)
- ADR-004: pytest Subprocess Integration (subprocess produces output to serialize)
- ADR-005: Parameter Validation Strategy (validated parameters produce predictable results)
- [pytest-json-report Plugin](https://github.com/numirias/pytest-json-report)
- [pytest Output Formats](https://docs.pytest.org/en/stable/how-to/output.html)
- REQUIREMENTS_ANALYSIS.md: FR-1.2 (Execute tests with proper result reporting)
- EVENT_MODEL.md: Workflow 2 shows result formatting in execute_tests command
