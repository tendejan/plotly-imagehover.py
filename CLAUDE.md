# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository

This is `plotly.py`, the open-source Python graphing library built on top of `plotly.js`. This particular checkout is a personal fork (`tendejan/plotly-imagehover.py`) tracking upstream `plotly/plotly.py` on `main`.

## Setup

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync --extra dev          # full dev environment
# or: pip install -e '.[dev]'
```

If testing changes in Jupyter Lab/Notebook, also run `jupyter labextension develop .` after `pip install jupyter`.

## Common commands

```bash
# Run all tests
python -m pytest tests

# Run a single test file
python -m pytest tests/test_core/test_graph_objs/test_figure.py

# Lint / format (ruff, pinned version in pyproject.toml)
ruff check .
python commands.py lint
python commands.py format

# Regenerate graph_objs from the plotly.js schema (after editing codegen/)
python commands.py codegen [--noformat]

# Update the bundled plotly.js version (schema + JS bundle + codegen)
python commands.py updateplotlyjs          # set SKIP_NPM=1 to skip the npm build step
python commands.py updateplotlyjsdev --devrepo <repo> --devbranch <branch>   # or --local <path>

# Bump plotly.py's own version across all files
python commands.py bumpversion X.Y.Z
```

All `commands.py` subcommands are documented in `CONTRIBUTING.md`.

### JS/Jupyter widget build

Only needed when touching `js/`:

```bash
cd js/
npm ci
npm run build
```

This rebuilds the JupyterLab mime-renderer extension and the `FigureWidget` bundle, producing artifacts under `plotly/labextension/` and `plotly/package_data/widgetbundle.js`. **These build artifacts must be committed** — CI (`check-js-build.yml`) verifies they're in sync with `js/` source.

## Architecture

### The codegen boundary is the most important thing to understand

Most of `plotly.py`'s trace/layout API (`plotly.graph_objs`, re-exported as `plotly.graph_objects`/`go`) is **generated, not hand-written**, from the `plotly.js` JSON schema:

- `codegen/resources/plot-schema.json` — the schema, pulled from a `plotly.js` release (or dev build).
- `codegen/` — the generator itself (`datatypes.py`, `figure.py`, `compatibility.py`, `validators.py`, `utils.py`). Reads the schema and writes:
  - `plotly/graph_objs/` — one file per trace/layout type (`_bar.py`, `_scatter.py`, `_layout.py`, ...), all generated.
  - `plotly/validators/` — validator classes for every attribute, generated.
- `plotly/graph_objects/__init__.py` is just a lazy re-export shim over `plotly/graph_objs/` (uses `TYPE_CHECKING` + `__getattr__`), not a place to add logic.

**Never hand-edit files under `plotly/graph_objs/` or `plotly/validators/`.** Any change to trace/layout attributes must go through `plotly.js` upstream or through the `codegen/` generator, then be produced via `python commands.py codegen`.

Hand-written, non-generated logic that applies across all figure types lives in `plotly/basedatatypes.py` (`BaseFigure`, `BaseTraceType`, etc. — `add_trace`, `update_layout`, `for_each_trace`, and friends). This is the file to touch for cross-cutting `Figure`/trace behavior.

### Package layout

- `plotly/express/` (`px`) — high-level declarative API built on top of `graph_objects`. Concerns itself with reshaping input data (via `narwhals`, a pandas/polars-agnostic layer) and building `go.Figure`s; avoids doing visualization logic itself. `_core.py` has the main figure-building machinery; `_chart_types.py` defines the public `px.bar`, `px.scatter`, etc.
- `plotly/io/` (`pio`) — low-level display/read/write: renderers (`_renderers.py`, `_base_renderers.py`), static image export via Kaleido (`_kaleido.py`) or legacy Orca (`_orca.py`), JSON/HTML serialization, templates.
- `plotly/subplots.py` / `plotly/_subplots.py` — `make_subplots` and multi-plot layout helpers.
- `plotly/figure_factory/` — legacy "figure factory" chart builders (dendrograms, ternary contours, etc.), largely superseded by `express` but still maintained.
- `plotly/matplotlylib/` — converts matplotlib figures to plotly.
- `_plotly_utils/` — a separate top-level package for utilities shared between codegen-time and runtime code (`basevalidators.py`, `colors/`, `data_utils.py`). Per convention in `codegen/__init__.py`, `codegen/` must never import from `plotly/` — only from `_plotly_utils/` — to keep code generation decoupled from the runtime package.
- `templategen/` — generates the built-in plotly themes/templates (`plotly_white`, `plotly_dark`, etc.).
- `js/` — TypeScript source for the two Jupyter integrations: the JupyterLab mime-renderer extension (`src/mimeExtension.ts`) and `FigureWidget`'s anywidget-based JS (`src/widget.ts`).

### Tests

`tests/` mirrors the package structure:
- `tests/test_core/` — fast tests with no optional dependencies, organized by subsystem (`test_graph_objs`, `test_subplots`, `test_figure_widget_backend`, `test_offline`, `test_colors`, ...).
- `tests/test_optional/` — tests requiring optional deps (`px`, `figure_factory`, Kaleido, matplotlylib, etc.).
- `tests/test_io/`, `tests/test_plotly_utils/` — self-explanatory.
- `tests/percy/` — visual regression fixtures.
- `test_init/` — sanity checks that importing `plotly` doesn't eagerly import heavy optional dependencies.

Pytest markers `nodev` and `matplotlib` are defined in `pyproject.toml`.

## Contribution conventions (from CONTRIBUTING.md)

- Work on a branch, never commit directly to `main`.
- Changes to `graph_objects` behavior go through the codegen system or upstream `plotly.js`, not hand-edits to generated files.
- Don't commit `uv.lock` changes unless `pyproject.toml` dependencies actually changed.
- Add a `CHANGELOG.md` entry for substantial changes.
- New features need docstring updates and (per the doc PR checklist in `CONTRIBUTING.md`) doc examples under `doc/python/` using `px` where possible, `df` for dataframes, and ending each example with `fig.show()`.
