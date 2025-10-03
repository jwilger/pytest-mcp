{
  description = "pytest-mcp: MCP server providing standardized pytest execution for AI agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python 3.12+ environment with all development dependencies
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Core dependencies
          pip
          setuptools
          pytest
          pytest-cov
          pydantic

          # Development tools
          mypy
          # Note: ruff is a top-level package, added to buildInputs below
          # Note: bandit is a Python package
          bandit
          hypothesis

          # MCP and reporting
          pytest-json-report
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.ruff    # Linting and formatting tool
            pkgs.mutmut  # Mutation testing for Python
          ];

          shellHook = ''
            echo "=================================================="
            echo "pytest-mcp Development Environment"
            echo "=================================================="
            echo ""
            echo "Python: $(python --version)"
            echo ""
            echo "Available Development Tools:"
            echo "  pytest        - Test execution"
            echo "  pytest-cov    - Test coverage reporting"
            echo "  mypy          - Type checking (strict mode)"
            echo "  ruff          - Linting and formatting (ALL rules)"
            echo "  bandit        - Security scanning"
            echo "  hypothesis    - Property-based testing"
            echo "  mutmut        - Mutation testing"
            echo ""
            echo "Quick Start:"
            echo "  mypy .              # Type check"
            echo "  ruff check .        # Lint code"
            echo "  ruff format .       # Format code"
            echo "  pytest              # Run tests"
            echo "  pytest --cov=src    # Run tests with coverage"
            echo "  bandit -r src/      # Security scan"
            echo "  mutmut run          # Run mutation tests"
            echo ""
            echo "Environment ready!"
            echo "=================================================="
            echo ""
          '';

          # Environment variables for tool configuration
          PYTHON_VERSION = "3.12";

          # Mypy configuration
          MYPY_CACHE_DIR = ".mypy_cache";

          # Pytest configuration
          PYTEST_CACHE_DIR = ".pytest_cache";

          # Development quality thresholds
          COVERAGE_MINIMUM = "80";
          MUTATION_SCORE_MINIMUM = "80";
          TRACE_SCORE_MINIMUM = "70";
        };
      }
    );
}
