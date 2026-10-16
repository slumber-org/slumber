# Participant UI

This page shows how to configure what the participant sees when a study runs in the GUI: the window around each screen, how each phase is laid out, and the buttons.

## Before you start

The GUI needs the optional NiceGUI dependency. If you didn't add it when installing SLUMBER, add it now:

```bash
uv sync --extra nicegui
```

Your study must also be set to use the GUI. `slumber study init` sets new studies to `headless`, so change `ui.type` in the study manifest (`study.yaml`) to `gui`:

```yaml
ui:
  type: gui
```

`slumber study run` opens the participant window in the browser. To test a condition without a window, add `--ui headless` to the command; this ignores all GUI settings for that run. See [Running a study](running-a-study.md).

## What the participant sees

Every screen sits inside the same window, the [AppFrame](../concepts/glossary.md#appframe):

```text
AppFrame
├── header   logo and title on the left, phase title in the middle (optional)
├── body     the current phase's layout and activities
└── footer   "Powered by SLUMBER" on the right
```

The AppFrame stays the same for the whole run. When a new phase starts, only the body changes. The header and footer can be shown or hidden, depending on the phase. Everything you set under `ui.settings` in `study.yaml` is the default for every phase, but a phase can override parts of it, as shown below. For a list of every setting and its default, see the [UI reference](../reference/ui.md).

## Change the header and footer per phase

During sleep, the screen should be dark, with as few distractions as possible. You can hide the header and footer for that phase with `frame`:

```yaml
  - id: sleep
    frame:
      header: false
      footer: false
    layout:
      type: hub
    ...
```

The override only applies while that phase (sleep, in this case) is active. When the next phase starts without a `frame`, the header and footer come back.

A phase can also change the header title:

```yaml
  - id: morning
    frame:
      header:
        title: Good morning
```

When the next phase starts, the header shows the study's title again.

To also show the current phase's `title` in the middle of the header, turn on `show_phase_title` for the whole study:

```yaml
ui:
  type: gui
  settings:
    frame:
      header:
        show_phase_title: true
```

## Choose stepper or hub

Each phase picks a layout in its condition file:

- **`stepper`** for screens the participant goes through in order, such as instructions. It shows **Previous**, **Next** and **Complete** buttons (the labels can be changed, see [below](#set-button-labels-and-skipping)), and optionally a list of the steps.
- **`hub`** for a single activity that fills the screen without navigation, such as the sleep screen.

See [Writing conditions](writing-conditions.md#choosing-a-layout) for how to add a layout to a phase.

## Set button labels and skipping

Set the stepper's button labels and behaviour once for the whole study under `ui.settings.layouts.stepper`. For example, to use different labels and hide the list of steps:

```yaml
ui:
  type: gui
  settings:
    layouts:
      stepper:
        previous_button: Back
        next_button: Continue
        complete_button: Done
        show_activity_list: false
```

To change a setting for one phase only, set it under that phase's `layout.settings`. It is merged on top of the study defaults, so you only write what differs:

```yaml
  - id: setup
    layout:
      type: stepper
      settings:
        allow_skip: true
```

With `allow_skip: true`, the participant can open any step from the list and complete the phase without finishing every step. Without it, a step only becomes available once the steps before it are finished.

## Change the sleep buttons

The `sleep` activity has a main button that toggles between **Going to Sleep** and **I'm Awake**, and an **End Session** button below it. Only **End Session** asks "Are you sure?" by default. Change the labels under the activity's `settings`, or change what a button asks:

```yaml
    activities:
      - id: sleep
        type: sleep
        settings:
          message: "Press a button when you go to bed, wake up or finish."
          sleep_button: "Going to Bed"
          wake_button: "I Woke Up"
          end_button:
            label: "Finish Night"
            confirm:
              title: "Finish the night?"
              message: "This ends the sleep phase."
              confirm_label: "Yes, finish"
              cancel_label: "Not yet"
```

Quote labels such as `"Yes"` or `"No"`, because YAML reads them as true or false. Every setting, the button styles and the questions are listed in the [UI reference](../reference/ui.md#how-the-sleep-buttons-work).

## Change the port

The GUI runs on port 8080. If that port is already in use, choose another one:

```yaml
ui:
  type: gui
  settings:
    port: 8081
```

## Use your own logo, favicon and title

By default, the GUI shows the SLUMBER logo and favicon and uses `study_name` as the header title. To use your own, put the files in `assets/` and refer to them in `study.yaml`:

```yaml
ui:
  type: gui
  settings:
    favicon: "{assets_dir}/favicon.png"
    frame:
      header:
        logo: "{assets_dir}/logo.png"
        title: "{study_name}"
```

The colours and font are fixed in SLUMBER 0.1: only the logo, favicon and title can be changed.
