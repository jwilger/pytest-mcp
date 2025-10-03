# ADR-002: Stateless Architecture for MCP Server

**Status**: accepted

**Date**: October 3, 2025 (Friday) - Accepted October 3, 2025

**Project**: pytest-mcp

## Context

The pytest-mcp MCP server executes pytest operations on behalf of AI assistants. Each MCP tool invocation (test discovery, test execution) represents a discrete operation that AI agents request independently.

When designing the server architecture, we must decide whether to maintain state between operations or treat each tool invocation as stateless. Key considerations include:

1. **Execution Independence**: pytest itself is stateless - each `pytest` command invocation starts fresh without dependencies on previous runs.

2. **AI Interaction Patterns**: AI assistants typically make independent, context-free tool calls based on current user conversation state, not server session history.

3. **Server Lifecycle**: MCP servers may be started/stopped frequently by AI assistant hosts, making long-lived state management complex.

4. **Concurrency**: Multiple AI assistants or parallel tool invocations may interact with the same MCP server instance.

## Decision

**We will implement the pytest-mcp server as stateless, treating each MCP tool invocation as an independent, self-contained operation.**

The server will:
- Accept all necessary parameters for each operation within the tool call itself
- Not maintain execution history, cached results, or session state between tool invocations
- Invoke pytest programmatically as a fresh operation for each request
- Return complete, self-contained responses requiring no prior context

## Rationale

### Why Stateless Architecture?

1. **Alignment with pytest Model**: pytest itself operates statelessly - each execution is independent. Introducing state in the MCP layer would create impedance mismatch without clear benefit.

2. **Simpler Mental Model**: AI agents provide all context per request, receive complete responses, and make independent decisions. No need to track "what happened before" across tool calls.

3. **Concurrency Without Complexity**: Stateless design eliminates race conditions, locking requirements, and state synchronization challenges when handling parallel requests.

4. **Server Lifecycle Resilience**: Server restarts, crashes, or protocol reconnections don't lose critical state because there is no state to lose. Each operation stands alone.

5. **Predictable Behavior**: Same input parameters always produce same behavior, regardless of previous operations. No hidden dependencies on execution history.

6. **Testing Simplicity**: Stateless operations are trivial to test - provide inputs, assert outputs, no setup/teardown of shared state required.

### Why NOT Stateful Alternatives?

**Alternative: Cache Test Discovery Results**
- **Rejected**: Test structure changes frequently during development; cache invalidation becomes complex
- AI agents re-discover tests when needed; discovery operations are fast enough without caching
- Cached state can become stale, leading to incorrect AI decisions based on outdated information

**Alternative: Maintain Execution History**
- **Rejected**: AI assistants don't need server-side history; they maintain conversation context themselves
- Adds memory management complexity without corresponding benefit
- History persistence across server restarts adds implementation and operational burden

**Alternative: Session-Based State Management**
- **Rejected**: MCP protocol doesn't provide session affinity guarantees; state could be lost arbitrarily
- Multiple AI assistants may share same MCP server; session isolation becomes complex
- Requires explicit session lifecycle management (create, destroy, timeout) with no clear use case

**Alternative: Connection-Scoped State**
- **Rejected**: MCP connection lifecycle is managed by AI assistant host, not our control
- Connection drops require state recovery mechanisms
- State scoped to connection doesn't survive assistant restarts, limiting usefulness

## Consequences

### Positive Outcomes

1. **Implementation Simplicity**: No state management code, no locks, no synchronization primitives needed.

2. **Operational Reliability**: Server crashes/restarts have no impact on correctness; no state recovery mechanisms required.

3. **Horizontal Scalability**: Multiple server instances can handle requests without state coordination (if scaling becomes relevant).

4. **Deterministic Testing**: Every operation testable in isolation with complete input → output verification.

5. **Reduced Bug Surface**: Entire class of state-related bugs (race conditions, stale cache, memory leaks) eliminated by design.

### Negative Outcomes / Constraints

1. **No Cross-Operation Optimization**: Cannot cache discovery results or reuse pytest session setup across invocations.

2. **Potential Redundant Work**: AI agents may request same test discovery multiple times; each invocation repeats the work.

3. **No Historical Analytics**: Server cannot track trends, execution patterns, or performance metrics across runs without external logging infrastructure.

4. **Parameter Repetition**: AI agents must provide complete context (paths, options, filters) with every tool call; cannot rely on "previously set" state.

### Future Decisions Enabled

- **ADR-003**: Stateless design enables simple pytest subprocess invocation per request without session management complexity
- **ADR-004**: Parameter validation can focus solely on single-request completeness without considering state dependencies
- **ADR-005**: Response structures need only contain current operation results, not historical context

### Future Decisions Constrained

- Cannot introduce caching, history tracking, or session features without reversing this architectural decision
- Performance optimizations must focus on single-operation efficiency, not cross-operation state reuse
- Any future logging/metrics must be push-based to external systems, not accumulated in server memory

## Alternatives Considered

See "Why NOT Stateful Alternatives?" section in Rationale above for detailed analysis of:
- Cached test discovery results
- Execution history maintenance
- Session-based state management
- Connection-scoped state

## References

- ADR-001: MCP Protocol Selection (establishes MCP context for architectural decisions)
- [MCP Protocol Specification](https://modelcontextprotocol.io/) - MCP stateless tool invocation model
- EVENT_MODEL.md: All workflows show independent tool invocations without state dependencies
