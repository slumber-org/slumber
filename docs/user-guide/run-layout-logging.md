# Run directory layout and logging

Each run produces a dedicated output directory. SLUMBER creates this directory automatically using a layout template from `study.yaml`, then configures loguru file handlers (also from `study.yaml`) so that all log output for that run lands in the right place.

## Run directory layout

### Configuration

In `study.yaml`, the `runs` section controls where output is stored:

```yaml
runs:
  base_directory: runs          # relative to the study folder
  layout: sub-{participant_id}/ses-{session_id}/run-{run_id}
```

`base_directory` is the root folder for all run output. `layout` is a path template expanded with the run context at start time. The final run directory is:

```
<study_dir>/<base_directory>/<expanded_layout>/
```

For example, with the defaults above and `participant_id=sub-001`, `session_id=ses-01`, `run_id=20241001T220000`:

```
my-study/runs/sub-sub-001/ses-ses-01/run-20241001T220000/
```

### Supported placeholders

| Placeholder | Description |
|-------------|-------------|
| `{study_id}` | Study identifier from `study.yaml`. |
| `{participant_id}` | Participant identifier for this run. |
| `{session_id}` | Session identifier for this run. |
| `{run_id}` | Unique run identifier (e.g. a timestamp or UUID). |
| `{condition_id}` | Condition identifier for this run. |

### Python API

```python
from slumber.runtime import RunContext, resolve_run_dir, create_run_dir
from slumber.config import load_study

study = load_study(study_dir)
ctx = RunContext(
    study_id=study.study_id,
    participant_id="sub-001",
    session_id="ses-01",
    run_id="20241001T220000",
    condition_id="control",
)

# Compute the path without creating it:
run_dir = resolve_run_dir(study, ctx, study_dir)

# Or create the directory immediately:
run_dir = create_run_dir(study, ctx, study_dir)
```

## Run logging

### Configuration

The `logging` section of `study.yaml` defines loguru handlers applied at run start. Each entry in `handlers` is passed as keyword arguments to `loguru.logger.add()`:

```yaml
logging:
  level: INFO
  handlers:
    - sink: "{run_id}.log"
      level: DEBUG
      rotation: "10 MB"
    - sink: "{run_dir}/errors.log"
      level: ERROR
```

If a handler does not include a `level` key, the top-level `logging.level` is used as the default.

### Sink path placeholders

All run-context placeholders (`{study_id}`, `{participant_id}`, `{session_id}`, `{run_id}`, `{condition_id}`) are available in sink strings, plus `{run_dir}` (the absolute path to the run directory as a string).

Relative sink paths are resolved relative to the run directory. Absolute paths are used as-is.

| Example sink | Resolved path |
|---|---|
| `"{run_id}.log"` | `<run_dir>/<run_id>.log` |
| `"errors.log"` | `<run_dir>/errors.log` |
| `"{run_dir}/out.log"` | `<run_dir>/out.log` |
| `"/var/log/slumber/{run_id}.log"` | `/var/log/slumber/<run_id>.log` |

### Python API

```python
from slumber.runtime import configure_run_logging
from loguru import logger

handler_ids = configure_run_logging(study, ctx, run_dir)

# ... run executes ...

# Remove handlers when the run ends:
for hid in handler_ids:
    logger.remove(hid)
```

`configure_run_logging` returns the list of loguru handler IDs. Store them and call `logger.remove()` on each to deregister handlers after the run completes.

### Any loguru sink is supported

Because handler config is passed directly to `logger.add()`, you can use any sink type that loguru supports — file paths, `sys.stderr`, a callable, or a third-party sink — as long as the sink value is serialisable in YAML (file path strings are the most common case).

See the [loguru documentation](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add) for the full list of `logger.add()` parameters.
