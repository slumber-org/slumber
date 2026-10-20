# Run lifecycle

This page explains what happens while a condition runs: how the RunEngine moves from phase to phase, how activities report back, and how `on:` handlers decide what happens next. For every field you can write in the YAML, see the [Configuration reference](../reference/configuration.md).

## From start to finish

When you run `slumber study run --condition <name>`:

1. **The study is loaded and validated:** the manifest, every condition file, and every plugin `type` it uses.
2. **The run folder is created** from `runs.directory` and `runs.layout`, and `run.json` is written into it with the study, condition and run ids and the start time.
3. **Logging starts** with the handlers from `study.logging`.
4. **The UI starts**: `gui` or `headless`, from `ui.type` in `study.yaml` or from `--ui` if you passed it. With `--ui headless`, all GUI settings are ignored. The GUI applies the theme and mounts the AppFrame once for the whole run.
5. **The entry phase starts.** From here on, the run is driven by events and actions.
6. **The run ends** when an `end_run` action runs: pipelines are stopped, the current phase is unmounted, and the UI shuts down. If the UI stops on its own before that (for example, headless has nothing left to do), the engine ends the run the same way.

## Starting a phase

Each `start_phase` (including the first one, for the entry phase) does the following:

1. Unmounts the previous phase, if there is one.
2. Applies the frame for this phase: the study's `ui.settings.frame`, with the phase's `frame` merged on top. This is how a sleep phase hides the header and footer.
3. Creates the phase's layout and activities, with their settings validated and their paths and placeholders resolved (see [Paths and placeholders](../user-guide/paths-and-placeholders.md)).
4. Mounts the layout, which mounts the activities.

A phase stays active until an action starts another phase or ends the run. Phases don't advance on their own.

## How activities signal

An activity can report two different things, through the host object it receives when it is mounted (see the [Activity contract](../reference/plugins.md#activity-slumberactivities)):

| Call | Goes to | Means |
|------|---------|-------|
| `complete()` | The layout | "This step is finished." |
| `emit(name)` | The RunEngine | "This study event happened", for example `marked_awake`. |

The layout, in turn, sends one event of its own:

| Event | Goes to | Means |
|-------|---------|-------|
| `phase_completed` | The RunEngine | The layout decided the whole phase is done. |

```text
Activity → host.complete()  → Layout → (when the phase is done) phase_completed → RunEngine
Activity → host.emit(name)  → RunEngine
```

**Why `complete()` is not just another event:** finishing a step is the layout's business. If every finished step were a study event, `on:` handlers would fire for each step, and "the phase is complete" would be ambiguous. Keeping `complete()` with the layout means the RunEngine only hears about the phase as a whole (`phase_completed`) and about events that matter to the study (`emit`).

Activities decide *when* to call these, not what they mean for the study. For example, `instruction` calls `complete()` as soon as it is shown, and `sleep` only emits `marked_awake` or `end_sleep` when the participant presses a button.

## When a phase is completed

`phase_completed` depends on the layout:

- **`stepper`:** sent when the participant presses the **Complete** button on the last step. That button is enabled once every activity in the phase has called `complete()`, or straight away if the phase sets `allow_skip: true`.
- **`hub`:** never sent. A hub phase is left through an event emitted by its activity (for example, the sleep activity's `end_sleep`).
- **headless:** layouts are not used. If every activity calls `complete()` as soon as it is mounted, `phase_completed` is sent immediately. See [gui and headless](#gui-and-headless).

## Events, handlers and actions

A handler connects an event to a list of actions:

```yaml
on:
  - event: phase_completed
    do:
      - start_pipeline: main
      - start_phase: sleep
```

Handlers can be written on a **phase** or on an **activity**. When an event arrives, the RunEngine collects the matching handlers:

1. If an activity emitted the event, that activity's own `on:` handlers come first.
2. Then the current phase's `on:` handlers.

Every matching handler runs, not just the first one. `phase_completed` comes from the layout, not from an activity, so only phase handlers can react to it. An event with no matching handler is ignored.

The collected actions run **in the order they are written**:

| Action | Effect |
|--------|--------|
| `start_phase: <id>` | Unmount the current phase and start `<id>`. |
| `start_pipeline: <id>` | Start the pipeline `<id>` in the background. |
| `stop_pipeline: <id>` | Stop the pipeline `<id>`. |
| `end_run` | End the run. Any actions after it are skipped. |

Because actions run in order, `[stop_pipeline: main, start_phase: morning]` stops recording before the morning phase appears.

## Open-ended activities

Some activities never call `complete()`, so a phase built around them is normally left through events instead of `phase_completed`. `sleep` is the example in 0.1: it stays on screen until the participant presses **I'm Awake** (which emits `marked_awake`) or **End Session** (which emits `end_sleep`). The phase is left through handlers for those events: a `start_phase` or `end_run` action unmounts the sleep activity and moves on.

For example, a sleep phase with a wake-up loop:

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
        - event: end_sleep
          do:
            - stop_pipeline: main
            - start_phase: morning
```

- **I'm Awake** → the `awakening` phase starts. When the participant finishes it, its `phase_completed` handler starts `sleep` again. This loop repeats for every awakening during the night.
- **End Session** → two actions run in order: `stop_pipeline: main` stops the recording, then `start_phase: morning` shows the morning screen.

Pipelines and phases are independent: a pipeline is a background process, not part of any phase, and it keeps running across phase changes until a `stop_pipeline` action stops it or the run ends. Here, `main` is the id of a pipeline defined under `pipelines:` in the condition. It would typically be started when the participant goes to sleep, and keeps recording through the whole sleep and awakening loop.

## gui and headless

Both UIs use the same RunEngine, handlers and actions. They differ in how activities are presented and who triggers events:

| | `gui` | `headless` |
|---|---|---|
| Window | Browser window with AppFrame | None |
| Layouts | `stepper` and `hub` arrange activities | Not used; each activity's `mount()` still runs, with nothing to draw into |
| `phase_completed` | When the participant presses **Complete** in a stepper | Immediately, if every activity completes as soon as it is mounted |
| `sleep` | Waits for the wake or end button | Emits `end_sleep` shortly after mounting |
| Frame overrides | Show or hide the header and footer | Ignored |

Mounting an activity means calling its `mount()` method, not only drawing it. In headless, every activity in the phase is still mounted, one after another, but its host has no screen area to draw into. The activity skips the drawing and runs the rest of its logic: `instruction` still loads its content file and calls `complete()`.

So a headless run walks the main path of a condition without anyone at the keyboard, which is what makes it useful for testing and CI. It never emits `marked_awake`, so branches that depend on the participant waking up are only exercised in the GUI.
