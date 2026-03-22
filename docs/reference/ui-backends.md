# UI Backends

UI backends implement the `UIBackend` protocol and control the full participant experience for a study condition.

## UIBackend Protocol

```python
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class UIBackend(Protocol):
    def run(
        self,
        study: Study,
        condition: Condition,
        context: RunContext,
        config: dict[str, Any],
    ) -> None:
        """Run the full UI lifecycle for a condition."""
        ...
```

The orchestrator calls `run()` once per study run. The backend owns the full lifecycle: displaying pages, executing procedures, handling user interaction, and returning when the session is complete.

### Arguments

- **`study`**: The loaded `Study` manifest (name, settings, UI config).
- **`condition`**: The `Condition` to run (procedures dict + DAG).
- **`context`**: `RunContext` with IDs (study, participant, session, run, condition).
- **`config`**: The `study.ui.config` dict from the manifest.

## Built-in Backends

### `headless`

Logs all procedures and steps without displaying a UI. Ignores triggers and guards — runs all procedures sequentially. Used for testing and CI.

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
state.handle_event("wake_up")    # auto-increments awakening_count
state.set("custom_key", "value") # arbitrary keys
state.get("custom_key")          # → "value"
state.awakening_count             # → 1
```

### Guard Evaluation

```python
from slumber.runtime.events import evaluate_guard

evaluate_guard(None, state)                      # always True
evaluate_guard({"awakening_count": 1}, state)     # exact match
evaluate_guard({"awakening_count": {"gt": 1}}, state)  # comparison
evaluate_guard("my_module:my_func", state)        # Python callable
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
from slumber.ext.ui.nicegui.renderers import register_renderer, get_renderer

def render_my_task(step, container):
    from nicegui import ui
    with container:
        ui.label(f"Custom: {step.settings}")

register_renderer("my_task", render_my_task)
```

Unregistered task types fall back to a placeholder renderer.

## Implementing a Custom Backend

1. Create a class with a `run()` method matching the protocol.
2. Register it as an entry point in `pyproject.toml`:

```toml
[project.entry-points."slumber.ui_backends"]
my_backend = "my_package.backend:MyBackend"
```

3. Set `ui.backend: my_backend` in `study.yaml`.
