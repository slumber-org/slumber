# UI reference

`study.ui` selects how a run is presented. 0.1 backends are a **built-in map** (`gui` | `headless`), not an entry-point group. Both drive the same RunEngine; they differ only in presentation.

```yaml
ui:
  type: gui   # or headless
```

| `type` | Role |
|--------|------|
| `gui` | Participant window (NiceGUI): AppFrame + layout + activities. |
| `headless` | No window. Sequential activities auto-`complete()`. Sleep emits `end_sleep` on mount so the demo finishes without a browser. |

Override for one run: `slumber study run --ui headless` (or `gui`). Switching to headless clears GUI-only settings.

## GUI settings

Optional under `ui.settings` when `type` is `gui`:

```yaml
ui:
  type: gui
  settings:
    port: 8080
    favicon: "{assets_dir}/favicon.png"
    frame:
      header:
        logo: "{assets_dir}/logo.png"
        title: "{study_name}"
        show_phase_title: true
    layouts:
      stepper:
        previous_button: Previous
        next_button: Next
        complete_button: Complete
        show_activity_list: true
        show_progress_bar: true
        show_step_count: true
        show_step_name: false
        number_steps: false
        allow_skip: false
```

Phase `layout.settings` deep-merges over study `ui.settings.layouts.<type>`. Phase `frame` deep-merges over study `ui.settings.frame` (e.g. hide header/footer during sleep).

Requires the NiceGUI optional dependency:

```bash
uv sync --extra nicegui
```

## AppFrame

Chrome around the layout: header (logo and study title on the left, optional phase title centred), body, footer (caption on the right). Study frame is the default; `start_phase` merges the phase's optional frame override over it, expands placeholders in the header title and resolves the header logo path, then calls `UIBackend.apply_frame(frame, phase)`.

## Layouts

Each phase selects a layout. Layouts fill the AppFrame body and host that phase's activities.

| `type` | Role |
|--------|------|
| `stepper` | Ordered activities: optional list + activity slot, progress bar, prev/next/complete. |
| `hub` | One activity filling the body. |

Stepper settings and the step states are described in the [user guide](../user-guide/nicegui-ui.md#stepper).

Within a layout, only the activity slot remounts. A layout swap remounts the body. For when each layout sends `phase_completed`, see [Run lifecycle](../concepts/run-lifecycle.md#when-a-phase-is-completed).

## Activities

Activities report back with `complete()` and `emit(name)`; see [How activities signal](../concepts/run-lifecycle.md#how-activities-signal).

| Key | Behaviour |
|-----|-----------|
| `instruction` | Renders markdown or text (image paths resolve like other study paths); calls `complete()` on mount. |
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

For how headless runs a condition overall, see [gui and headless](../concepts/run-lifecycle.md#gui-and-headless). See [Running a study](../user-guide/running-a-study.md) and the `examples/demo/` package in the repository.
