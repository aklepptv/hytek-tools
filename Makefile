PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
BLACK := .venv/bin/black
MYPY := .venv/bin/mypy

.PHONY: dev test lint format typecheck check

dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST)

lint:
	$(RUFF) check .

format:
	$(BLACK) .

typecheck:
	$(MYPY) src

check:
	$(RUFF) check .
	$(BLACK) --check .
	$(MYPY) src
	$(PYTEST)
