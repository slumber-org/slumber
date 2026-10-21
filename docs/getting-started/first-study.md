# Your first study

This walkthrough runs an example sleep study from start to finish, as a participant would see it. It takes about 10 minutes.

You need SLUMBER installed from source, including the GUI dependency (see [Installation](installation.md)).

Open a terminal in the `slumber` folder that was created when you cloned the repository during installation:

```bash
cd path/to/slumber
```

All commands on this page use paths that start from this folder.

## 1. Look at the study

The example is in `examples/sleep-study/`:

```text
examples/sleep-study/
├── study.yaml                   the study manifest
├── conditions/
│   ├── control.yaml
│   └── relaxation.yaml
├── assets/
│   └── instructions/            texts shown to the participant
│       ├── welcome.md
│       ├── relaxation.md
│       ├── before-sleep.md
│       ├── awakening.md
│       └── morning.md
└── runs/                        output of each run
```

It is a basic home sleep study with two conditions:

- **`relaxation`**: the participant does a short breathing exercise before going to sleep.
- **`control`**: the participant goes to sleep without the exercise.

Open both files in `conditions/` side by side. They are the same except for one step in the evening:

```yaml
      - id: relaxation
        title: Relaxation exercise
        type: instruction
        settings: { content: "{assets_dir}/instructions/relaxation.md" }
```

In both conditions, the night goes like this: the participant reads a welcome text and a few instructions for going to sleep, then the recording starts and the sleep screen appears. The participant can report waking up during the night, and ends the session in the morning. There is no sleep device in this example: during sleep, the recording contains dummy samples instead of physiological data. Everything the participant does on screen is logged as in a real study.

For how a study, its conditions and the recording fit together, see the [Concepts overview](../concepts/overview.md). To write your own condition file, see [Writing conditions](../user-guide/writing-conditions.md).

## 2. Validate the study

```bash
uv run slumber study validate --study-dir examples/sleep-study
```

```text
Study: Sleep Study (sleep-study)
Conditions: 2
  - control
  - relaxation
```

If validation reports an error, [Validating a study](../user-guide/validating-a-study.md) explains how to read it.

## 3. Run it as a participant

```bash
uv run slumber study run --study-dir examples/sleep-study --condition relaxation
```

A browser window opens. Go through the night:

1. **Evening:** read the three steps with **Next**, then press **Complete**.
2. **Sleep:** the header and footer disappear and the sleep screen appears. Press **Going to Sleep**, wait a few seconds, then press **I'm Awake**.
3. **You're awake:** press **Complete** to go back to sleep.
4. **Sleep:** press **End Session** and confirm.
5. **Good morning:** press **Complete**.

The run ends. Near the end of the terminal output, this line shows where the run was saved:

```text
Run complete: …/examples/sleep-study/runs/run-<run id>
```

!!! tip "Testing without a window"
    To test a condition quickly without opening a window, add `--ui headless` to the run command:

    ```bash
    uv run slumber study run --study-dir examples/sleep-study --condition relaxation --ui headless
    ```

    The whole night then runs in about a second. See [gui and headless](../concepts/run-lifecycle.md#gui-and-headless).

To change what the participant sees, such as button labels or the logo, see [Participant UI](../user-guide/participant-ui.md). For how a run moves from phase to phase, see [Run lifecycle](../concepts/run-lifecycle.md).

## 4. Look at the output

Open `examples/sleep-study/runs/`. There is one folder per run. Your run's folder contains:

| File | Contents |
|------|----------|
| `run.json` | Study, condition, run id and start time |
| `run.log` | Every phase and step of the run, with timestamps |
| `recording.jsonl` | Dummy samples recorded during sleep, one per second. A real study would store device data here. |

To change where runs are saved or what is logged, see [Run output and logging](../user-guide/run-output-and-logging.md).

## 5. Optional: run the other condition

Run the `control` condition:

```bash
uv run slumber study run --study-dir examples/sleep-study --condition control
```

This time the evening has two steps instead of three: the relaxation exercise is missing, because that is the only difference between the two conditions. Open the new `run.log` to see the difference.

You can also change a text shown by an `instruction` activity, for example `assets/instructions/welcome.md`, and run again to see it on screen.

## Next steps

To create your own study, continue with [Study setup](../user-guide/study-setup.md).
