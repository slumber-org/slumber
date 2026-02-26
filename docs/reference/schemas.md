# Schema reference

Core Pydantic schemas for study manifest, conditions, procedures, and DAG. All live under `slumber.schemas` and are used for config loading and validation.

## Study manifest (`study.yaml`)

The study manifest describes a single study: identity, where conditions live, run layout, run-time logging, and UI selection.

| Field | Type | Description |
|-------|------|-------------|
| `study_id` | string | Unique study identifier (required). |
| `name` | string | Human-readable study name (required). |
| `conditions_dir` | string | Directory name, relative to study folder, containing condition YAML files. Default: `conditions`. |
| `runs` | RunLayout | Run output directory layout (base_directory + layout with placeholders). |
| `logging` | RunLoggingConfig | Logging config for runs: `level` and `handlers` (list of dicts passed to loguru `logger.add()`). |
| `ui` | UI | Selected UI backend key and optional config. |

**RunLayout**: `base_directory` (default `runs`) and `layout` (path template). Allowed placeholders in `layout`: `study_id`, `participant_id`, `session_id`, `run_id`, `condition_id`.

**RunLoggingConfig**: `level` (default `INFO`), `handlers` (list of handler configs; each is kwargs for `logger.add()`). Sink paths may use placeholders (e.g. `run_id`) substituted at run start.

**UI**: `backend` (plugin key, e.g. `headless`, `nicegui`), `config` (optional dict for the backend).

Extra keys in the manifest are forbidden.

## Condition file (per-condition YAML)

One condition = named procedures + one DAG. Typically stored in `<study_dir>/<conditions_dir>/<condition_name>.yaml`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Condition name (required). |
| `procedures` | dict[str, Procedure] | Mapping from procedure name to Procedure (e.g. `pre_sleep`, `awakening`, `post_sleep`, `wbtb`). At least one required. |
| `dag` | DAG | Processing DAG for this condition (required). |

## Procedure and Task

Procedures are UI-agnostic: each task is keyed by a **type** string (resolved via the `slumber.tasks` entry point), not by widget class.

**Task**:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Task plugin key (e.g. `instruction`, `survey`). |
| `title` | string | Human-readable task title. |
| `kwargs` | dict | Plugin-specific options (optional). |

**Procedure**:

| Field | Type | Description |
|-------|------|-------------|
| `tasks` | list[Task] | Ordered list of tasks (at least one). |
| `show_task_list` | bool | Whether to show the task list in the UI. Default: true. (YAML may use `show_item_list` as alias.) |
| `allow_skip_tasks` | bool | Whether the current task can be skipped. Default: false. |

## DAG

Processing DAG: components (plugin-keyed by `unit_type`), stream connections, and process component names. Units are resolved via the `slumber.units` entry point at runtime; the schema does not resolve to classes.

**Component**:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique component name: uppercase with underscores (e.g. `MASTER`, `ZMAX_STORAGE`). |
| `unit_type` | string | Unit plugin key (YAML may use `unit` as alias). |
| `settings` | dict \| null | Plugin-specific unit settings (optional). |

**Connection**: `output_stream` and `input_stream`, each in the form `<component_name>/<stream_name>` (e.g. `ZMAX/OUTPUT_SAMPLE`).

**DAG**:

| Field | Type | Description |
|-------|------|-------------|
| `components` | list[Component] | At least one component; names must be unique. |
| `connections` | list[Connection] | Stream connections (output → input). May be given as `[output_stream, input_stream]` tuples. |
| `process_components` | list[str] | Component names that run as separate processes. Each must exist in `components`. |

Validation: connection stream names must reference existing component names (first segment before `/`). Stream existence on the actual unit is checked at runtime via the plugin registry.
