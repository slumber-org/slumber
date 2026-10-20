# Running a study

This page shows how to run a condition of your study, for a participant or to test it, and how to check the result.

## Run a condition

```bash
slumber study run --study-dir path/to/my-study --condition relaxation
```

`--condition` takes the condition's `name`. For all options, see the [CLI reference](../reference/cli.md#slumber-study-run).

Every run gets its own new folder under `runs/`, so running the same condition again never overwrites an earlier run.

## GUI or headless

Whether a run opens the participant window depends on `ui.type` in `study.yaml`:

- **`gui`** opens the participant window in the browser. Use it for real sessions and to see what the participant sees. See [Participant UI](participant-ui.md).
- **`headless`** runs without a window and finishes in seconds. Use it to check that a condition runs from start to finish after you change it.

To use the other one for a single run, add `--ui`:

```bash
slumber study run --study-dir path/to/my-study --condition relaxation --ui headless
```

For how the two differ, see [gui and headless](../concepts/run-lifecycle.md#gui-and-headless).

## Stop a run early

Press **Ctrl+C** in the terminal where the run started. The run stops immediately, including any recording, and everything recorded until then stays in the run folder.

## Check that the run succeeded

When a run ends normally, the terminal shows where it was saved:

```text
Run complete: path/to/my-study/runs/run-<run id>
```

If something goes wrong, it shows `Run failed:` and the reason instead.

A run that failed or was stopped early still has a run folder, with `run.json` and whatever was recorded until then. If your study writes a log file into the run folder, you can tell these runs apart: only a complete run's log ends with a `Run completed` line.

For what each file in the run folder contains, see [Run output and logging](run-output-and-logging.md).

For what SLUMBER does step by step during a run, see [Run lifecycle](../concepts/run-lifecycle.md#from-start-to-finish).
