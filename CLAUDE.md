# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SLUMBER (Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings) is a Python framework for conducting home-based sleep studies. It provides a YAML-driven configuration system, a plugin architecture for extensibility, and a Supabase backend for multi-participant study management.

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

# Database migrations
uv run slumber db upgrade            # apply migrations
uv run slumber db revision -m "description"  # create migration

# Docs
uv run mkdocs serve
```

## Architecture

### Layers

**CLI** (`src/slumber/cli/`) — Typer app: `auth`, `study`, `condition`, `db`, `participant`, `session`, `doctor`. Commands that need Supabase call :func:`slumber.supabase.utils.exit_unless_supabase_extra_installed` before lazy imports. Entry point is `slumber:main`.

**Schemas** (`src/slumber/schemas/`) — Pydantic v2 models that define the study contract:
- `StudyManifest` — top-level `study.yaml` (metadata, dirs, UI config, run layout, logging)
- `ConditionSchema` — per-condition YAML (procedures dict + DAG definition)
- `ProcedureSchema` — ordered steps with task references
- `DAGSchema` — data acquisition graph (ezmsg components + connections)

**Config** (`src/slumber/config/`) — Loads and discovers study folders, resolves condition YAMLs, validates via schemas.

**Plugin Registry** (`src/slumber/plugins/registry.py`) — Discovers plugins via Python entry points (`slumber.tasks`, `slumber.units`, `slumber.ui_backends`). Built-in plugins: `instruction` task, `headless` UI backend.

**Supabase stack** (`src/slumber/supabase/`, optional extra `slumber[supabase]`) — Auth client (`supabase/auth/`), REST/table helpers (`supabase/backend/`), SQLModel tables (`supabase/models.py`), shared helpers (`supabase/utils.py`, e.g. ``DATABASE_URL``). Migrations live in `migrations/versions/`.

### Plugin System

Third-party packages register plugins via `pyproject.toml` entry points:
```toml
[project.entry-points."slumber.tasks"]
my_task = "my_package.tasks:MyTask"
```
Task classes subclass `src/slumber/plugins/tasks/base.py`. UI backends subclass `src/slumber/plugins/ui/base.py` (`UIBackend`).

### Study Folder Structure

A study lives in a directory with:
```
study.yaml          # StudyManifest
conditions/         # one YAML per condition (ConditionSchema)
assets/             # static files for participants
runs/               # output data, one subfolder per run
```

### Environment Variables

Required in `.env` (see `.env.example`):
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — public API access
- `SUPABASE_SERVICE_ROLE_KEY` — admin operations (participant/session CLI commands)
- `DATABASE_URL` — PostgreSQL URI for Alembic migrations

## Key Conventions

- Pydantic v2 schemas are the source of truth for config validation; extend them when adding new config fields.
- All CLI commands that touch the backend require an authenticated Supabase session (`slumber auth login`).
- Row-Level Security (RLS) is enforced on all Supabase tables; service role key bypasses RLS for admin CLI commands.
- Session windows use a PostgreSQL exclusion constraint to prevent overlap — enforce this in any new session-related code.
- `ezmsg` is used as the data acquisition backbone; DAG components in conditions map to ezmsg `Unit` subclasses registered under `slumber.units`.

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

### Comments & TODOs

- Write **only necessary comments** (non-obvious rationale, trade-offs, constraints).
- Use `TODO:` for follow-ups; do not use `FIXME`/`XXX`.

### Logging

- Use **loguru** for all logging (`from loguru import logger`). Never use stdlib `logging` in new code.
- CLI commands expose a `-v`/`--verbose` flag for increased verbosity.
- **Run** (study run / participant app): configure logging from study settings via `runs.logging` — a **handlers** list of dicts, each passed as kwargs to loguru `logger.add()` (sink, level, format, rotation, retention, compression, etc.); support placeholders in sink paths (e.g. `run_id`).

### Utilities Placement

- Cross-cutting helpers go in `src/slumber/utils/` (used broadly across the codebase).
- If a helper is only used within a specific subsystem, **co-locate** it there (e.g. `src/slumber/<submodule>/utils.py`).
- Avoid "misc" util dumping; utilities should have a clear, stable purpose.

### Test Layout & DRY

- **Test layout mirrors the package**: `tests/config/` → `slumber.config`, `tests/cli/` → `slumber.cli`, etc. Only use top-level `tests/` for cross-cutting smoke/integration tests.
- Do not duplicate logic; **extract shared code** into reusable helpers/modules when it improves clarity.
- In tests, avoid copy/paste setup: prefer **shared fixtures** (`tests/conftest.py`) and parametrization.
- Keep fixtures focused and composable; don't build overly generic "god fixtures".

## Legacy Reference

This repository (`slumber-org/slumber`) is the **new canonical framework**. The original SLUMBER codebase was built for a specific LD (lucid dreaming) induction study and contains a mature end-to-end implementation (devices, `ezmsg` DAG wiring, and a participant-facing GUI). We keep it as a **reference and migration source**, but **do not treat it as the framework baseline**.

- Remote: `https://github.com/alitsaberi/slumber`
- Local: `/Users/alisaberi/Desktop/Projects/slumber`
- Notable legacy characteristics: Qt/PySide6 UI, YAML configs coupling GUI procedures + DAG components, `ezmsg` processing backbone.

### CRITICAL: Before refactoring or implementing any feature

1. **Check the legacy codebase** at `/Users/alisaberi/Desktop/Projects/slumber` for existing implementations.
2. **Search for related functionality** to understand what features exist, how they're implemented, what edge cases matter, and what patterns should be preserved.
3. **Compare implementations** to ensure feature parity and that important aspects aren't lost.
4. **Reference legacy code** when defining APIs, schemas, or interfaces to ensure compatibility.

Key legacy locations:
- DAG schema: `slumber/models/dag.py`
- Procedure/Task schema: `slumber/models/gui.py`
- Condition load/sync: `slumber/models/condition.py`, `slumber/scripts/update_conditions.py`

### What should (and should not) be ported

- **Port into core** (only if broadly useful): config schemas, plugin interfaces, logging/audit, orchestration primitives.
- **Port as extensions** (`slumber.ext.*`): device integrations (ZMax, Polar), processing pipelines, participant UI (NiceGUI preferred over legacy Qt).
- **Keep legacy-only**: study-specific copy, instructions, surveys, and tuning parameters that are not generally applicable.
