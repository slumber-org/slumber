# AGENTS.md

Guidance for AI agents and collaborators working in this repository.

## Project Overview

SLUMBER (Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings) is a Python framework for conducting home-based sleep studies. It provides a YAML-driven configuration system, a plugin architecture for extensibility, and optional extensions (e.g. Supabase) for multi-participant study management.

## Commands

```bash
# Install dependencies (full test suite needs optional extras — same as CI)
uv sync --all-extras --dev

# Run the CLI
uv run slumber --help

# Lint and format
uv run ruff check .
uv run ruff format .
uv run ruff check --fix .

# Tests (after `uv sync --all-extras --dev`; core-only install may miss imports)
uv run pytest
uv run pytest -v
uv run pytest tests/test_smoke.py          # specific file
uv run pytest -k test_name                  # filter by name

# Database migrations (Supabase extension; not required for local study run)
uv run slumber db upgrade            # apply migrations
uv run slumber db revision -m "description"  # create migration

# Docs
uv run mkdocs serve
```

Update this section when the CLI surface changes (0.1 core: `study` / `doctor`; extensions attach via `slumber.cli`).

## Architecture

**Target architecture and terms** live in [`docs/design/0.1-base.md`](docs/design/0.1-base.md). Prefer that document when implementing or refactoring. The current tree may lag; names like tasks, procedures, and DAG are migration leftovers.

### Target (0.1) module map

```
slumber/
  schemas/     # Pydantic models only (no registry imports)
  config/      # load_study, validate plugins, resolve PluginSpec
  plugins/     # discovery only (registry, ConfiguredPlugin)
  run/         # RunEngine, run directory, run logging
  pipeline/    # pipeline manager + core units
  ui/          # AppFrame, gui/headless, layouts, activities, theme
  cli/         # core commands; loads extra Typer apps from slumber.cli

extensions/    # e.g. slumber-supabase, slumber-audio, slumber-somnio
examples/demo/
tests/         # mirrors src/slumber/
```

Study package on disk: `study.yaml`, `conditions/`, `assets/`, `runs/`.

Key 0.1 terms: Study, Condition, Phase, Activity, Layout, UI (`gui` / `headless`), Pipeline, Unit, RunEngine, Plugin (`type` + `settings`). Details, YAML shapes, and contracts are in the design doc — do not duplicate them here.

### Current tree (until reorg)

The installed package still has as-built layout and CLI (including in-tree Supabase helpers and older entry-point names such as `slumber.tasks`). Treat that as transitional; do not extend it contrary to `0.1-base.md`.

## Key Conventions

- Prefer the 0.1 design when adding or reshaping APIs: schemas validate shape only; plugins are discovery-only; `PluginSpec` is `type` + `settings`.
- Local study run must work without Supabase. Backend/auth/session features belong in an extension (`extensions/slumber-supabase`), not core.
- When touching existing Supabase code: authenticated session for backend CLI; RLS on tables; service role for admin; session windows must not overlap (exclusion constraint).
- `ezmsg` remains the processing backbone; pipeline units are ezmsg `Unit` subclasses registered under `slumber.units`.
- Path placeholders (`{assets_dir}`, `{run_dir}`, `{run_id}`, …) and relative→study-root resolution follow the design doc.

## Python Style

### Structure & Boundaries

- Keep **modules, classes, and functions small** and single-purpose; split when responsibilities diverge.
- Prefer a **clear module hierarchy** under `src/slumber/` (domain-first), not "mega" modules.
- Avoid deep import spaghetti; introduce intermediate modules or interfaces when needed.
- Keep I/O at the edges; keep core logic pure/testable when practical.
- Prefer explicit errors and validated inputs over silent fallbacks.

### Naming

- Use **complete, meaningful names**; avoid unclear abbreviations.
- **Constants**: `UPPER_SNAKE_CASE`
- **Module-private**: leading underscore (e.g. `_parse_header`)
- **Instance-private**: `self._field` (do not expose implicitly)
- Prefer verbs for functions (`load_records`) and nouns for types (`RecordLoader`).

### APIs, Typing, and Docstrings

- Use **type hints** for public functions/classes and non-trivial internals.
- Use **Google-style docstrings** (enforced by ruff pydocstyle `convention = "google"`).
- Docstrings should explain **intent/contract** (Args/Returns/Raises), not restate obvious code.

### String Formatting

- Prefer **f-strings** for interpolated strings (`f"run {run_id}"`).
- Avoid `%` formatting and `.format()` when an f-string is clearer.
- Exception: keep `.format()` for **template substitution** (e.g. user-configured layout strings with named placeholders).

```python
# Prefer
typer.echo(f"Synced {count} condition(s) for study {study_id!r}.")

# Avoid
typer.echo("Synced {} condition(s) for study {!r}.".format(count, study_id))
logger.info("Run %s failed", run_id)

# OK — external template, not inline interpolation
path = layout.format(**context)
```

### Comments & TODOs

- Write **only necessary comments** (non-obvious rationale, trade-offs, constraints).
- Use **`TODO:`** for follow-ups; do not use `FIXME`/`XXX`.

### Logging

- Use **loguru** for all logging (`from loguru import logger`). Never use stdlib `logging` in new code.
- CLI commands expose a `-v`/`--verbose` flag for increased verbosity.
- **Run** (study run / participant app): configure logging from study settings (0.1: `study.logging`) — a **handlers** list of dicts, each passed as kwargs to loguru `logger.add()`; support placeholders in sink paths (e.g. `run_id`).

### Utilities Placement

- Cross-cutting helpers go in `src/slumber/utils/` (used broadly across the codebase).
- If a helper is only used within a specific subsystem, **co-locate** it there (e.g. `src/slumber/<submodule>/utils.py` or `src/slumber/<submodule>/utils/`).
- Avoid "misc" util dumping; utilities should have a clear, stable purpose.

### Test Layout & DRY

- **Test layout mirrors the package**: `tests/config/` → `slumber.config`, `tests/cli/` → `slumber.cli`, `tests/schemas/` → `slumber.schemas`, `tests/plugins/` → `slumber.plugins`. Place tests for a given package in the matching `tests/<package>/` directory.
- Use **top-level** `tests/` only for cross-cutting smoke or integration tests (e.g. `tests/test_smoke.py`).
- Do not duplicate logic; **extract shared code** into reusable helpers/modules when it improves clarity.
- In tests, avoid copy/paste setup: prefer **shared fixtures** (`tests/conftest.py`) and parametrization.
- Keep fixtures focused and composable; don't build overly generic "god fixtures".

## Legacy Reference

This repository (`slumber-org/slumber`) is the **new canonical framework**. The original SLUMBER codebase was built for a specific LD (lucid dreaming) induction study and contains a mature end-to-end implementation (devices, `ezmsg` DAG wiring, and a participant-facing GUI). We keep it as a **reference and migration source**, but **do not treat it as the framework baseline**.

- Remote: [`https://github.com/alitsaberi/slumber`](https://github.com/alitsaberi/slumber)
- Notable characteristics: Qt/PySide6 UI, YAML configs coupling GUI procedures + DAG components, `ezmsg` processing backbone.

### CRITICAL: Before refactoring or implementing any feature

1. **Check the legacy repo** on GitHub for existing implementations.
2. **Search for related functionality** to understand what features exist, how they're implemented, what edge cases matter, and what patterns should be preserved.
3. **Compare implementations** to ensure feature parity and that important aspects aren't lost.
4. **Align new work with** [`docs/design/0.1-base.md`](docs/design/0.1-base.md) (phases, activities, pipelines) rather than copying legacy procedure/task/DAG shapes into core.

## Agent Skills

Task-specific workflows live in [`.agents/skills/`](.agents/skills/). Read and follow the relevant `SKILL.md` when a task matches a skill description.
