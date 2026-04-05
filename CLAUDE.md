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
Task classes subclass `src/slumber/plugins/tasks/base.py`. UI backends implement the `UIBackend` protocol from `src/slumber/plugins/types.py`.

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

- Use **loguru** for all logging (`from loguru import logger`). Never use stdlib `logging` in new code.
- CLI commands expose a `-v`/`--verbose` flag for increased verbosity.
- Type hints required for all public functions/classes; use **Google-style docstrings** (enforced by ruff pydocstyle).
- Use `TODO:` for follow-ups; do not use `FIXME`/`XXX`.
- Keep modules small and single-purpose; domain-first module hierarchy under `src/slumber/`.
- Cross-cutting helpers go in `src/slumber/utils/`; subsystem-specific helpers co-locate in that subsystem.
- **Test layout mirrors the package**: `tests/config/` → `slumber.config`, `tests/cli/` → `slumber.cli`, etc. Only use top-level `tests/` for cross-cutting smoke/integration tests.

## Legacy Reference

The original SLUMBER codebase (a specific lucid dreaming study) lives at:
- Remote: `https://github.com/alitsaberi/slumber`
- Local: `/Users/alisaberi/Desktop/Projects/slumber`

**Before implementing or refactoring any feature**, check the legacy repo for existing implementations. Key legacy locations:
- DAG schema: `slumber/models/dag.py`
- Procedure/Task schema: `slumber/models/gui.py`
- Condition load/sync: `slumber/models/condition.py`, `slumber/scripts/update_conditions.py`

What to port into **core**: config schemas, plugin interfaces, logging/audit, orchestration primitives.
What to port as **extensions** (`slumber.ext.*`): device integrations (ZMax, Polar), processing pipelines, participant UI (NiceGUI preferred over legacy Qt).

## Roadmap (Stage 1 — current)

Currently on **Stage 1** (core contract). The implementation plan lives in `.cursor/plans/stage_1_implementation_plan_01557d31.plan.md`.

Completed tasks (Tasks 1–6): schemas, study init, config load/validate, plugin registry, Supabase DB schema, Supabase Auth + participant/session CRUD.

Pending tasks:
- **Task 7**: `slumber condition sync` — upsert conditions from `conditions/` into Supabase
- **Task 8**: CLI skeleton refinement, `slumber doctor`, loguru verbose flag
- **Task 9**: Run directory layout + run logging from `study.logging`
- **Task 10**: `slumber study run` (minimal, headless), optional Sentry init

Future stages: Stage 2 (NiceGUI shell), Stage 3 (ZMax, HDF5, survey widgets, packaging), Stage 4 (docs), Stage 5 (coverage gates + CI).
