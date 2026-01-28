# OPGEE Makefile
#
# Uses uv for Python package management
# See: https://docs.astral.sh/uv/

.PHONY: test test-v test-cov lint format check clean build upload docs help

# ============================================
# Development
# ============================================

test:  ## Run tests
	uv run pytest

test-v:  ## Run tests (verbose)
	uv run pytest -v

test-cov:  ## Run tests with coverage
	uv run pytest --cov=opgee

lint:  ## Run linter
	uv run ruff check .

format:  ## Format code
	uv run ruff format .

check: lint test  ## Run all checks (lint + test)
	@echo "All checks passed"

dev:  ## Install in development mode
	uv sync

# ============================================
# Build & Release
# ============================================

build:  ## Build sdist and wheel
	uv build

clean-build:  ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info/

upload-test: build  ## Upload to TestPyPI
	uv run twine upload dist/* -r testpypi

upload: build  ## Upload to PyPI
	uv run twine upload dist/*

# ============================================
# Documentation
# ============================================

docs:  ## Build HTML documentation
	uv run make -C docs html

docs-pdf:  ## Build PDF documentation
	uv run make -C docs latexpdf

clean-docs:  ## Clean documentation build
	make -C docs clean

# ============================================
# Cleanup
# ============================================

clean: clean-build clean-docs  ## Clean all build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ============================================
# Help
# ============================================

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
