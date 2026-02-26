# Framework refactor plan (core + extensions)

This page tracks the staged refactor from the legacy study codebase into a general SLUMBER framework.

## Goals and constraints

- **Target repo**: this repository (`slumber-org/slumber`) is the canonical framework.
- **Researcher-first UX**: study setup should be mostly declarative (YAML), understandable with minimal coding.
- **Core vs extensions**: **core** is the framework package (schemas, CLI, plugin registry, backend, orchestration, templates); **extensions** (Django-app style) add optional tasks, units, schemas, and dependencies (devices, processing, UI, visualization).
- **Backbone**: keep `ezmsg` as the processing backbone.
- **Participant UI**: prioritize a **Python-first UI** with good DX and feature parity with the legacy Qt UI. Recommendation: ship a **NiceGUI** participant UI extension first, while keeping the core UI-agnostic.
- **Backend**: **Supabase** as the default backend (auth, Postgres, storage, optional realtime). Researchers who prefer not to use the Supabase platform can run **Supabase locally** (CLI for dev, or self-hosted Docker for their own instance).
- **Logging**: **loguru** for application logging. **CLI and orchestration**: default level; CLIs support a **verbose** option (e.g. `-v` / `--verbose`) for increased verbosity. **Run** (when a study is running): logging is configured in **study settings** via `runs.logging`—multiple **handlers** with loguru `add()` args (sink, level, format, rotation, retention, compression, etc.).

## Researcher workflow and deployment model

The framework helps researchers **set up and run their project** and **ship an installable application** for participant laptops. Usage follows a **fork-and-customize** pattern:

1. **Base framework**: This repo (`slumber-org/slumber`) is the core framework. A researcher **forks** (or clones and customizes) to create their **own project/study repo**.
2. **Backend choice**:
   - **Supabase (cloud)**: Create a Supabase project, get URL + keys, configure in study. Easiest for most researchers; no server to run.
   - **Supabase (local)**: Researchers who don’t want to use the Supabase platform can run Supabase locally:
     - **Dev**: `supabase start` (Docker) for local development and testing.
     - **Self-hosted**: Run Supabase via Docker on their own server/lab for full control and data locality.
   - Framework treats both as “a Supabase backend”; only the endpoint and keys differ.
3. **Researcher setup (their fork)**:
   - Initialize study (configs, conditions, run layout, UI choice).
   - Configure **backend** (Supabase project URL + anon key; or local Supabase URL for dev/self-hosted).
   - Configure **conditions**, **settings**, and **components** (tasks, units, plugins) for their study.
4. **Environments (dev vs prod)**:
   - **Dev**: Point at a local Supabase instance (`supabase start`) or a dev Supabase project to test configs, dry runs, and conditions.
   - **Prod**: Point at production Supabase (cloud or self-hosted) and deploy.
5. **Participant deployment**:
   - Researchers **ship their study** as an application to be **installed on participant laptops** (packaged app or `pip` + study bundle).
   - Participant app connects to the researcher’s Supabase backend (cloud or self-hosted) for auth and syncing.
   - Participants **log in** (Supabase Auth); they **read** assigned sessions/conditions from the backend and **upload** run data. Optional local cache for offline runs, syncing when online.

This document’s staged plan below details how the core (schemas, Supabase backend, CLI, plugin system, templates) and later stages (extensions: UI, devices, sync, packaging) support this workflow.

### Backend options (Supabase)

| Option | Use case | How |
|--------|----------|-----|
| **Supabase cloud** | Most researchers; no server to run | Create project at supabase.com, add URL + anon key to `.env` or an env-specific file (e.g. `.env.prod`). |
| **Supabase local (dev)** | Develop and test without cloud | `supabase start` (Docker); use local URL and anon key in `.env.dev` (or similar). |
| **Supabase self-hosted** | Full control, data stays in lab | Run Supabase via Docker on own server; use that instance’s URL and keys. |

The framework uses the same Supabase client and schema for all three; only the endpoint and keys differ. Participant app is built once and configured at install time (or via env) with the researcher’s backend URL and anon key.

## What we have today (legacy reference)

The legacy codebase already demonstrates a useful pattern we’ll preserve:

- Study logic is largely **config-driven** (YAML)
- GUI procedures are expressed as an ordered list of **tasks** (instructions, surveys, device steps, calibrations)
- DAG pipelines are expressed as a list of **components** (units + settings) and **connections** (stream wiring)

## Target architecture (core + extensions)

- **Researcher side**: config-driven study (conditions, participants, sessions); **Supabase** as backend (cloud or local/self-hosted) for dev and prod; CLI and tooling to init, validate, and run studies.
- **Participant side**: **installed app on participant laptops**; login via **Supabase Auth**; **reads** conditions/participants/sessions from Supabase; **uploads** run data; optional local cache for offline runs with sync when online.

The framework is organized in two layers (similar in spirit to Django’s core vs apps):

### Package layout

| Layer | Package | Role |
|-------|---------|------|
| **Core** | `slumber` (`src/slumber/`) | The framework: config schemas (Study/Condition, Procedure/Task, DAG), plugin registry and discovery (entry points), CLI (study init/validate/run, doctor, auth, participants, sessions, condition sync), backend abstraction (Supabase), orchestration, default study templates, run layout/logging, optional Sentry, packaging. Everything a study needs without extensions. |
| **Extensions** | `slumber.ext.*` | Optional, self-contained feature sets (Django-app style). Each extension can introduce its own **tasks**, **units**, **schemas**, and **dependencies**. Registered via the core plugin API. |

Dependency direction: **core** ← **each extension**. Extensions depend on core; core does not depend on extensions.

### Core responsibilities (`slumber`)

- **Config schemas** (Pydantic): Study/Condition, Procedure/Task, DAG (units/connections/process_components).
- **Plugin API**: discover and register units, tasks, UIs, devices (e.g. Python entry points); stable contracts for extension authors.
- **Backend abstraction**: Supabase client (Postgres, Auth, Storage, optional Realtime); same API whether cloud or local/self-hosted; migrations (Supabase migrations or Alembic against Postgres).
- **Authentication**: Supabase Auth for users/participants; session and participant identity aligned with Supabase (e.g. custom claims or `participants` table linked to `auth.users`).
- **Orchestration**: validate/run configs; run directories; logging/audit (via **loguru**); reproducible metadata.
- **CLI**: study init, validate, run, doctor; backend, auth, participants, sessions, condition sync.
- **Default templates**: study folder layout, `study.yaml` template, conditions layout.
- **Monitoring (optional)**: **Sentry** integration for error and performance monitoring when a study is run (researcher-run and participant app); opt-in via `SENTRY_DSN` in env; context (study_id, participant_id, session_id) set where available.
- **Packaging/ship**: support for building an installable participant app (e.g. PyInstaller, or `pip` + study bundle) that connects to the researcher’s configured Supabase backend.

### Extensions (Django-app style)

Extensions (initially in-repo under `slumber.ext.*`; may later be split into separate repos) are self-contained: each can bring its own **tasks**, **units**, **schemas**, and **dependencies**. Examples:

- **`slumber.ext.devices.zmax`**: ZMax device integration — ZMax-specific tasks (e.g. connection widget), units (data receiver), schemas (device config), and optional pip dependencies.
- **`slumber.ext.devices.polar`**: Polar device (same pattern).
- **`slumber.ext.processing.*`**: pipelines (sleep scoring, detectors) — their units and schemas.
- **`slumber.ext.ui.nicegui`**: participant app shell + task library (instruction, survey, device widgets, etc.).
- **`slumber.ext.visualization.*`**: dashboards/plotting.

## Staged refactor plan

**Gradual development**: Each stage is a **complete increment**. Documentation and tests are **developed throughout** each stage—as tasks and features are implemented—not deferred to later stages. By the end of every stage we have:
- **Features** implemented and working
- **Documentation** for what was built (user-facing and/or developer-facing as appropriate), written alongside the implementation
- **Tests** covering the new behavior, written alongside the implementation
- A **usable** product at that scope (researchers can rely on it for the capabilities delivered)

Stages 4 and 5 then **unify and elevate** this per-stage work: project-wide documentation (user guide, API reference, deployment) and project-wide testing (coverage gates, CI, test pyramid completeness).

### Stage 1 — Establish the core contract (schemas + CLI + plugin system + database + auth)

- Port and generalize the legacy config models into the new repo:
  - DAG schema (components/connections)
  - Procedure/task schema (task library + kwargs)
- **Study folder structure** (one study per folder, for now):
  - A **study** is a single folder that contains the study definition and all assets. The **study id** is defined in the manifest inside that folder.
  - **Init wizard**: `slumber study init`. The wizard asks for **base dir** (default: **`.`**) and **study_id**; the study folder is then created at **`<base_dir>/<study_id>/`**. Both can be overridden by CLI args (e.g. `--base-dir`, `--study-id`) for non-interactive use.
  - **CLI workflow (inspired by [U-Time](https://github.com/perslev/U-Time))**: After init, the researcher **cd**s into the study folder and runs subsequent commands **from there**. The study is **discovered from the current directory** (e.g. look for `study.yaml` in cwd). No need to pass study-id for validate/run when inside the study folder; optionally support `--study-dir <path>` when running from elsewhere.
  - Standard layout: **.env** files live at the **project root** (parent of study folder(s), or repo root). The **study folder** contains only definition and assets:

    ```
    <project-root>/           # repo root or cwd for CLI (base_dir when running init)
      .env.example            # optional: committed template listing required vars (no secrets)
      .env                    # or .env.dev, .env.prod, etc. — gitignored
      <study_id>/             # study folder: <base_dir>/<study_id>/
        study.yaml            # study manifest (study_id, name, conditions_dir, runs, ui)
        conditions/           # condition configs (one file per condition)
        assets/               # study assets (instructions, media, etc.)
    ```

  - **Researcher secrets and multiple environments**: Secrets (e.g. Supabase URL and anon key) live in **`.env`** files at the **project root**, not inside the study folder. Support **multiple env files per environment** (e.g. `.env`, `.env.dev`, `.env.prod`). The active file is chosen by environment (e.g. `SLUMBER_ENV=dev` → load `.env.dev`; default if unset can be `.env`). All env files that may contain secrets (`.env`, `.env.*`) are **gitignored**; optionally commit **`.env.example`** at project root with variable names only (no secrets). Never commit secrets.
  - **Participant-side local data**: Local state, cache, and **run data** are for the **participant** app (on participant laptops). They are stored in the participant app’s data directory where the app is installed, not in the researcher’s study folder. The study manifest’s `runs.base_directory` and layout describe where the participant app writes runs in that context.
  - **Run outputs (researcher)**: If researchers run the UI locally for testing, run data can go in a folder at study root (e.g. `runs/`); that folder can be gitignored if desired. The main run-data flow is participant → Supabase (or upload from participant machine).
  - **Conditions**: The manifest names the conditions folder (default `conditions/`); conditions are loaded from that folder. Optionally the manifest can list condition IDs that must exist as files there.
  - **Run directory layout** and **selected UI** are defined in the study manifest. **Run layout placeholders**: one project = one study; use `participant_id`, `session_id`, `run_id` (and any others the schema supports).
  - **By example:** a minimal study is this folder with `study.yaml` and a conditions folder. The manifest describes study identity, where conditions live, where run data goes, and which UI to use:

  ```yaml
  # study.yaml (top-level study manifest — no participants/sessions here)
  study_id: ld-induction-2025
  name: Lucid dreaming induction pilot

  # Conditions: folder name (default conditions/) or list of condition IDs that must exist as files in that folder
  conditions_dir: conditions   # optional; default "conditions"

  # Run directory layout: placeholders participant_id, session_id, run_id (no study_id; one project = one study)
  runs:
    base_directory: runs
    layout: "sub-{participant_id}/ses-{session_id}/run-{run_id}"
  
  # Logging during a run: configure loguru handlers via add() args (sink, level, format, rotation, retention, etc.)
  logging:
    level: INFO   # optional default level when handler does not set level
    handlers:     # list of handler configs; each is passed to loguru logger.add(**handler)
      - sink: stderr
        level: INFO
        format: "<level>{message}</level>"
      - sink: "runs/logs/run_{run_id}.log"   # placeholders from run context
        level: DEBUG
        rotation: "10 MB"
        retention: "1 week"
        compression: "gz"

  # Selected UI: which participant app to launch (e.g. NiceGUI)
  ui:
    backend: nicegui
    config:
      theme: dark
  ```

  Participants and sessions are created/updated/deleted via **CLI** or **API**. Conditions are synced via a **sync** CLI with the DB (similar to legacy `update_conditions`).

- **Researcher .env and .gitignore**: Add **`.env`** and **`.env.*`** (e.g. `.env.dev`, `.env.prod`) to `.gitignore` at **project root** so secrets are never committed. Document in the user guide. Use **`.env.example`** (committed, at project root) as a template listing variable names only. Optional **`SENTRY_DSN`** in `.env.example` (no value)—when set, enables Sentry error/performance monitoring when a study is run.
- **Backend (Supabase)**:
  - **Database**: Postgres via Supabase. Schema (e.g. SQLModel or raw SQL) for Study, Condition, Participant, Session, Run; **Participants** linked to Supabase Auth users (e.g. `auth.users.id`). One user can be linked to many participants (one per study). Migrations via Supabase migrations (or Alembic targeting Postgres).
  - **Auth**: Supabase Auth for sign-up, sign-in, password change. Participant app uses Supabase client; researcher CLI can use service role or admin API for creating participants and linking to auth users.
  - **Storage** (optional): Supabase Storage for run artifacts (e.g. HDF5, logs) if not stored only on participant machines.
  - **Local Supabase**: Researchers use `supabase start` for dev or self-hosted Docker for prod; framework only needs `SUPABASE_URL` and `SUPABASE_ANON_KEY` (and optionally service key for admin operations).
- **Authentication** (Supabase Auth):
  - **User**: identity in Supabase Auth; one user can be linked to many **participants** (one participant per study) in app tables.
  - **Participant**: per-study record linked to `auth.users`; used for study-specific data (sessions, runs).
  - **CLI**: `slumber auth login` (or use Supabase session); password change via Supabase; **create participant** creates/links auth user and participant row (e.g. `slumber participant create --study-id ...`).
- Implement CLI commands:
  - `slumber study init`: wizard prompts for **base dir** (default **`.`**) and **study_id**, then creates the study folder at **`<base_dir>/<study_id>/`** with `study.yaml`, `conditions/`, `assets/`. Optionally creates **`.env.example`** and a first env file at **project root** (base_dir) if not already present. Override with args: e.g. `--base-dir`, `--study-id` (non-interactive). After init, researcher **cd**s into the study folder to run other commands.
  - `slumber study validate`: run from **inside the study folder**; validates the study in cwd (finds `study.yaml` there). Optional `--study-dir <path>` to validate a study at a given path without cd.
  - `slumber study run`: run from **inside the study folder**; launches UI + `ezmsg` pipeline(s) for the study in cwd. Optional `--study-dir <path>` to run a study at a given path.
  - `slumber doctor`: environment, Supabase connectivity, and optional-dependency checks (run from study folder or project root).
  - **Backend**: configure Supabase via `.env` or env-specific file (e.g. `SLUMBER_ENV=dev` → load `.env.dev`); `slumber db migrate` (or Supabase CLI migrations) for schema.
  - **Auth/participants**: create/list participants (per study, linked to Supabase Auth); create/update/delete sessions; **sync conditions** (push condition configs from conditions folder into Supabase, similar to legacy `update_conditions`).
  - **Packaging** (Stage 1 or 3): document or stub for building installable participant app that uses configured Supabase URL/keys.
- Implement plugin discovery (recommended: Python entry points) so extensions can register:
  - **Units** (DAG component types)
  - **Tasks** (UI-agnostic task specs + UI renderers)
  - **UI backends** (NiceGUI initially)
- **Logging**: Use **loguru** for all application logging. **CLI/orchestration**: default level; add a **verbose** option (e.g. `-v` / `--verbose`) to CLI commands for more verbose output. **Run** (`slumber study run` and participant app): configure logging from **study settings** via `runs.logging`—support a **handlers** list where each item is passed as kwargs to `logger.add()` (sink, level, format, rotation, retention, compression, etc.); optional default `level`; support placeholders (e.g. `run_id`) in sink paths. Avoid stdlib `logging` in new code.
- **Sentry (optional run-time monitoring)**: When a study is run (e.g. `slumber study run`), initialize Sentry if `SENTRY_DSN` is set; set context (study_id, environment); no-op when DSN is unset. Enables researchers to monitor errors and performance during runs. Document in CLI/env docs; test that init is no-op without DSN and that context is set when DSN is present.
- **Documentation (Stage 1)**: Written as each area is implemented. Study/condition schema and manifest format; `.env` and multiple env files per environment (e.g. `.env.dev`, `.env.prod`, `SLUMBER_ENV`); .gitignore for secrets; optional Sentry (`SENTRY_DSN`) for run monitoring; CLI reference for `init`, `validate`, `run`, `doctor` (including **verbose** option), backend config, auth, participants, sessions, condition sync; **run logging** via study settings (`runs.logging`: handlers with loguru `add()` args); minimal “first study” walkthrough so researchers can init a study and use the CLI.
- **Tests (Stage 1)**: Written as each area is implemented. Schema validation tests; plugin discovery/registration tests; CLI tests (key commands); Supabase backend integration tests (or mocked); tests for participant/session CRUD and condition sync. Core code covered so Stage 1 is safe to extend.
- **Usable after Stage 1**: Researchers can init a study, configure Supabase (cloud or local), validate configs, create participants/sessions, sync conditions, and run the app (UI placeholder if needed); all with documented behavior and tests in place.

### Stage 2 — NiceGUI shell (participant UI)

- Create **`slumber.ext.ui.nicegui`** as the **participant UI shell**: app frame, navigation, procedure engine integration (UI-agnostic in core).
- Provide a minimal “default study template” that launches the NiceGUI participant app.
- **No concrete widgets yet**: instruction, survey, device connection, etc. are refactored and wired in Stage 3.
- **Documentation (Stage 2)**: Written as the UI shell and template are implemented. How to run the participant UI; structure of the NiceGUI shell and how it hooks into the procedure engine; how to use the default study template; any new CLI or config options for the UI.
- **Tests (Stage 2)**: Written as the UI shell and template are implemented. UI shell / procedure engine integration tests; smoke or contract tests for the NiceGUI app (e.g. launch, basic navigation); tests for the default template. Stage 2 behavior documented and tested.
- **Usable after Stage 2**: Researchers can launch the participant app from the framework, see the shell and navigation, and run a minimal procedure; docs and tests cover the new UI surface.

### Stage 3 — Refactor target features (this version)

Features to refactor/port into the framework for this version (widgets and infrastructure on top of the NiceGUI shell):

- **ZMax**: ZMax device integration and data collection
- **Data Queues**: Data queues and buffers
- **ZMax Data Receiver**: ZMax data receiving unit
- **HDF5 Storage**: HDF5 data storage system
- **Event Logger**: Event logging system
- **Procedure**: Procedure management system
- **Instruction Widget**: Instruction widget
- **Survey Widget**: Survey/questionnaire widget
- **ZMax Connection Widget**: ZMax device connection widget
- **Release process** (framework only): **tagging and changelog** in CI/CD; **hotfix instructions** in docs. No PyPI (or other) publish in this plan; release is for the **slumber** framework repo only.
- **Supabase as source of truth**: **researcher** uses Supabase (cloud or local) for study, conditions, participants, sessions; **participant** app reads from Supabase and **uploads run data** (and optionally artifacts to Storage). Dev vs prod = different Supabase projects or local vs cloud. **Ship participant app**: build installable app (e.g. packaged binary or `pip` bundle) so researchers can distribute it for installation on participant laptops; app connects to researcher’s configured Supabase backend.
- **Sentry in participant app**: When the participant app runs a study, initialize Sentry if `SENTRY_DSN` is set (e.g. in built app config or env); set context (study_id, participant_id, session_id) so runs can be monitored and errors attributed. Same opt-in behavior as researcher-run.
- **Documentation (Stage 3)**: Written as each feature is refactored. Each refactored feature (ZMax, queues, HDF5, event logger, procedure, instruction/survey/ZMax widgets); release and packaging process; how to build and ship the participant app; Supabase sync and dev/prod; end-to-end example study walkthrough.
- **Tests (Stage 3)**: Written as each feature is refactored. DAG wiring tests; integration tests for ZMax (or simulated device), data queues, HDF5 storage, event logger; procedure and widget tests; packaging/ship smoke test if feasible; tests for participant read/upload flow. Stage 3 features covered so the full stack is safe to use.
- **Usable after Stage 3**: Full feature set (widgets, devices, storage, procedure, sync, packaging) is implemented, documented, and tested; researchers can run an end-to-end study and ship the participant app to laptops.

### Stage 4 — Documentation (project-wide consolidation)

Unify and expand the docs written throughout Stages 1–3 into a single, cohesive set. Expand MkDocs:

- **User guide**: concepts (Study/Condition/Task/DAG), “build your first study”, config cookbook, `.env` and multiple environments, .gitignore for secrets, troubleshooting; unify and polish Stage 1–3 user-facing docs.
- **Developer guide**: architecture, extension authoring, contribution workflow.
- **API reference**: generated from docstrings (mkdocstrings) for the public API.
- **Examples**: minimal example configs + a “legacy LD study” example as a separate implementation repo.
- **Deployment**: how to fork the repo, configure Supabase (cloud or local), use dev/prod backends, **build and ship** the participant app for installation on participant laptops, and run scheduled sessions; optional **Sentry** setup for monitoring runs (researcher and participant).

**Usable after Stage 4**: Full user and developer documentation; clear path from first study to deployment.

### Stage 5 — Testing (project-wide consolidation + coverage)

Build on the tests written throughout Stages 1–3; add coverage measurement and CI enforcement:

- **Coverage**: Measure coverage for **core**; enforce a coverage gate (e.g. in CI) so regressions are caught.
- **Test pyramid**: Ensure the pyramid is complete—schema validation, plugin discovery, DAG wiring, integration (simulated devices/units), UI smoke/contract tests—filling any gaps from Stages 1–3.
- **CI**: Runs tests and coverage on every change; document how to run tests locally.

**Usable after Stage 5**: Core is under a coverage gate; test suite is the maintained standard for the project.

## Deliverables by milestone

Each milestone is **usable** at completion: features work, and docs + tests exist for that scope.

- **M1** (Stage 1): Core schemas + plugin registry + **Supabase backend** (Postgres schema, Auth, env/config) + CLI (`validate`/`run`/`doctor`, backend, auth, participants, sessions, condition sync) + optional **Sentry** for run monitoring (researcher-run) + **docs** (schema, `.env` and multi-env, Sentry, CLI, minimal “first study” walkthrough) + **tests** (schema, plugins, CLI, backend/CRUD, Sentry no-op/context). Researchers can init a study, configure Supabase, and use the CLI with confidence.
- **M2** (Stage 2): NiceGUI **shell** (participant app frame, procedure engine, default template) + **docs** (how to run UI, shell structure, template) + **tests** (shell integration, UI smoke/contract). No instruction/survey/device widgets yet. Researchers can launch the participant app and run a minimal procedure.
- **M3** (Stage 3): ZMax, queues, HDF5, event logger, procedure, instruction/survey/ZMax widgets + release process + Supabase sync + **ship participant app** + Sentry in participant app for run monitoring + **docs** (features, packaging, sync, example study, Sentry for participants) + **tests** (DAG, integration, widgets, packaging/sync). Full stack usable end-to-end.
- **M4** (Stage 4): **Project-wide docs** (unifying Stage 1–3 docs): user guide, developer guide, API reference (mkdocstrings), examples, deployment guide. Single cohesive documentation set.
- **M5** (Stage 5): **Project-wide testing** (building on Stage 1–3 tests): coverage measurement + CI gate for core; complete test pyramid; CI runs tests and coverage. Core under a maintained coverage standard.
