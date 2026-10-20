# UI reference

Lookup tables for the `ui` section of `study.yaml` and the built-in layouts and activities. For how to use them, see [Participant UI](../user-guide/participant-ui.md).

## UI types

Set with `ui.type`. Both use the same RunEngine; they only differ in presentation.

| `type` | Description |
|--------|-------------|
| `gui` | Participant window in the browser (NiceGUI): AppFrame, layouts and activities. Requires the `nicegui` extra. |
| `headless` | No window. Used for testing; see [Headless behaviour](#headless-behaviour). Default for new studies. |

`slumber study run --ui gui|headless` overrides `ui.type` for one run. `--ui headless` ignores all `ui.settings`.

## GUI settings

Under `ui.settings` when `ui.type` is `gui`. All are optional.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `port` | integer | `8080` | Port the GUI runs on. |
| `favicon` | path | SLUMBER favicon | Browser tab icon. |
| `frame` | [Frame settings](#frame-settings) | header and footer shown | Default AppFrame for every phase. |
| `layouts.stepper` | [Stepper settings](#stepper) | see table | Default settings for every `stepper` phase. |

## Frame settings

Under `ui.settings.frame` (study default) or a phase's `frame` (override for that phase). A phase's `frame` is merged on top of the study's.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `header` | `false` or mapping | shown | `false` hides the header. |
| `header.logo` | path | SLUMBER logo | Logo in the header. |
| `header.title` | string | `study_name` | Title in the header. |
| `footer` | boolean | shown | `false` hides the footer. |

## Layouts

Set with a phase's `layout.type`. A phase's `layout.settings` is merged on top of the study's `ui.settings.layouts.<type>`.

| `type` | Description |
|--------|-------------|
| `stepper` | Ordered activities with **Previous**, **Next** and **Complete** buttons and an optional list of steps. |
| `hub` | One activity, full screen, no navigation. |

For when each layout sends `phase_completed`, see [Run lifecycle](../concepts/run-lifecycle.md#when-a-phase-is-completed).

### Stepper

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `previous_button` | string | `Previous` | Label of the button to the previous step. |
| `next_button` | string | `Next` | Label of the button to the next step. |
| `complete_button` | string | `Complete` | Label of the button on the last step, which completes the phase. |
| `show_activity_list` | boolean | `true` | Show the list of steps. |
| `allow_skip` | boolean | `false` | Let the participant move on before a step has finished. |

### Hub

No settings.

## Activities

Activities report back with `complete()` and `emit(name)`; see [How activities signal](../concepts/run-lifecycle.md#how-activities-signal).

| Key | Behaviour |
|-----|-----------|
| `instruction` | Renders markdown or text; calls `complete()` on mount. |
| `sleep` | Wake / end buttons → `emit("marked_awake")` / `emit("end_sleep")`. Does not complete. |

### Activity settings

Set under the activity's `settings:`. All are optional.

| Activity | Setting | Default | Description |
|----------|---------|---------|-------------|
| `instruction` | `content` | `""` | Markdown text, or a path to a Markdown file (usually `{assets_dir}/…`). If the value is not an existing file, it is shown as text. |
| `sleep` | `wake_button` | `I'm Awake` | Label of the button that emits `marked_awake`. |
| `sleep` | `end_button` | `End Session` | Label of the button that emits `end_sleep`. |

For how to use them in a condition, see [Writing conditions](../user-guide/writing-conditions.md#add-activities).

## Headless behaviour

| Key | Headless |
|-----|----------|
| `instruction` | Completes on mount, as in the GUI. |
| `sleep` | Emits `end_sleep` shortly after mounting. Never emits `marked_awake`. |

For how headless runs a condition overall, see [gui and headless](../concepts/run-lifecycle.md#gui-and-headless).
