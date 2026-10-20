# Running a study

`slumber study run` executes one condition from a study package on disk. It creates a run directory, configures logging, starts the UI (`gui` or `headless`), and drives phases and pipelines through the RunEngine until `end_run`.

Local run does **not** require auth, scheduling, or a remote backend.

## Quick start

```bash
slumber study run --study-dir path/to/my-study --condition demo

# Same condition, no browser (CI / headless)
slumber study run --study-dir path/to/my-study --condition demo --ui headless
```

`--condition` takes the condition's `name`. For all options, see the [CLI reference](../reference/cli.md#slumber-study-run).

`run_id` is a new UUID. Set `PARTICIPANT_ID` only if your `runs.layout` uses `{participant_id}`.

## What happens during a run

1. **Study is loaded** — manifest and conditions validated; plugins resolved.
2. **UI override applied** (optional) — `--ui` replaces `study.ui.type` (headless clears GUI-only settings).
3. **Run directory is created** — from `study.runs.directory` + `study.runs.layout`.
4. **`run.json` is written** with study/condition/run ids and `started_at`.
5. **Run logging is applied** — handlers from `study.logging`.
6. **UI starts** — GUI mounts AppFrame, or headless drives the same engine without a window.
7. **`start_phase(entry)`** — layout + activities; events run `do` actions (`start_pipeline`, `start_phase`, `stop_pipeline`, `end_run`).
8. **`end_run`** — stop pipelines, unmount, finalize logging.

## Demo walkthrough

The repo ships `examples/demo/` (setup → clock pipeline → sleep → awakening loop → morning → `end_run`):

```bash
# GUI (requires slumber[nicegui]; study.yaml defaults to gui)
uv run slumber study run --study-dir examples/demo --condition demo

# Headless
uv run slumber study run --study-dir examples/demo --condition demo --ui headless
```

Headless finishes without a browser; see [gui and headless](../concepts/run-lifecycle.md#gui-and-headless) for how. Expect `runs/run-<uuid>/run.json` and `clock.jsonl`.

## First study from scratch

```bash
# 1. Create the study folder
slumber study init --base-dir . --study-id my-study --name "My Study"

# 2. Write a condition in my-study/conditions/demo.yaml
#    (see Writing conditions, or copy examples/demo/conditions/demo.yaml)

# 3. Validate
slumber study validate --study-dir my-study

# 4. Run headless
slumber study run --study-dir my-study --condition demo --ui headless
```

See [Run output and logging](run-output-and-logging.md) and [Participant UI](nicegui-ui.md).
