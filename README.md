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

## CLI examples

Inspect record-type counts:

```bash
hytek inspect samples/meet.hy3
```

Dump every record without decoding fields:

```bash
hytek dump samples/meet.hy3
```

Example output:

```text
Record 1
  Byte offset: 0
  Line number: 1
  Record type: D0
  Record length: 8
  Raw text: D0header

Record 2
  Byte offset: 9
  Line number: 2
  Record type: D1
  Record length: 130
  Raw text: D1M    1Smith               John                Johnny              J12345678901234   4207212012 13                             00
```
