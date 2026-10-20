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
| `stepper` | Ordered activities: optional list + activity slot; prev/next/complete. |
| `hub` | One activity, full bleed. |

Within a layout, only the activity slot remounts. A layout swap remounts the body. After every sequential activity has `complete()`d, the layout emits `phase_completed`.

## Activities

Activities are layout-agnostic. They call host methods; they do not define what completion means for the study.

| Call | Audience | Meaning |
|------|----------|---------|
| `complete()` | Layout | This mounted instance finished as a step |
| `emit(name)` | RunEngine | A named study event happened |
| `phase_completed` | RunEngine (from layout) | Layout decided the phase is done |

| Key | Behaviour |
|-----|-----------|
| `instruction` | Renders markdown or text; calls `complete()` on mount. |
| `sleep` | Wake / end buttons → `emit("marked_awake")` / `emit("end_sleep")`. Does not complete. |

Open-ended activities (`sleep`) leave via `start_phase` / `end_run` actions, which unmount them.

## Headless behaviour

Headless uses the same event → action path:

- Activities that finish on mount auto-`complete()` (e.g. `instruction`).
- `sleep` emits `end_sleep` as soon as it mounts so setup → pipeline → morning → `end_run` can finish in CI without a browser.
- GUI waits on the wake and end buttons.

See [Running a study](../user-guide/running-a-study.md) and the `examples/demo/` package in the repository.
