# Writing conditions

A condition file describes one arm of your study, for example *active* versus *control*: it defines what participants see and interact with, as well as what happens behind the scenes. This page builds a condition step by step.

For what happens at runtime when the condition runs, see [Run lifecycle](../concepts/run-lifecycle.md). For every field and its default, see the [Configuration reference](../reference/configuration.md#condition-file-per-condition-yaml).

## The condition file

Each condition is one YAML file in the study's `conditions/` folder. A study can have as many as you like:

```text
my-study/
└── conditions/
    ├── control.yaml
    ├── stimulation-type-1.yaml
    └── stimulation-type-2.yaml
```

### The basic structure

A condition has four top-level keys:

```yaml
name: demo        # same as the file name
entry: setup      # the phase the run starts in
phases: [...]     # the stages of the session
pipelines: [...]  # optional: background recording
```

`entry` must correspond to the `id` of one of the phases. The rest of this page fills in `phases` and `pipelines`.

### File naming

The file name, without `.yaml` or `.yml`, must be the same as the `name` field inside it. For example, `conditions/control.yaml` must start with:

```yaml
name: control
```

This name is what you pass to `slumber study run --condition control`. If the two don't match, loading the study fails:

```text
Condition file error: /path/to/my-study/conditions/control.yaml
  name: 'no-stimulation' does not match the file name 'control'
```

## Add a phase

A phase is one stage of the session, such as *setup* or *sleep*. Phases don't have to run in a fixed order, and the same phase can run more than once (for example, in [Sleep and wake loop](#sleep-and-wake-loop)).

Each phase has an `id`, a `layout` and at least one activity (under `activities`):

```yaml
phases:
  - id: setup
    title: Setup
    layout:
      type: stepper
    activities:
      - ...
```

- **`id`** must be unique within the condition. Handlers and `entry` refer to phases by this id.
- **`title`** is optional and defaults to the `id`.
- **`layout`** decides how the phase's activities are arranged on screen.

### Choosing a layout

There are two types of layout: `stepper` and `hub`.

| Use | When |
|-----|------|
| `stepper` | The participant goes through one or more screens in order, with **Previous**, **Next** and **Complete** buttons. |
| `hub` | A single activity fills the screen, with no navigation. Give a hub phase exactly one activity; any others are ignored. |

The button labels and other stepper settings come from the study's `ui.settings.layouts.stepper` defaults. A phase can override them under `layout.settings`, for example to let the participant move on without finishing each step:

```yaml
    layout:
      type: stepper
      settings:
        allow_skip: true
```

See [Participant UI](participant-ui.md) for the study-wide defaults and the [UI reference](../reference/ui.md) for every setting.

## Add activities

An activity is one thing the participant sees or does. Each activity has an `id` (unique within its phase), a `type`, and optional `title` and `settings`. In a stepper, the `title` is shown in the activity list.

The current SLUMBER version has two built-in activity types, `instruction` and `sleep`:

### `instruction`: show a text

Shows Markdown text. `content` is either a path to a Markdown file or the text itself:

```yaml
    activities:
      - id: welcome
        title: Welcome
        type: instruction
        settings: { content: "{assets_dir}/instructions/intro.md" }
```

Put the files in the study's `assets/` folder and refer to them with `{assets_dir}/…`. A bare file name such as `content: intro.md` is **not** looked up anywhere: it is shown as the literal text "intro.md". See [Paths and placeholders](paths-and-placeholders.md#which-values-are-treated-as-paths).

The Markdown can also contain images, for example `![Headband]({assets_dir}/images/headband.png)`. See [Images in instruction texts](../reference/ui.md#images-in-instruction-texts) for the options.

An instruction counts as finished as soon as it is shown.

### `sleep`: the night screen

Shows a main button that toggles between going to sleep (**Going to Sleep**) and waking up (**I'm Awake**), and a button to end the session in the morning. You can change their labels:

```yaml
    activities:
      - id: sleep
        type: sleep
        settings:
          sleep_button: "Going to Sleep"
          wake_button: "I'm Awake"
          end_button: "End Session"
```

A button can also set its style and the question it asks; see [Change the sleep buttons](participant-ui.md#change-the-sleep-buttons).

A sleep activity never finishes by itself. Pressing a button sends an event (`marked_asleep`, `marked_awake` or `end_sleep`), and you decide what happens next with handlers, as described below.

## Decide what happens next: `on:` handlers

Phases don't advance on their own. You connect **events** to **actions** with `on:` handlers:

```yaml
    on:
      - event: phase_completed
        do:
          - start_pipeline: main
          - start_phase: sleep
```

This reads as: "when the setup phase is completed, start the `main` pipeline, then go to the `sleep` phase". The actions in `do:` run in the order you write them.

### Which events you can handle

| Event | Sent when | Put the handler on |
|-------|-----------|--------------------|
| `phase_completed` | The participant presses **Complete** at the end of a `stepper` phase | The phase |
| `marked_asleep` | The participant presses the sleep button of a `sleep` activity | The sleep activity (or its phase) |
| `marked_awake` | The participant presses the wake button of a `sleep` activity | The sleep activity (or its phase) |
| `end_sleep` | The participant presses the end button of a `sleep` activity | The sleep activity (or its phase) |

A `hub` phase never sends `phase_completed`, so it must be left through an event from its activity.

### Which actions you can use

| Action | Effect |
|--------|--------|
| `start_phase: <phase id>` | Leave the current phase and start another one. |
| `start_pipeline: <pipeline id>` | Start a pipeline in the background. |
| `stop_pipeline: <pipeline id>` | Stop a running pipeline. |
| `end_run` | End the run. Actions after it are skipped. |

A short action can be written on one line: `do: [{ start_phase: awakening }]`.

For the exact rules (which handlers run when both the activity and the phase handle an event, and in what order), see [Events, handlers and actions](../concepts/run-lifecycle.md#events-handlers-and-actions).

## Add a pipeline

A pipeline records data in the background while the phases run. It is a list of **units** (processing steps) and the **connections** between them. The built-in `clock` and `jsonl_writer` units are for testing: `clock` produces dummy samples (`rate` per second), and `jsonl_writer` writes what it receives to a file.

```yaml
pipelines:
  - id: main
    units:
      - id: clock
        type: clock
        settings: { rate: 1.0 }
      - id: store
        type: jsonl_writer
        settings: { path: "{run_dir}/clock.jsonl" }
    connections:
      - [clock/OUTPUT, store/INPUT]
```

- Each connection goes from `<unit id>/<output stream>` to `<unit id>/<input stream>`.
- Use `{run_dir}` for output files so each run writes into its own folder.
- A pipeline does nothing until a `start_pipeline` action starts it. It keeps running across phase changes until a `stop_pipeline` action or the end of the run.

## Common patterns

### Start recording when the participant goes to sleep

Start the pipeline in the same handler that moves to the sleep phase, so recording begins exactly when the sleep screen appears:

```yaml
    on:
      - event: phase_completed
        do:
          - start_pipeline: main
          - start_phase: sleep
```

### Hide the header and footer during sleep

Add a `frame` override to the phase. It applies only while that phase is active:

```yaml
  - id: sleep
    frame:
      header: false
      footer: false
```

### Sleep and wake loop

Send the participant to an awakening phase when they press the wake button, and back to sleep when they finish it. This repeats for every awakening during the night:

```yaml
  - id: sleep
    layout:
      type: hub
    activities:
      - id: sleep
        type: sleep
        on:
          - event: marked_awake
            do: [{ start_phase: awakening }]

  - id: awakening
    layout:
      type: stepper
    activities:
      - id: awake
        type: instruction
        settings: { content: "{assets_dir}/instructions/awakening.md" }
    on:
      - event: phase_completed
        do: [{ start_phase: sleep }]
```

### End the session

Stop the recording before showing the morning screen, then end the run when the participant completes it:

```yaml
          - event: end_sleep
            do:
              - stop_pipeline: main
              - start_phase: morning

  ...

  - id: morning
    ...
    on:
      - event: phase_completed
        do: [{ end_run }]
```

## Validate as you go

Run the validator after each change:

```bash
slumber study validate --study-dir my-study
```

It reports mistakes before a participant ever sees them: a file name that doesn't match `name`, an `entry` or `start_phase` that isn't a phase id, a `start_pipeline` that isn't a pipeline id, a connection to a unit that doesn't exist, an unknown `type`, and settings with the wrong type. See [Validating a study](validating-a-study.md) for how to read the errors.

!!! warning "Misspelled settings are not reported"
    An activity or unit setting with a misspelled name, such as `wake_buton` or `rat`, is ignored and the default is used. For activities, check the names against the [UI reference](../reference/ui.md#activity-settings).

To check that the condition runs from start to finish, run it headless:

```bash
slumber study run --study-dir my-study --condition demo --ui headless
```

A headless run never presses the wake button, so the sleep and wake loop is only tested in the GUI. See [Running a study](running-a-study.md).

## The complete example

Putting all of this together gives a complete condition, `conditions/demo.yaml`:

```yaml
name: demo
entry: setup

phases:
  - id: setup
    title: Setup
    layout:
      type: stepper
      settings:
        allow_skip: true
    activities:
      - id: welcome
        title: Welcome
        type: instruction
        settings: { content: "{assets_dir}/instructions/intro.md" }
    on:
      - event: phase_completed
        do:
          - start_pipeline: main
          - start_phase: sleep

  - id: sleep
    title: Sleep
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

  - id: awakening
    title: Awakening
    layout:
      type: stepper
    activities:
      - id: awake
        title: You're awake
        type: instruction
        settings: { content: "{assets_dir}/instructions/awakening.md" }
    on:
      - event: phase_completed
        do: [{ start_phase: sleep }]

  - id: morning
    title: Morning
    layout:
      type: stepper
    activities:
      - id: complete
        title: Session complete
        type: instruction
        settings: { content: "{assets_dir}/instructions/morning.md" }
    on:
      - event: phase_completed
        do: [{ end_run }]

pipelines:
  - id: main
    units:
      - id: clock
        type: clock
        settings: { rate: 1.0 }
      - id: store
        type: jsonl_writer
        settings: { path: "{run_dir}/clock.jsonl" }
    connections:
      - [clock/OUTPUT, store/INPUT]
```
