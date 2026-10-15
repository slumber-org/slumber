# Participant UI (GUI)

The GUI backend presents a run in a browser window via [NiceGUI](https://nicegui.io/). It uses the same RunEngine as headless: phases, layouts, activities, and event → action handlers.

## Setup

```bash
uv sync --extra nicegui
```

```yaml
ui:
  type: gui
  settings:
    port: 8080
    frame:
      header:
        title: "{study_name}"
        show_phase_title: true
    layouts:
      stepper:
        show_activity_list: true
        allow_skip: false
```

## App flow

```
AppFrame
  ├── header            ← logo and study title on the left, phase title centred
  ├── body
  │     └── layout (stepper | hub)
  │           └── activity slot
  └── footer            ← "Powered by SLUMBER" caption
```

1. Run starts → theme + AppFrame mount once.
2. Engine `start_phase(entry)` → apply the phase's frame (study frame merged with the phase override) → mount layout + activities.
3. Activities call `complete()` or `emit(...)`; handlers run `do` actions.
4. `end_run` unmounts and finishes.

Phases are started by actions (`start_phase`), not sequenced as a flat procedure list.

## AppFrame

| Setting (`frame.header`) | Effect |
|--------------------------|--------|
| `title` | Study title in the header. Placeholders such as `{study_name}` are expanded. Defaults to the study name. |
| `logo` | Header logo path (relative to the study root, typically `{assets_dir}/…`). A phase can set its own. |
| `show_phase_title` | Show the active phase's `title` centred in the header. Off unless set. |

A phase's `frame` merges over the study's, so a phase only lists what it changes. `header: false` or `footer: false` hides that region (typical during sleep).

## Layouts

| Layout | Use |
|--------|-----|
| `stepper` | Ordered steps with an optional activity list, a progress bar and navigation. |
| `hub` | A single activity filling the body, centred (e.g. sleep). |

Phase `layout.settings` merges over study `ui.settings.layouts.<type>`.

### Stepper

| Setting | Default | Effect |
|---------|---------|--------|
| `previous_button`, `next_button`, `complete_button` | Previous, Next, Complete | Button labels. |
| `show_activity_list` | `true` | List of the steps beside the activity. |
| `show_progress_bar` | `true` | Progress bar between Previous and Next. |
| `show_step_count` | `true` | "Step x of y" above the bar. Needs the bar. |
| `show_step_name` | `false` | The current step's title above the bar. Needs the bar. |
| `number_steps` | `false` | Number the steps in the list. |
| `allow_skip` | `false` | Let the participant open any step and complete the phase without finishing every step. |

Each step has a **state**: not started, current, or done (its activity called `complete()`). The list and the progress bar show the same states.

A step is also **available** or not, worked out from the states. A step is available when every step before it is done. Unavailable steps are dimmed in the list and cannot be opened. Complete is enabled once every step is done. With `allow_skip` every step is available and Complete is always enabled.

Long content scrolls inside the activity card; the header, buttons and footer stay in place. Below 800 px wide the list becomes a strip above the activity. Sizes follow the size of the app window.

## Activities

| Activity | Behaviour |
|----------|-----------|
| `instruction` | Markdown/text from `settings.content` (path or string). Completes on mount. |
| `sleep` | "I'm Awake" / "End Session" (labels configurable). Emits `marked_awake` / `end_sleep` only. |

Example sleep phase (hidden chrome):

```yaml
- id: sleep
  frame:
    header: false
    footer: false
  layout:
    type: hub
  activities:
    - id: sleep
      type: sleep
      settings:
        wake_button: "I'm Awake"
        end_button: "End Session"
      on:
        - event: marked_awake
          do: [{ start_phase: awakening }]
        - event: end_sleep
          do:
            - stop_pipeline: main
            - start_phase: morning
```

## Branding

Fixed dark theme tokens load once at GUI start. Package defaults supply logo and favicon; override with `ui.settings.favicon` and `frame.header.logo` (paths relative to the study root, typically `{assets_dir}/…`). If a phase's logo file is missing, the header shows the study logo; if that is missing too, the packaged SLUMBER logo. A warning is written to the run log.

See [UI reference](../reference/ui.md) and [Configuration reference](../reference/configuration.md).
