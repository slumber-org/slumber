# UI Backends

UI backends subclass **`UIBackend`** (`slumber.plugins.ui.base`) and control the full participant experience for a study condition.

## `UIBackend`

- **`ui_settings_model`**: `ClassVar[type[BaseModel] | None]` — Pydantic model for `study.ui.settings`, or `None` if the backend accepts no settings.
- **`configure(settings: dict) -> None`**: Validates and stores settings (implemented on the base class).
- **`run(study, condition, context) -> None`**: Run the full UI lifecycle (implemented by each backend).

The orchestrator calls `configure()` once per run with `study.ui.settings`, then `run()`.

### Arguments to `run`

- **`study`**: The loaded `Study` manifest.
- **`condition`**: The `Condition` to run (procedures dict + DAG).
- **`context`**: `RunContext` with IDs (study, participant, session, run, condition).

Participant-facing settings live under **`study.ui.settings`** in `study.yaml` (see study schema).

## Built-in Backends

### `headless`

Logs all procedures and steps without displaying a UI. Ignores triggers and guards — runs all procedures sequentially. Used for testing and CI. Does not accept `ui.settings`.

### `nicegui`

Web-based participant app using [NiceGUI](https://nicegui.io/). Provides login, welcome, procedure execution, sleep monitoring, and completion pages. See [NiceGUI UI guide](../user-guide/nicegui-ui.md).

Requires the `nicegui` optional dependency:

```bash
uv sync --extra nicegui
```

## Event System

The event dispatch engine (`slumber.runtime.events`) is UI-agnostic and available to all backends.

### SessionState

Mutable key-value store tracking runtime state during a session:

```python
from slumber.runtime.events import SessionState

state = SessionState()
state.handle_event("wake_up")  # auto-increments awakening_count
state.set("custom_key", "value")  # arbitrary keys
state.get("custom_key")  # → "value"
state.awakening_count  # → 1
```

### Guard Evaluation

```python
from slumber.runtime.events import evaluate_guard

evaluate_guard(None, state)  # always True
evaluate_guard({"awakening_count": 1}, state)  # exact match
evaluate_guard({"awakening_count": {"gt": 1}}, state)  # comparison
evaluate_guard("my_module:my_func", state)  # Python callable
```

### Procedure Matching

```python
from slumber.runtime.events import get_triggered_procedures

triggered = get_triggered_procedures("wake_up", condition.procedures, state)
# Returns list of (name, procedure) tuples in YAML order
```

## Task Renderer Dispatch

The NiceGUI backend uses a renderer dispatch to map `task_type` to render functions:

```python
from slumber.plugins.ui.nicegui.renderers import register_renderer, get_renderer


def render_my_task(step, container):
    from nicegui import ui

    with container:
        ui.label(f"Custom: {step.settings}")


register_renderer("my_task", render_my_task)
```

Unregistered task types fall back to a placeholder renderer.

## Implementing a Custom Backend

1. Subclass **`UIBackend`** (`slumber.plugins.ui.base`), set `ui_settings_model` (or `None`), and implement `run()`.
2. Register the **class** as an entry point in `pyproject.toml`:

```toml
[project.entry-points."slumber.ui_backends"]
my_backend = "my_package.backend:MyBackend"
```

3. Set `ui.backend: my_backend` in `study.yaml` (and optional `ui.settings` if your model defines fields).
