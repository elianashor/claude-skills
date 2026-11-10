# Contributing

## Setup

```bash
pip install -e ".[dev]"
pre-commit install        # optional: ruff, sync check, guard and lint on every commit
```

## The one rule about scripts

Every script a skill ships is a copy of a module in `src/pincite/`. Edit the module, never the copy, then run:

```bash
python tools/sync_scripts.py
```

CI fails if a copy drifts. The mapping lives in `tools/sync.json`. Each module must stay self-contained (standard library plus `openpyxl` and `pdfplumber`) so that a skill uploaded on its own still runs.

## Before you open a pull request

```bash
ruff check . && ruff format --check .
python -m pytest
pincite lint --strict
pincite guard
```

## Fixtures

Tests use synthetic documents built in `tests/conftest.py`. Never add a real report, deposition, expert file or anything produced in a matter, even redacted.

## Changing a skill

Skills update themselves from user feedback, but only with format and method rules. A refinement must never carry content, names, figures or anything traceable to a source document. If a change would weaken the fidelity, verification or confidentiality rules, it does not go in.

## Releasing

1. Bump the version in `src/pincite/__init__.py` and both `plugins/*/.claude-plugin/plugin.json` files.
2. Add a section to `CHANGELOG.md`.
3. Tag `vX.Y.Z` and push the tag. The release workflow checks that all versions agree, runs the tests, and publishes the skill bundles, plugin bundles, wheel, sdist and checksums.

PyPI publishing stays off until the repository variable `PUBLISH_TO_PYPI` is `true` and the workflow is registered as a trusted publisher.
