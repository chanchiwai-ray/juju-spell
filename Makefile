help:  # Display help
	@echo "Usage: make [target] [ARGS='additional args']\n\nTargets:"
	@awk -F'#' '/^[a-z-]+:/ { sub(":.*", "", $$1); print " ", $$1, "#", $$2 }' Makefile | column -t -s '#'

all: fix static  # Run all quick, local commands

fix:  # Format the Python code
	uv run codespell -w .
	uv run ruff format .
	uv run ruff check --fix --exit-zero --silent .

static:  # Run static code analysis
	uv run codespell .
	uv run ruff format --diff .
	uv run ruff check --no-fix .
	uv run mypy --install-types --non-interactive .
