# HYTEK Tools

Open-source toolkit for reading, validating, comparing, and converting HY-TEK swimming meet files.

## First-time setup

Requires Python 3.12 or newer.

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

Or set up manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Development commands

| Command | Description |
| --- | --- |
| `make dev` | Install editable package with dev dependencies and pre-commit hooks |
| `make test` | Run the test suite |
| `make lint` | Run Ruff |
| `make format` | Format with Black and apply Ruff fixes |
| `make typecheck` | Run MyPy |
| `make check` | Run lint, typecheck, and tests |
