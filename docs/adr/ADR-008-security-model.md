# ADR-008: Security Model (Constraint-Based Interface)

**Status**: accepted

**Date**: October 3, 2025 (Friday) - Accepted October 3, 2025

**Project**: pytest-mcp

## Context

AI agents integrating with MCP servers represent a novel security challenge. Unlike traditional user-driven tools, AI agents:

1. **Interpret Natural Language**: Commands derived from ambiguous user requests, not explicit parameters
2. **Generate Tool Calls**: Construct arguments programmatically, increasing risk of malformed or malicious inputs
3. **Chain Operations**: May combine multiple tool calls based on prior results
4. **Operate Autonomously**: Less human oversight per individual operation

Traditional security approaches for developer tools assume:
- Human users understand command syntax and consequences
- Shell access is acceptable for local development
- Developers can visually inspect commands before execution
- Trust boundary is "user vs system," not "AI agent vs system"

The pytest-mcp server must provide a **safe interface for AI-driven test execution** while maintaining developer productivity.

Key security tensions:

1. **Expressiveness vs Safety**: Rich pytest functionality requires many parameters, but each parameter is an attack surface.

2. **Flexibility vs Constraints**: Developers need to run arbitrary pytest commands; AI agents should not have shell access.

3. **Isolation vs Performance**: Strong isolation (containers, VMs) improves security but adds complexity and latency.

4. **Trust Model**: Should we trust the AI agent, the user, both, or neither?

5. **Error Information**: Security errors need enough detail for debugging but not enough to aid attackers.

## Decision

**pytest-mcp employs a constraint-based security model: AI agents operate through a structured, constrained interface that prevents entire classes of attacks by design.**

Specifically:

### Security Architecture Principles

1. **No Shell Access**: AI agents never execute arbitrary shell commands. All operations flow through structured MCP tool calls with validated parameters.

2. **Structured Parameters Only**: Tool accepts typed, validated parameters (paths, flags, markers) defined in schema. No command string concatenation.

3. **Subprocess Isolation**: pytest executes in subprocess with no inherited environment variables or file descriptors beyond necessity.

4. **Path Validation**: All filesystem paths validated for existence, type (file/directory), and absence of path traversal attacks.

5. **Parameter Allowlisting**: Only explicitly documented pytest parameters permitted. Unknown flags rejected at validation layer.

6. **Exit Code Semantics**: Clear distinction between test failures (data) and execution failures (errors) prevents security-relevant conditions from being ignored.

### Trust Model

**Trusted**:
- User who configured MCP server (owns filesystem, controls pytest installation)
- pytest binary and plugins (user installed and controls)
- Python environment executing MCP server

**Untrusted**:
- AI agent tool calls (may be malformed, malicious, or exploitative)
- User's natural language requests to AI (may be misinterpreted or contain injection attempts)
- Test code itself (may contain bugs, but that's pytest's security domain)

**Security Boundary**: The MCP server is the trust boundary. Parameters entering from AI agent are untrusted until validated.

### Attack Vectors Mitigated

#### 1. Command Injection

**Attack**: AI agent attempts to inject shell commands via parameter manipulation.

```
# Example Attack Attempt:
{
  "test_path": "tests/; rm -rf /; #"
}
```

**Mitigation**:
- **No Shell Execution**: subprocess.run() called with list arguments, never shell=True
- **Path Validation**: Rejects paths containing command separators (`;`, `|`, `&`)
- **Type Enforcement**: Schema validation ensures test_path is string, not command sequence

**Status**: ✅ Prevented by design (ADR-004, ADR-005)

#### 2. Path Traversal

**Attack**: AI agent attempts to access files outside project directory.

```
# Example Attack Attempt:
{
  "test_path": "../../../etc/passwd"
}
```

**Mitigation**:
- **Path Normalization**: Resolve paths to absolute, normalized form
- **Existence Checks**: Validate paths exist and are files/directories as expected
- **No Symlink Following** (future enhancement): Reject symlinks pointing outside project root

**Status**: ✅ Prevented by ADR-005 validation rules

#### 3. Arbitrary Code Execution via Plugins

**Attack**: AI agent specifies malicious pytest plugin via `-p` parameter.

```
# Example Attack Attempt:
{
  "extra_args": ["-p", "malicious_plugin"]
}
```

**Mitigation**:
- **Plugin Parameter Blocked**: `-p` flag not in allowlist (ADR-005)
- **No Dynamic Plugin Loading**: pytest uses pre-configured environment plugins only
- **Future**: Explicit plugin allowlist if needed

**Status**: ✅ Prevented by parameter allowlisting

#### 4. Environment Variable Injection

**Attack**: AI agent attempts to modify behavior via environment variables.

```
# Example Attack Attempt:
{
  "environment": {
    "PYTEST_CURRENT_TEST": "hijacked",
    "LD_PRELOAD": "/path/to/malicious.so"
  }
}
```

**Mitigation**:
- **No Environment Parameter**: Tool schema does not accept environment variables
- **Clean Environment**: subprocess spawned with sanitized environment (future enhancement)

**Status**: ✅ Prevented by schema design (ADR-001, ADR-005)

#### 5. Resource Exhaustion

**Attack**: AI agent triggers infinite test loops or memory exhaustion.

```
# Example Attack Attempt:
{
  "test_path": "tests/infinite_loop_test.py"
}
```

**Mitigation**:
- **Timeout Enforcement**: Subprocess killed after configurable timeout (ADR-007)
- **No Resource Limit Controls**: AI agent cannot disable timeouts
- **Future**: Memory/CPU limits via cgroups or process resource limits

**Status**: ✅ Timeout mitigates; full resource limits future work

#### 6. Information Disclosure via Error Messages

**Attack**: AI agent probes filesystem or system state via error messages.

```
# Example Attack Attempt:
{
  "test_path": "/etc/shadow"  # Probe for existence
}
```

**Mitigation**:
- **Generic Error Messages**: Path validation errors do not reveal filesystem structure beyond project directory
- **No Stack Traces in Production**: Internal errors sanitized before returning to agent
- **Structured Error Data**: Error context limited to execution-relevant information (ADR-007)

**Status**: ⚠️ Partially mitigated; production deployment should sanitize error details further

#### 7. Test Code Tampering

**Attack**: AI agent modifies test files before execution.

```
# Example: AI agent writes malicious code to test file
```

**Mitigation**:
- **Out of Scope**: pytest-mcp does not provide file modification capabilities
- **Assumption**: Test file modification is separate MCP tool with own security model
- **Principle**: pytest-mcp only executes existing tests, never modifies code

**Status**: ✅ Out of scope by design (ADR-002: stateless, read-only execution)

### Security vs Usability Trade-offs

| Security Measure | Usability Impact | Justification |
|-----------------|------------------|---------------|
| No shell access | Cannot use shell features (pipes, globs) | Eliminates command injection entirely |
| Parameter allowlist | Cannot use all pytest flags | Most flags unnecessary for AI agent use cases |
| Path validation | Cannot test files outside project | AI agents should operate within project scope |
| Timeout enforcement | Long test suites may be killed | Configurable timeout balances safety and flexibility |
| No environment control | Cannot set pytest environment variables | Reduces attack surface; environment pre-configured |

## Rationale

### Why Constraint-Based Interface?

1. **Attack Prevention by Design**: Attacks impossible to attempt, not just detected and blocked.
   - No code path exists for command injection
   - Type system enforces parameter constraints
   - Validation layer is unavoidable chokepoint

2. **AI-Appropriate Abstraction**: AI agents excel at structured tool calls; shell commands are human-centric.
   - LLMs better at generating JSON than shell syntax
   - Validation errors clearer than shell errors
   - Structured results easier for agents to parse

3. **Defense in Depth**: Multiple layers prevent attacks:
   - Schema validation (MCP layer)
   - Parameter validation (application layer)
   - subprocess.run() safety (execution layer)
   - Timeout enforcement (resource layer)

4. **Audit Trail**: Structured parameters are loggable and auditable.
   - Can log exact tool calls for security review
   - Can detect anomalous parameter patterns
   - Future: Rate limiting or anomaly detection

### Why Subprocess Isolation?

1. **Blast Radius Limitation**: pytest bugs or malicious test code cannot escape subprocess.

2. **Resource Control**: Timeouts, future memory limits enforceable at process boundary.

3. **Clean State**: Each execution starts fresh; no state leakage between runs (ADR-002).

4. **Standard Practice**: subprocess isolation is battle-tested security pattern.

### Why Parameter Allowlisting (Not Blocklisting)?

**Allowlisting Approach**:
- Define safe parameters explicitly
- Reject anything not on allowlist
- Safe by default; additions require deliberate decisions

**Blocklisting Approach** (rejected):
- Define dangerous parameters explicitly
- Allow everything else
- Dangerous by default; blocklist inevitably incomplete

**Rationale**: New pytest flags unknown to MCP server are rejected, not silently passed through. Prevents exploitation of undocumented or future pytest features.

### Why Trust pytest Binary?

pytest installation is **trusted** because:
- User controls Python environment and package installation
- User could already execute pytest directly with full capabilities
- MCP server cannot be more secure than underlying pytest installation

**Scope**: pytest-mcp secures **AI agent interface**, not pytest itself. pytest security is separate concern.

## Consequences

### Positive Outcomes

1. **Entire Attack Classes Eliminated**: Command injection, arbitrary execution impossible by design.

2. **Clear Security Boundary**: Trust model explicit; AI agents clearly untrusted.

3. **Auditable Operations**: Structured parameters enable security monitoring and logging.

4. **Fail-Safe Defaults**: Unknown parameters rejected; timeouts enforced; paths validated.

5. **AI-Friendly Interface**: Structured constraints easier for LLMs than shell syntax.

6. **Composable Security**: Each ADR adds security layer:
   - ADR-001: Schema validation at MCP layer
   - ADR-005: Parameter validation at application layer
   - ADR-004: Subprocess isolation at execution layer
   - ADR-007: Timeout enforcement at resource layer

### Negative Outcomes / Constraints

1. **Reduced Flexibility**: Cannot use all pytest features (e.g., custom plugins via `-p`).
   - **Acceptable**: AI-driven testing focuses on common workflows, not edge cases.

2. **Parameter Allowlist Maintenance**: New pytest features require allowlist updates.
   - **Mitigation**: Conservative allowlist; additions driven by user requests.

3. **False Positives**: Legitimate use cases may be blocked by overly strict validation.
   - **Example**: Unusual but valid path structures
   - **Mitigation**: Validation rules tuned based on real-world usage.

4. **Incomplete Information Disclosure Protection**: Error messages may leak some filesystem information.
   - **Future Work**: Production mode with sanitized error messages.

5. **No Protection Against Malicious Tests**: pytest executes user's test code; malicious tests can harm system.
   - **Out of Scope**: pytest-mcp assumes test code is user-controlled and trusted.

### Future Decisions Enabled

- Enhanced resource limits (memory, CPU, file descriptors)
- Audit logging and anomaly detection
- Rate limiting for AI agent requests
- Sandboxing (containers, VMs) for untrusted test execution
- Cryptographic signing of test results

### Future Decisions Constrained

- Cannot add shell command parameter without violating security model
- Parameter additions require security review and allowlist update
- Stateless design (ADR-002) prevents sophisticated attack detection (e.g., rate limiting requires state)

## Alternatives Considered

### Alternative 1: Shell Command Interface

**Approach**: Tool accepts arbitrary shell command string; execute via `shell=True`.

**Why Rejected**:
- Command injection trivial for AI agents generating strings
- Entire security model collapses to "trust the AI agent"
- Shell syntax fragile; small errors cause failures
- No structured validation possible
- Error handling ambiguous (shell errors vs pytest errors)

**Fatal Flaw**: Eliminates all security guarantees.

### Alternative 2: Blocklist Dangerous Parameters

**Approach**: Allow all pytest parameters except explicitly blocked ones.

**Why Rejected**:
- Blocklist inevitably incomplete (new pytest flags, undocumented features)
- Insecure by default; requires ongoing maintenance
- Future pytest versions may introduce exploitable flags
- Cannot anticipate all attack vectors

**Better**: Allowlist provides safe-by-default foundation.

### Alternative 3: Sandbox All Execution (Containers)

**Approach**: Execute pytest in Docker container or VM with no host access.

**Why Rejected**:
- Significant complexity for local development tool
- Performance overhead (container startup latency)
- Requires Docker/VM infrastructure (bad DX for many developers)
- Overkill for trust model (user already controls filesystem)

**Revisit**: Valuable for cloud-hosted MCP servers or untrusted test execution.

### Alternative 4: Trust AI Agent Completely

**Approach**: No validation; assume AI agent is benevolent and competent.

**Why Rejected**:
- AI agents make mistakes (hallucinate parameters, misinterpret requests)
- User requests may contain accidental injection patterns
- No defense against compromised AI agent or prompt injection attacks
- Violates principle of least privilege

**Fatal Flaw**: Single point of failure (AI agent trustworthiness).

### Alternative 5: Execute pytest as User's Shell Command

**Approach**: MCP server constructs shell command and uses user's shell to execute.

**Why Rejected**:
- Inherits shell's environment and complexity
- Shell injection via parameter concatenation
- Shell syntax varies across platforms (bash, zsh, PowerShell)
- Loses structured parameter validation

**Better**: Subprocess with list arguments is portable and secure.

### Alternative 6: No Timeout Enforcement

**Approach**: Allow pytest to run indefinitely; trust user to kill runaway processes.

**Why Rejected**:
- Resource exhaustion attacks possible
- AI agents cannot manually intervene to kill processes
- Hung tests block MCP server indefinitely
- Poor UX for AI-driven workflows

**Better**: Configurable timeout balances safety and flexibility (ADR-007).

## Implementation Notes

### Security Checklist for Parameter Validation

```python
def validate_security_constraints(params: dict[str, Any]) -> None:
    """Security-focused validation before pytest execution."""

    # Path Traversal Prevention
    if "test_path" in params:
        path = Path(params["test_path"]).resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if ".." in str(path):  # After normalization, this shouldn't happen
            raise ValueError("Path traversal detected")

    # Command Injection Prevention
    if "extra_args" in params:
        for arg in params["extra_args"]:
            if any(char in arg for char in [";", "|", "&", "\n", "`"]):
                raise ValueError(f"Prohibited character in argument: {arg}")

    # Plugin Injection Prevention
    if "extra_args" in params:
        for arg in params["extra_args"]:
            if arg.startswith("-p"):
                raise ValueError("Plugin loading via -p flag prohibited")

    # Allowlist Validation
    allowed_flags = {"-v", "-s", "-x", "-k", "-m", "--tb", "--maxfail", ...}
    for arg in params.get("extra_args", []):
        if arg.startswith("-") and arg not in allowed_flags:
            raise ValueError(f"Unknown or prohibited flag: {arg}")
```

### Subprocess Security Hardening

```python
import subprocess
from pathlib import Path

def execute_pytest_securely(
    command: list[str],
    timeout: float,
    cwd: Path
) -> subprocess.CompletedProcess:
    """Execute pytest with security hardening."""

    # Security: Use list arguments (not shell)
    # Security: Set timeout to prevent resource exhaustion
    # Security: Sanitize environment (future enhancement)
    # Security: Set working directory explicitly

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        shell=False,  # CRITICAL: Never use shell=True
        # Future: env={...}  # Clean environment
    )

    return result
```

### Error Message Sanitization

```python
def sanitize_error_for_agent(error: Exception, include_details: bool = False) -> dict:
    """Sanitize error messages to prevent information disclosure."""

    if include_details:
        # Development mode: Full details
        return {
            "message": str(error),
            "type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
    else:
        # Production mode: Generic message
        return {
            "message": "pytest execution failed",
            "type": "ExecutionError",
            "hint": "Check server logs for details"
        }
```

## References

- ADR-001: MCP Protocol Selection (structured parameters, schema validation)
- ADR-002: Stateless Architecture (no persistent state, each execution isolated)
- ADR-004: pytest Subprocess Integration (subprocess isolation)
- ADR-005: Parameter Validation Strategy (allowlisting, path validation)
- ADR-006: Result Structuring and Serialization (structured output, no shell parsing)
- ADR-007: Error Handling and Exit Code Semantics (timeout enforcement, error context)
- REQUIREMENTS_ANALYSIS.md: NFR-2.1 (Security constraints), NFR-2.2 (Safe parameter handling)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [Python subprocess Security](https://docs.python.org/3/library/subprocess.html#security-considerations)
