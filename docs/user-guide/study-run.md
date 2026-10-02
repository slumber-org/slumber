# Running a study

`slumber study run` executes one condition from a study package on disk. It creates a run directory, configures logging, starts the UI (`gui` or `headless`), and drives phases and pipelines through the RunEngine until `end_run`.

Local run does **not** require auth, scheduling, or a remote backend.

## Quick start

```bash
slumber study run --study-dir path/to/my-study --condition demo

# Same condition, no browser (CI / headless)
slumber study run --study-dir path/to/my-study --condition demo --ui headless
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--study-dir`, `-d` | — | Path to the study folder. Also read from `STUDY_DIR`. |
| `--condition`, `-c` | — | Condition name (from loaded YAML). Required. |
| `--ui` | — | Override `study.ui.type` for this run (`gui` or `headless`). |

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

Headless completes without a browser: instruction activities auto-complete; sleep emits `end_sleep` on mount. Expect `runs/run-<uuid>/run.json` and `clock.jsonl`.

## First study from scratch

```bash
# 1. Create the study folder
slumber study init --base-dir . --study-id my-study --name "My Study"

# 2. Add a condition (copy or adapt examples/demo/conditions/demo.yaml)
#    under my-study/conditions/

# 3. Validate
slumber study validate --study-dir my-study

# 4. Run headless
slumber study run --study-dir my-study --condition demo --ui headless
```

See [Run layout and logging](run-layout-logging.md) and [Participant UI](nicegui-ui.md).
