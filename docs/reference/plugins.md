# Plugin reference

The framework discovers **activities** and **units** via Python entry points. UI backends and layouts are a **built-in map**, resolved through the same `resolve_plugin_spec` helper. No module scanning is used.

YAML → schemas (shape only) → config (`resolve_plugin_spec`) → RunEngine.

## Entry-point groups

| Group | Purpose | Used by |
|-------|---------|---------|
| `slumber.activities` | Participant-facing steps | Phase activities |
| `slumber.units` | ezmsg nodes in a pipeline | Pipeline manager |

Register plugins in `pyproject.toml`:

```toml
[project.entry-points."slumber.activities"]
instruction = "slumber.ui.activities.instruction:InstructionActivity"
sleep = "slumber.ui.activities.sleep:SleepActivity"

[project.entry-points."slumber.units"]
clock = "slumber.pipeline.units.clock:ClockUnit"
jsonl_writer = "slumber.pipeline.units.jsonl_writer:JsonlWriterUnit"
```

Optional packages may also attach Typer apps through the `slumber.cli` entry-point group (not a PluginSpec).

## Plugin registry

```python
from slumber.plugins import EntryPointGroup, get_registry, PluginNotFoundError

registry = get_registry()

activity_class = registry.get_plugin(EntryPointGroup.ACTIVITIES, "instruction")
unit_class = registry.get_plugin(EntryPointGroup.UNITS, "clock")

registry.list_plugins(EntryPointGroup.ACTIVITIES)
registry.list_plugins(EntryPointGroup.UNITS)
```

Built-in UI (`gui`, `headless`) and layouts (`stepper`, `hub`) are **not** entry points; config consults a built-in map owned by `slumber.ui`.

## Contracts

### ConfiguredPlugin

Shared base for activities (and UI/layout adapters):

```python
class ConfiguredPlugin(ABC):
    settings_model: ClassVar[type[BaseModel] | None] = None
```

Config validates `settings` against `settings_model` when resolving a PluginSpec.

### Activity (`slumber.activities`)

- Subclass of `ConfiguredPlugin` with `mount(activity_host)` / `unmount()`.
- Host provides the UI container, `complete()`, `emit()`, and path helpers.
- `complete()` tells the layout this step finished; `emit(name)` sends a study event to the RunEngine.

### Unit (`slumber.units`)

- Subclass of `ez.Unit`. Settings use the unit's `SETTINGS` class (prefer `slumber.pipeline.units.Settings` for Pydantic validation).
- Config builds instances via the pipeline helpers; stream names are checked when starting a pipeline.

```python
import ezmsg.core as ez
from pydantic import Field

from slumber.pipeline.units import Settings


class MyUnitSettings(Settings):
    rate: float = Field(gt=0)


class MyUnit(ez.Unit):
    SETTINGS = MyUnitSettings
```

## Built-in plugins

| Kind | Keys | Notes |
|------|------|-------|
| UI | `gui`, `headless` | Built-in map. Same RunEngine; presentation differs. |
| Layout | `stepper`, `hub` | Built-in map. |
| Activity | `instruction`, `sleep` | Entry points under `slumber.activities`. |
| Unit | `clock`, `jsonl_writer` | Entry points under `slumber.units`. |

## Errors

- **PluginNotFoundError** (subclass of `LookupError`): Raised when a requested plugin key is not registered. Attributes: `group`, `key`, `available`.
