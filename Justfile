# Justfile for Wrench project
# This file defines tasks for building, testing, linting, and running examples
# Use `just --list` to see available tasks

#
# tools/jira:
#         uv run -- python -m tools.jira_components --sep ';' --header no $(project)
#
# tools/sonar:
#         uv run -- python -m tools.sonar_metrics --sep ';' --header no $(org)
#
# tools/sc:
#         uv run -- python -m tools.softwarecatalog export --format csv --filename data/out/sc_entities.csv
# #       uv run -- python -m tools.softwarecatalog export --format json |jq
#
# tools/gh:
#         uv run -- python -m tools.github
#
# test:
#         uv run -- pytest
#


# set dotenv-load

ARGS_TEST := env("_UV_RUN_ARGS_TEST", "")

@_:
   just --list

# Run Software Catalog exporter
[group('tools')]
run-sc-exporter:
    uv run -m tools.sc-exporter export --format json --filename out.json # --verbose

# Run examples
examples:
    uv run python examples/backstage_example.py

# Run tests
[group('qa')]
test *args:
    uv run {{ ARGS_TEST }} -m pytest {{ args }}

_cov *args:
    uv run -m coverage {{ args }}

# Run tests and measure coverage
[group('qa')]
@cov:
    just _cov erase
    just _cov run -m pytest tests
    just _cov report

# Run linters
[group('qa')]
lint:
    uvx ruff check
    uvx ruff format

# Check types
[group('qa')]
typing:
    uvx ty check --python .venv src

# Perform all checks
[group('qa')]
check-all: lint cov typing

# Update dependencies
[group('lifecycle')]
update:
    uv sync --upgrade

# Ensure project virtualenv is up to date
[group('lifecycle')]
install:
    uv sync

# Remove temporary files
[group('lifecycle')]
clean:
    rm -rf .venv .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
    find . -type d -name "__pycache__" -exec rm -r {} +

# Recreate project virtualenv from nothing
[group('lifecycle')]
fresh: clean install

# vim: set filetype=Makefile ts=4 sw=4 et:
