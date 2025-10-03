{
  description = "pytest-mcp: MCP server providing standardized pytest execution for AI agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            # Python runtime
            pkgs.python312

            # UV package manager - handles all Python dependencies
            pkgs.uv

            # System-level development tools
            pkgs.git
            pkgs.ruff    # Linting and formatting tool
            pkgs.mypy    # Type checking
            pkgs.bandit  # Security scanning
            pkgs.mutmut  # Mutation testing for Python
          ];

          shellHook = ''
            # Set up uv-managed virtual environment
            if [ ! -d .venv ]; then
              echo "Creating virtual environment with uv..."
              uv venv
            fi

            # Activate the virtual environment
            source .venv/bin/activate

            echo "=================================================="
            echo "pytest-mcp Development Environment"
            echo "=================================================="
            echo ""
            echo "Python: $(python --version)"
            echo "Virtual Environment: .venv (uv-managed)"
            echo ""
            echo "Dependency Management:"
            echo "  uv sync              - Install/sync dependencies from pyproject.toml"
            echo "  uv add <package>     - Add a new dependency"
            echo "  uv add --dev <pkg>   - Add a development dependency"
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
            echo "  uv sync             # Sync dependencies first!"
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
