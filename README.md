# pytest-mcp

MCP server providing opinionated pytest execution interface for AI agents.

## Overview

pytest-mcp is a Model Context Protocol (MCP) server that enables AI coding assistants to execute pytest with intelligent test selection, structured result interpretation, and context-aware recommendations.

## Status

This project is in active development. The current skeleton app is a minimal placeholder to validate CI infrastructure. Full MCP server functionality is coming soon.

## Development

This project uses Nix for reproducible development environments. To get started:

```bash
# Enter development shell
nix develop

# Run tests
pytest

# Run type checking
mypy src

# Run linting
ruff check src tests

# Run security scanning
bandit -r src
```

## License

MIT License - See LICENSE file for details.
