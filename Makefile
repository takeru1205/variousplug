# Makefile for VariousPlug development and testing

.PHONY: help test test-unit test-integration test-coverage lint format type-check dev-install clean build

# Default target
help:
	@echo "VariousPlug Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  dev-install     Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-verbose   Run tests with verbose output"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run all linting tools"
	@echo "  format        Format code with black and isort"
	@echo "  type-check    Run mypy type checking"
	@echo ""
	@echo "Build:"
	@echo "  build         Build the package"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make dev-install"
	@echo "  make test"
	@echo "  make test-coverage"
	@echo "  make lint"

# Development setup
dev-install:
	@echo "Installing development dependencies..."
	uv sync
	uv pip install -e ".[dev]"
	@echo "Development environment ready!"

# Testing commands
test:
	@echo "Running all tests..."
	uv run pytest

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/unit/ -m "not integration"

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/ -m "integration"

test-coverage:
	@echo "Running tests with coverage..."
	uv run pytest --cov=variousplug --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/"

test-verbose:
	@echo "Running tests with verbose output..."
	uv run pytest -v -s

test-fast:
	@echo "Running fast tests (excluding slow tests)..."
	uv run pytest -m "not slow"

test-api:
	@echo "Running tests that require API keys..."
	uv run pytest -m "requires_api_key"

# Code quality
lint: lint-ruff lint-mypy
	@echo "All linting completed!"

lint-ruff:
	@echo "Running ruff linter..."
	uv run ruff check .

lint-mypy:
	@echo "Running mypy..."
	uv run mypy src/

format:
	@echo "Formatting code with ruff..."
	uv run ruff format .
	@echo "Code formatting completed!"

format-check:
	@echo "Checking code formatting..."
	uv run ruff format --check .
	uv run ruff check .

type-check:
	@echo "Running type checking..."
	uv run mypy src/

# Build commands
build:
	@echo "Building package..."
	uv build

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean completed!"

# Development workflow
check: format lint test
	@echo "All checks passed!"

ci: format-check lint test-coverage
	@echo "CI checks completed!"

# Ruff specific commands
ruff-fix:
	@echo "Running ruff with auto-fix..."
	uv run ruff check --fix .

ruff-unsafe-fix:
	@echo "Running ruff with unsafe auto-fix..."
	uv run ruff check --fix --unsafe-fixes .

# Quick development commands
quick-test:
	@echo "Running quick tests..."
	uv run pytest tests/unit/ -x --tb=short

watch-test:
	@echo "Watching for changes and running tests..."
	uv run pytest-watch -- tests/unit/

# Documentation
docs-serve:
	@echo "Serving documentation..."
	@echo "Documentation available at:"
	@echo "  - RunPod Guide: docs/runpod-guide.md"
	@echo "  - Vast.ai Guide: docs/vast-ai-guide.md"

# Installation verification
verify-install:
	@echo "Verifying installation..."
	uv run vp --help
	@echo "Installation verified!"

# Debug and troubleshooting
debug-env:
	@echo "Debug information:"
	@echo "Python version:"
	python --version
	@echo ""
	@echo "UV version:"
	uv --version
	@echo ""
	@echo "Installed packages:"
	uv pip list
	@echo ""
	@echo "Current directory:"
	pwd
	@echo ""
	@echo "Project structure:"
	find . -name "*.py" -type f | head -20

# Testing specific components
test-config:
	@echo "Testing configuration management..."
	uv run pytest tests/unit/test_config.py -v

test-clients:
	@echo "Testing platform clients..."
	uv run pytest tests/unit/test_vast_client.py tests/unit/test_runpod_client.py -v

test-cli:
	@echo "Testing CLI..."
	uv run pytest tests/unit/test_cli.py -v

test-base:
	@echo "Testing base classes..."
	uv run pytest tests/unit/test_base.py -v

# Performance testing
test-performance:
	@echo "Running performance tests..."
	uv run pytest tests/ -k "performance" --tb=short

# Security testing
test-security:
	@echo "Running security-related tests..."
	uv run pytest tests/ -k "security" --tb=short