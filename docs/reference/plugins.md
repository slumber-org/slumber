# Plugin reference

The framework discovers **units**, **tasks**, and **UI backends** via Python entry points. No direct module scanning is used; extensions and the core package register plugins under fixed entry-point groups.

## Entry-point groups

| Group | Purpose | Used by |
|-------|---------|--------|
| `slumber.units` | Create DAG components | DAG runtime |
| `slumber.tasks` | Create and validate procedure tasks | Procedure runtime |
| `slumber.ui_backends` | UI backends (run procedures without/with GUI) | Study run |

Register your plugin in `pyproject.toml`. For `slumber.units`, register the **Unit class** (ez.Unit subclass); the registry stores the class; use `build_unit_from_settings(unit_class, settings)` to build instances. For `slumber.tasks`, register a **Task subclass** (the class is stored; use `build_task_from_settings` to build instances from step settings). For `slumber.ui_backends`, register a **`UIBackend` subclass** (the class is stored; the orchestrator instantiates it per run, calls `configure(study.ui.settings)`, then `run`).

```toml
[project.entry-points."slumber.tasks"]
my_task = "mypackage.tasks:MyTask"

[project.entry-points."slumber.units"]
my_unit = "mypackage.units:MyUnit"

[project.entry-points."slumber.ui_backends"]
my_ui = "mypackage.ui:MyUIBackend"
```

## Plugin registry

Use the default registry from code:

```python
from slumber.plugins import EntryPointGroup, get_registry, PluginNotFoundError

registry = get_registry()

# Resolve plugins (raises PluginNotFoundError if missing)
unit_class = registry.get_plugin(EntryPointGroup.UNITS, "my_unit")
task_class = registry.get_plugin(EntryPointGroup.TASKS, "my_task")
ui_backend = registry.get_plugin(EntryPointGroup.UI_BACKENDS, "my_ui")

# List registered keys per group
registry.list_plugins(EntryPointGroup.UNITS)
registry.list_plugins(EntryPointGroup.TASKS)
registry.list_plugins(EntryPointGroup.UI_BACKENDS)
```

## Contracts

### Unit (`slumber.units`)

- **Resolved as:** A **Unit class** (subclass of `ez.Unit`). The registry stores the class; use `build_unit_from_settings(unit_class, settings)` from `slumber.plugins.units` to build instances.
- **Usage:** The runtime resolves the unit class and calls `build_unit_from_settings` with the component’s `settings` to build the unit instance for the DAG.

**Register the class:** Register your ez.Unit subclass; the registry stores it. Use the framework’s `Settings` (subclass of `ez.Settings`) from `slumber.plugins.units` for the unit’s `SETTINGS` so config dicts are validated and coerced.

```toml
[project.entry-points."slumber.units"]
my_unit = "mypackage.units:MyUnit"
```

```python
import ezmsg.core as ez
from pydantic import Field

from slumber.plugins.units import Settings

class MyUnitSettings(Settings):
    enabled: bool = True
    count: int = Field(ge=0, le=100)

class MyUnit(ez.Unit):
    SETTINGS = MyUnitSettings

    def __init__(self, settings: MyUnitSettings) -> None:
        super().__init__(settings)
        self.settings = settings
```

You can use plain `ez.Settings` (e.g. dataclass-style) if you don’t need validation; `build_unit_from_settings` will call `SETTINGS(**settings_dict)` in that case.

### Task (`slumber.tasks`)

- **Resolved as:** A **Task class** (subclass of `Task` from `slumber.plugins.tasks.base`). The registry stores the class; use `build_task_from_settings(task_class, settings)` from `slumber.plugins.tasks` to build and validate an instance from a step's settings.
- **Procedure spec:** In condition YAML, each **step** has `task_type` (or alias `task`) and optional `settings` (dict), similar to DAG `Component` with `unit_type` and `settings`. A procedure is a list of steps.
- **Usage:** Config loading or validate resolves the Task class and calls `build_task_from_settings`; the run uses the step spec (task_type, settings) when executing the procedure.

### UI backend (`slumber.ui_backends`)

- **Resolved as:** A **class** subclassing **`UIBackend`** (`slumber.plugins.ui.base`). The registry stores the class. Each run constructs an instance, calls `configure(study.ui.settings)`, then `run(study, condition, context)`. Declare optional `ui_settings_model` (Pydantic model) or `None` if `ui.settings` must be empty.
- **Usage:** The orchestrator resolves the backend class, builds an instance, validates UI settings, and runs the full participant UI lifecycle (procedure iteration, pages, events).

## Built-in plugins

The core package ships:

- **`slumber.ui_backends.headless`** — Headless UI backend: no window, runs all procedures sequentially and logs steps (for validate/CI/minimal run).
- **`slumber.tasks.instruction`** — Task class `InstructionTask` (task_type `instruction`) with optional `text` or `content` settings.

No built-in **units** are provided; DAG units are added by extensions (e.g. device or processing packages).

## Errors

- **PluginNotFoundError** (subclass of `LookupError`): Raised when a requested plugin key is not registered. Attributes: `group`, `key`, `available` (list of registered keys for that group).
