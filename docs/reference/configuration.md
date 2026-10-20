# Configuration reference

Core Pydantic schemas for study manifests and conditions. All live under `slumber.schemas` and validate **shape only** — they do not import the plugin registry or resolve implementations.

## PluginSpec

Shared reference used by UI, layouts, activities, and units:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Entry-point name or built-in key (required). |
| `settings` | dict | Optional settings validated later by the implementation. |

## Study manifest (`study.yaml`)

| Field | Type | Description |
|-------|------|-------------|
| `study_id` | string | Unique study identifier (required). |
| `study_name` | string | Human-readable study name (required). |
| `conditions_dir` | string | Directory of condition YAML files, relative to the study folder. Default: `conditions`. |
| `assets_dir` | string | Directory of assets, relative to the study folder. Default: `assets`. |
| `runs` | RunLayout | Run output directory and path template. |
| `ui` | PluginSpec | UI selection (`gui` or `headless`) and optional settings. Default type: `headless`. |
| `logging` | LoggingConfig | Run logging: `level` and `handlers` (list of dicts passed to loguru `logger.add()`). |

**RunLayout**: `directory` (default `runs`) and `layout` (path template, default `run-{run_id}`). Allowed placeholders in `layout`: `study_id`, `run_id`, `condition_id`, `participant_id`, `session_id`.

**LoggingConfig**: `level` (default `INFO`), `handlers` (list of handler configs). Sink paths may use placeholders (e.g. `run_id`, `run_dir`) substituted at run start.

**UI (`PluginSpec`)**: `type` is `gui` or `headless`. For `gui`, optional `settings` may include `port`, `favicon`, `frame`, and `layouts` (stepper defaults). See [UI](ui.md).

Extra keys in the manifest are forbidden.

Minimal example:

```yaml
study_id: demo
study_name: Demo Study
ui:
  type: headless
```

## Condition file (per-condition YAML)

One condition = entry phase + phases + optional pipelines. Stored as `<study_dir>/<conditions_dir>/<name>.yaml`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Condition name (required). |
| `entry` | string | Id of the phase to start (required). |
| `phases` | list[Phase] | Named stages (at least one). |
| `pipelines` | list[Pipeline] | Named processing graphs (optional). |

## Phase

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique phase id (required). |
| `title` | string | Display title. Defaults to `id` when omitted. |
| `layout` | PluginSpec | Layout (`stepper` or `hub`) and settings. |
| `activities` | list[Activity] | Ordered activities (at least one). |
| `frame` | FrameSettings | Optional AppFrame override merged over study `ui.settings.frame`. |
| `on` | list[EventHandler] | Phase-scoped event handlers. |

`frame.header` / `frame.footer` may be `false` to hide chrome (typical during sleep).

## Activity

Extends PluginSpec with instance fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique activity id within the phase. |
| `title` | string | Display title. Defaults to `id`. |
| `type` | string | Activity plugin key (e.g. `instruction`, `sleep`). |
| `settings` | dict | Plugin-specific settings. |
| `on` | list[EventHandler] | Activity-scoped event handlers. |

Built-in activities: `instruction` (markdown/text; calls `complete()` on mount), `sleep` (wake/end buttons; emits study events, never completes).

## Pipeline

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique pipeline id. |
| `units` | list[Unit] | Units (`id` + PluginSpec). At least one. |
| `connections` | list[Connection] | Stream links. Shorthand `[output, input]` or `{output, input}`. |

**Unit**: `id` plus `type` / `settings` (PluginSpec). Stream endpoints use `<unit_id>/<stream_name>` (e.g. `clock/OUTPUT`).

Built-in units: `clock` (periodic samples at `settings.rate`), `jsonl_writer` (append to `settings.path`).

## Actions and events

**Action** — exactly one of:

| Field | Meaning |
|-------|---------|
| `start_phase` | Phase id to start |
| `start_pipeline` | Pipeline id to start |
| `stop_pipeline` | Pipeline id to stop |
| `end_run` | End the run (`true` / bare `end_run`) |

**EventHandler**: `event` (string) + `do` (ordered list of actions).

Handlers on the emitting activity are matched first, then handlers on the active phase. Layouts emit `phase_completed` when every sequential activity has `complete()`d. Activities may `emit` named study events (e.g. `marked_awake`, `end_sleep`).

## Path placeholders

Placeholders expand first; then relative results resolve against the **study root**. Absolute paths stay absolute.

| Placeholder | Expands to |
|-------------|------------|
| `{assets_dir}` | Study assets directory |
| `{run_dir}` | This run's directory |
| `{run_id}` | Run id |
| `{study_name}` | Study display name |
| `{study_id}` | Study id |

Plus run-layout keys (`condition_id`, `participant_id`, `session_id`) where applicable.
