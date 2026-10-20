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
| `stepper` | Ordered steps with optional activity list and navigation. |
| `hub` | Single full-bleed activity (e.g. sleep). |

Phase `layout.settings` merges over study `ui.settings.layouts.<type>`.

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
