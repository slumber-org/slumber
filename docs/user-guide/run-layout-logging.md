# Run directory layout and logging

Each run produces a dedicated output directory. SLUMBER creates it from `study.runs`, writes `run.json`, then configures loguru handlers from `study.logging`.

## Run directory layout

### Configuration

```yaml
runs:
  directory: runs
  layout: run-{run_id}
```

Final path: `<study_dir>/<directory>/<expanded_layout>/`.

Default layout yields:

```
my-study/runs/run-<uuid>/
├── run.json
└── (artifacts and log files)
```

### Supported placeholders (`runs.layout`)

| Placeholder | Description |
|-------------|-------------|
| `{study_id}` | Study identifier from `study.yaml`. |
| `{run_id}` | Unique run identifier (UUID for local runs). |
| `{condition_id}` | Condition name for this run. |
| `{participant_id}` | Optional; set `PARTICIPANT_ID` if your layout uses it. |
| `{session_id}` | Optional; unused by local core runs. |

### Python API

```python
from slumber.run import RunContext, resolve_run_dir, create_run_dir
from slumber.config import load_study

study = load_study(study_dir)
ctx = RunContext(
    study_id=study.study_id,
    run_id="…",
    condition_id="demo",
)

run_dir = resolve_run_dir(study, ctx, study_dir)
run_dir = create_run_dir(study, ctx, study_dir)
```

## Run logging

### Configuration

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

Each `handlers` entry is kwargs for `loguru.logger.add()`. If a handler omits `level`, the top-level `logging.level` is used.

### Sink path placeholders

Run-context keys plus `{run_dir}` (absolute run directory). Relative sinks resolve under the run directory; absolute paths are used as-is.

| Example sink | Resolved path |
|---|---|
| `"{run_id}.log"` | `<run_dir>/<run_id>.log` |
| `"errors.log"` | `<run_dir>/errors.log` |
| `"{run_dir}/out.log"` | `<run_dir>/out.log` |

### Python API

```python
from slumber.run import configure_run_logging
from loguru import logger

handler_ids = configure_run_logging(study, ctx, run_dir, placeholders=…)

for hid in handler_ids:
    logger.remove(hid)
```

Any sink type loguru supports can appear in YAML when serialisable (file path strings are typical).
