---
name: stage-1-core-contract
overview: "Implement Stage 1 of the framework refactor: core schemas + CLI + entry-point-based plugin discovery + local database (SQLite) + authentication, grounded in the legacy local repo at `/Users/alisaberi/Desktop/Projects/slumber` but generalized for the new framework repo with local-first architecture."
todos:
  - id: define-core-schemas
    content: "Create Pydantic v2 schemas for `Study`, `Condition` (with multiple study-specific procedures like pre_sleep/awakening/post_sleep/wbtb), `Procedure/TaskSpec`, and `DAG` (components/connections/process groups) under `src/slumber/schemas/` based on legacy shapes but UI-agnostic + plugin-keyed. Note: procedures are study-specific (defined within each condition), not reusable across studies."
    status: in_progress
  - id: implement-database-layer
    content: Implement SQLModel-based database schema (Study, Condition, Participant, Session, User tables) with SQLite as default, dual-mode config loading (file-based YAML/JSON OR database-backed), Alembic migrations, and database initialization CLI commands.
    status: pending
  - id: implement-auth-layer
    content: "Implement local authentication system: user/participant identity management, session-based auth, password hashing (bcrypt/argon2), local credentials storage, CLI commands (`slumber auth login`, `slumber auth create-user`), session persistence, and **interactive auth prompts in `slumber run`** (mobile app model - if not logged in, prompts for username/password interactively)."
    status: pending
  - id: implement-plugin-registry
    content: Implement `PluginRegistry` that loads entry points for units/tasks/UI backends and provides stable lookup + error messages; define entry-point group names as part of the public contract.
    status: pending
  - id: implement-cli-validate-run-doctor-db-auth
    content: Replace placeholder `slumber:main` with a Typer-based CLI that supports `study init`, `validate`, `run`, `doctor`, `db init/migrate`, and `auth login/create-user` subcommands, including config loading (modular study directory OR database) and formatted Pydantic error output. Use Typer's type hints for argument/option parsing and Rich for help/error formatting.
    status: pending
  - id: implement-study-init
    content: Implement `slumber study init` command that creates a modular study directory structure with template files (study.yaml manifest + conditions/ subdirectory + example condition file).
    status: pending
  - id: implement-run-lifecycle-tracking
    content: "Implement Run lifecycle management: create Run records with authenticated participant context, track stop/interrupt events, support restart with `parent_run_id` relationships, and update Run status/end_time appropriately."
    status: pending
  - id: headless-ui-and-minimal-example
    content: Ship a minimal built-in `headless` UI backend + at least one minimal task type so `slumber run` works end-to-end; add `examples/minimal_study/` directory structure and wire it into docs.
    status: pending
  - id: tests-for-stage-1-contract
    content: Add focused tests for schema validation, plugin lookup, DAG connection validation, database operations, auth flows, and run lifecycle tracking to lock in the Stage 1 contract.
    status: pending
isProject: false
---

# Stage 1 — Core contract (schemas + CLI + plugin system + database + auth)

## Outcome (definition of done)

- `slumber db init` creates a local SQLite database in user data directory (e.g., `~/.slumber/slumber.db`) with all tables.
- `slumber auth create-user <username>` creates a local user account with hashed password storage.
- `slumber auth login <username>` authenticates and establishes a session for participant UI.
- `slumber study init <study-id>` creates a new study directory structure with template files (modular config: `study.yaml` manifest + `conditions/` subdirectory).
- `slumber validate <study-dir>` OR `slumber validate --from-db <study-id>` loads config (file-based study directory OR database-backed) and performs **strict Pydantic validation** with actionable, path-specific errors.
- `slumber run <study-dir>` OR `slumber run --from-db <study-id>` OR `slumber run --session-id <session-id>` can:
  - **requires authentication** (participant must be logged in via `slumber auth login`)
  - resolve plugins (units/tasks/UI backend) via **Python entry points**
  - build an `ezmsg` DAG from the config and start it
  - invoke a selected **UI backend** via a stable interface (initially ship a minimal built-in `headless` backend so the command is usable before Stage 2)
  - associate runs with authenticated participant user
  - track run state transitions (started → stopped/interrupted → restarted) with parent_run relationships
- `slumber doctor` checks environment + optional extras and reports what’s missing.
- A minimal example study config exists (modular directory structure and database-backed) and is documented.

## What we’re porting/generalizing from legacy (local)

From `/Users/alisaberi/Desktop/Projects/slumber`:

- **DAG schema**: `slumber/models/dag.py` (`DAG`, `ComponentConfig`, `connections`, `process_components`), but replace direct module scanning (`slumber.dag.units`) with a plugin registry.
- **Procedure/task schema**: `slumber/models/gui.py` (`Procedure`, `Task(title, widget, kwargs)`), but replace Qt widget resolution with **UI-agnostic task specs** plus per-UI renderers.
- **Condition config shape**: `configs/conditions/condition_*.yaml` where `gui` contains **multiple procedures** (pre_sleep, awakening, post_sleep, wbtb) + `dag` are nested under a named config. **Procedures are study-specific** (defined within each condition, not reusable across studies). Stage 1 will keep this modular approach: a study is a **directory** containing a `study.yaml` manifest plus a `conditions/` subdirectory with individual condition files.

## Proposed new core module layout (in this repo)

- Schemas (Pydantic models for validation + serialization):
  - `src/slumber/schemas/study.py`: `Study`, `Participant`, `SessionPlan` (or similar), `RunLayout`, `SelectedUI`
  - `src/slumber/schemas/condition.py`: `Condition` (multiple procedures + DAG), condition assignment hooks
  - `src/slumber/schemas/procedure.py`: `Procedure`, `TaskSpec(type, title, kwargs)`
  - `src/slumber/schemas/dag.py`: `DAG`, `ComponentSpec(name, unit_type, settings)`, `ConnectionSpec`
- Database layer (SQLModel tables + migrations):
  - `src/slumber/db/models.py`: SQLModel table definitions (`Study`, `Condition`, `Participant`, `Session`, `User`, `Run`)
  - `src/slumber/db/session.py`: database session management, connection factory (SQLite by default, configurable via env)
  - `src/slumber/db/migrations/`: Alembic migration scripts
  - `src/slumber/db/init.py`: database initialization, table creation
- Authentication (required for participant UI - mobile app model):
  - `src/slumber/auth/models.py`: `User`, `AuthSession` (authentication sessions, distinct from study Sessions), password hashing utilities
  - `src/slumber/auth/manager.py`: `AuthManager` for login/logout, user creation, session validation, current user context, interactive login prompt
  - `src/slumber/auth/middleware.py`: middleware for CLI/UI to check auth and prompt interactively if not authenticated
  - `src/slumber/auth/context.py`: thread-local/context manager for current authenticated user (used by Run creation)
  - `src/slumber/auth/session_storage.py`: persist auth sessions across CLI invocations (local file or database)
- Config loading + error formatting (dual-mode: file OR database):
  - `src/slumber/config/load.py`: load study directory (manifest + conditions) OR load from database by ID; normalize paths relative to the study directory.
  - `src/slumber/config/study_loader.py`: load modular study structure (study.yaml + conditions/*.yaml) and merge into unified Study model.
  - `src/slumber/config/errors.py`: pretty-print Pydantic validation errors (field path, message, input snippet when possible).
  - `src/slumber/config/storage.py`: save/load study configs to/from database (convert Pydantic models ↔ SQLModel tables)
- Study initialization:
  - `src/slumber/study/init.py`: `StudyInitializer` that creates study directory structure with templates
  - `src/slumber/study/templates.py`: template files for `study.yaml`, `conditions/*.yaml`, `participants.yaml`
- Plugin system:
  - `src/slumber/plugins/registry.py`: `PluginRegistry` that loads entry points and offers `get_unit()`, `get_task()`, `get_ui_backend()`.
  - `src/slumber/plugins/types.py`: lightweight protocols/types for Unit factory, Task spec metadata, UI backend interface.
- CLI (using Typer):
  - `src/slumber/cli/main.py`: Typer app instance + main entry point
  - `src/slumber/cli/commands/{study,validate,run,doctor,db,auth}.py`: Typer command functions with type hints
  - Update `pyproject.toml` `[project.scripts]` to point `slumber` at `slumber.cli.main:app` (Typer's CLI app)
- Orchestration:
  - `src/slumber/runtime/orchestrator.py`: create run directory, write metadata, start DAG + UI backend, create Run records with authenticated participant context.
  - `src/slumber/runtime/run_manager.py`: Run lifecycle management (create, stop, restart tracking, parent_run relationships).
  - `src/slumber/runtime/run_directory.py`: deterministic run layout (e.g., `runs/<study>/<participant>/<run-id>/`).

## Dependency additions (Stage 1 only)

- Core runtime deps in `pyproject.toml`:
  - `pydantic` (schemas)
  - `pyyaml` (YAML loading)
  - `ezmsg` (DAG execution backbone)
  - `sqlmodel` (database ORM, combines SQLAlchemy + Pydantic)
  - `alembic` (database migrations)
  - `bcrypt` or `argon2-cffi` (password hashing for auth)
  - `typer` (CLI framework with type hints)
- Optional (nice-to-have) deps:
  - `rich` (better CLI error output; Typer uses Rich by default for help/errors)

## Plugin contract (entry points)

Define entry-point groups (names are part of the public contract):

- `slumber.units`: maps a string key (e.g., `"ZMaxDataReceiver"`) to an `ezmsg.core.Unit` subclass or a factory.
- `slumber.tasks`: maps a string key (e.g., `"instruction"`, `"survey"`) to a TaskSpec definition (UI-agnostic) plus optional validation of `kwargs`.
- `slumber.ui_backends`: maps a string key (e.g., `"headless"`, later `"nicegui"`) to a UI backend implementation.

In Stage 1, ship **built-in** (core) plugins for:

- `ui_backends.headless`: runs the procedure by printing task titles and writing placeholder outputs (so `slumber run` is end-to-end without Stage 2).
- `tasks.noop` (or `tasks.instruction` as a minimal stub): validates kwargs and is renderable by `headless`.

## Study config contract (Stage 1)

A `Study` is a **modular directory structure** (not a single file) that can be loaded from **filesystem** OR from **database** (researcher choice). The CLI supports both modes.

### File-based study structure (modular)

A study directory contains:

```
my-study/
  study.yaml          # Study manifest (metadata, participants, UI selection)
  conditions/
    condition_1.yaml  # Condition definition (multiple procedures + DAG)
    condition_2.yaml
    ...
  participants.yaml   # Optional: participant list + assignments
```

- `**study.yaml**` (study manifest) includes:
  - `study_id`: unique identifier
  - `name`, `description`: human-readable metadata
  - `conditions`: list of condition names (files in `conditions/` subdirectory)
  - `ui`: selected UI backend key + UI-specific config
  - `runs`: base output directory + layout options
  - `participants`: list with IDs and condition assignment strategy (or reference to `participants.yaml`)
- `**conditions/*.yaml**` (individual condition files):
  - Each file defines one condition with **multiple procedures** + `dag` sections
  - Condition name matches filename (e.g., `condition_1.yaml` → condition name `condition_1`)
  - **Procedures are study-specific** (defined within each condition, not reusable across studies)
  - Structure: `gui` section contains multiple procedures (e.g., `pre_sleep`, `awakening`, `post_sleep`, `wbtb`), each with its own `tasks` list
  - Rename `gui` → `procedures` (keeping multiple procedure structure) and `widget` → `type` (UI-agnostic):
    - Legacy: `gui.pre_sleep.tasks[].widget`, `gui.awakening.tasks[].widget`, etc.
    - New: `procedures.pre_sleep.tasks[].type`, `procedures.awakening.tasks[].type`, etc.
  - Example structure:
    ```yaml
    name: condition_1
    procedures:
      pre_sleep:
        tasks: [...]
      awakening:
        tasks: [...]
      post_sleep:
        tasks: [...]
      wbtb:  # optional
        tasks: [...]
    dag:
      components: [...]
      connections: [...]
    ```

### Database-backed study

Stores the same structure in SQLModel tables:

- `Study` table: top-level study metadata
- `Condition` table: linked conditions with multiple procedures
  - `id`, `study_id` (FK), `name`, `procedures` (JSONB - contains multiple procedures like pre_sleep, awakening, post_sleep, wbtb), `dag` (JSONB or normalized)
  - **Procedures are study-specific** - each condition defines its own procedures, not shared/reusable
- `Participant` table: participant records linked to study
  - `id`, `study_id` (FK), `participant_id` (unique string within study), `user_id` (FK to User, required - participant must have account for mobile app auth)
- `Session` table: study session instances (can be scheduled OR ad-hoc)
  - `id`, `participant_id` (FK), `condition_id` (FK), `scheduled_date` (nullable - ad-hoc sessions don't have scheduled date), `scheduled_time` (nullable), `status` (scheduled/active/completed/cancelled)
  - Note: Sessions can be **scheduled** (researcher plans ahead) OR **ad-hoc** (participant starts immediately). Both are valid.
- `Run` table: actual execution instances (tracks each start/stop cycle)
  - `id`, `session_id` (FK, nullable if run is completely ad-hoc without a session), `participant_id` (FK, required - tracks who ran it), `condition_id` (FK, required), `parent_run_id` (FK, nullable - links to previous Run if this is a restart)
  - `run_directory`, `start_time`, `end_time` (nullable if still running), `status` (running/completed/failed/interrupted/stopped)
  - `metadata` (JSONB): additional run context (why stopped, restart reason, etc.)

**Terminology clarification** (mobile app model):

- **Session**: A study session instance (scheduled OR ad-hoc). Represents "Participant P001 doing Condition C1" - can be planned ahead or started immediately.
- **Run**: An actual execution attempt. When a participant starts a session, a Run is created. If they stop and restart, a new Run is created with `parent_run_id` pointing to the stopped Run.
- **Run lifecycle**: 
  - Participant starts → Run created with status `running`
  - Participant stops/interrupts → Run status → `stopped` or `interrupted`, `end_time` set
  - Participant restarts → New Run created with `parent_run_id` pointing to stopped Run, status `running`
  - This allows tracking: "Run #3 is a restart of Run #2, which was stopped after 30 minutes"

Keep the legacy “condition contains gui + dag” concept, but rename `gui` → `procedure` and `widget` → `type` (UI-agnostic):

- Legacy: `gui.pre_sleep.tasks[].widget`
- New: `procedure.pre_sleep.tasks[].type`

**Dual-mode loading**: `slumber validate/run` accepts:

- `slumber validate <study-dir>` (file-based study directory)
- `slumber validate --from-db <study-id>` (database-backed)
- `slumber run <study-dir>` (file-based study directory, prompts for auth if not logged in)
- `slumber run --from-db <study-id>` (database-backed, prompts for auth if not logged in)
- `slumber run --session-id <session-id>` (run a specific session from database, prompts for auth if not logged in)
- `slumber run --restart-run-id <run-id>` (restart a stopped/interrupted run, prompts for auth if not logged in)

**Mobile app authentication model**:

- Participant UI (`slumber run`) **requires authentication** - if user not logged in, command prompts interactively for username/password
- Researcher CLI commands (`slumber validate`, `slumber study init`, `slumber db init`) may not require auth (TBD)
- When a Run is stopped/interrupted, participant can restart it later - creates new Run with `parent_run_id` link

## CLI behavior details

- `slumber db init`
  - creates local SQLite database at `~/.slumber/slumber.db` (or configurable via env `SLUMBER_DB_PATH`)
  - runs initial Alembic migration to create all tables
  - prints success message with database path
- `slumber db migrate`
  - runs pending Alembic migrations
  - prints migration status
- `slumber auth create-user <username>`
  - prompts for password (or accepts `--password` flag for non-interactive)
  - hashes password using bcrypt/argon2
  - creates `User` record in database
  - prints user ID
- `slumber auth login [<username>]`
  - if username provided: prompts for password
  - if username not provided: prompts interactively for both username and password
  - validates credentials
  - creates `AuthSession` record in database (or local session file for CLI)
  - stores session token/ID for subsequent commands
  - session persists across CLI invocations
- `slumber run` (any variant)
  - checks for existing auth session
  - if not authenticated: prompts interactively for username/password (same as `slumber auth login`)
  - proceeds with run after authentication
- `slumber study init <study-id> [--name <name>]`
  - creates a new study directory `<study-id>/` in current directory (or `--output-dir`)
  - creates `study.yaml` manifest template
  - creates `conditions/` subdirectory
  - creates example `conditions/condition_1.yaml` template
  - optionally creates `participants.yaml` template
  - prints instructions for next steps
- `slumber validate <study-dir>` OR `slumber validate --from-db <study-id>`
  - loads config (from file OR database)
  - resolves plugins (so unknown `unit_type` / `task type` / `ui backend` fails early)
  - prints a compact error report with the exact config path (`conditions.X.dag.components[3].settings...`)
- `slumber run <study-dir>` OR `slumber run --from-db <study-id>` OR `slumber run --session-id <session-id>` OR `slumber run --restart-run-id <run-id>`
  - **checks for authentication** - if user not logged in, prompts interactively for username/password (mobile app model)
  - if `--session-id`: loads session from database, determines participant + condition
  - if `--restart-run-id`: loads stopped/interrupted Run, creates new Run with `parent_run_id` pointing to it
  - creates run directory
  - writes `study_resolved.json` (fully resolved config with plugin keys + normalized paths)
  - creates `Run` record in database (if database mode) linking to authenticated `participant_id` and `condition_id`
  - if restarting: sets `parent_run_id` to the stopped Run
  - starts DAG via `ezmsg.run(...)` using resolved unit classes
  - starts UI backend using the stable UI interface
  - UI backend can signal stop/interrupt → updates Run status to `stopped`/`interrupted`, sets `end_time`
- `slumber doctor`
  - prints Python version, platform
  - checks database connectivity (if database exists)
  - checks for optional extras (e.g., NiceGUI) without importing them eagerly

## Database schema (SQLModel tables)

Port from legacy but generalize:

- `User`: user accounts (researchers/participants)
  - `id`, `username`, `email` (optional), `password_hash`, `created_at`, `is_active`
- `Study`: top-level study definitions
  - `id`, `study_id` (unique string), `name`, `description`, `created_at`, `created_by` (FK to User)
- `Condition`: study conditions (multiple procedures + DAG)
  - `id`, `study_id` (FK), `name`, `procedures` (JSONB - contains multiple study-specific procedures like pre_sleep, awakening, post_sleep, wbtb), `dag` (JSONB or normalized)
  - **Procedures are study-specific** - defined within each condition, not reusable across studies
- `Participant`: participant records
  - `id`, `study_id` (FK), `participant_id` (unique string within study), `user_id` (FK, nullable if participant doesn't have account), `assigned_condition_id` (FK, nullable)
- `Session`: scheduled/planned study sessions (one participant + one condition + scheduled date/time)
  - `id`, `participant_id` (FK), `condition_id` (FK), `scheduled_date`, `scheduled_time` (optional), `status` (scheduled/active/completed/cancelled)
  - Note: A Session is a **plan**, not an execution. Multiple Runs can belong to one Session.
- `Run`: actual execution instances (one Run = one actual execution of a Session)
  - `id`, `session_id` (FK, nullable if run is ad-hoc without a scheduled session), `run_directory`, `start_time`, `end_time`, `status` (running/completed/failed/interrupted), `metadata` (JSONB)
  - A Session can have zero or more Runs (e.g., if a session is re-run, interrupted and restarted, etc.)

**Local-first design**: SQLite database lives in user data directory (`~/.slumber/slumber.db`). No remote database required for Stage 1. Remote sync/auth will be Stage 3+.

## Tests to add in this repo

- `tests/test_config_validation.py`
  - validates a minimal example study config (both file-based and database-backed)
  - asserts missing plugin keys and schema errors are reported cleanly
- `tests/test_database.py`
  - database initialization creates all tables
  - can save/load study configs to/from database
  - migrations run successfully
- `tests/test_auth.py`
  - user creation hashes passwords correctly
  - login validates credentials
  - auth session management works
  - session persistence across CLI invocations
  - current user context is available after login
- `tests/test_run_auth_prompt.py`
  - `slumber run` prompts for auth if not logged in (interactive prompt)
  - `slumber run` uses existing session if already authenticated
  - auth prompt can be bypassed with explicit `--username`/`--password` flags (non-interactive mode)
- `tests/test_run_lifecycle.py`
  - Run creation associates with authenticated participant
  - Run stop/interrupt updates status correctly
  - Run restart creates new Run with `parent_run_id` link
  - Can query run history (all runs for a participant, restart chains)
- `tests/test_plugins.py`
  - plugin registry loads built-in entry points
  - unknown plugin key raises a clear exception
- `tests/test_dag_schema.py`
  - ensures DAG connections reference existing components/streams (ported conceptually from legacy `DAG.validate_connections`)

## Docs/example deliverables

- Add `examples/minimal_study/` directory structure (study.yaml + conditions/) that passes `slumber validate`.
- Add database initialization example: `examples/setup_database.md` showing `slumber db init` and `slumber auth create-user`.
- Expand docs minimally:
  - `docs/getting-started/installation-setup.md`: include database setup, auth, validate/run commands for the minimal example (both file-based and database-backed modes).
  - `docs/user-guide/index.md`: define “Study / Condition / Task / DAG” terms, explain file-based vs database-backed configs, and point at the example.
  - `docs/developer-guide/index.md`: document database schema, auth flow, and dual-mode config loading.

