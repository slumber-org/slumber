# Run output and logging

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

For the placeholders allowed in `runs.layout`, see the [Configuration reference](../reference/configuration.md#study-manifest-studyyaml).

## Run logging

### Configuration

```yaml
logging:
  level: INFO
  handlers:
    - sink: "{run_dir}/{run_id}.log"
      level: DEBUG
      rotation: "10 MB"
    - sink: "{run_dir}/errors.log"
      level: ERROR
```

Each `handlers` entry is kwargs for `loguru.logger.add()`. If a handler omits `level`, the top-level `logging.level` is used.

### Sink path placeholders

Run-context keys plus `{run_dir}` (absolute run directory). Relative sinks resolve against the study root; absolute paths are used as-is. Use `{run_dir}/…` to write logs inside the run directory.

| Example sink | Resolved path |
|---|---|
| `"{run_id}.log"` | `<study_dir>/<run_id>.log` |
| `"errors.log"` | `<study_dir>/errors.log` |
| `"{run_dir}/out.log"` | `<run_dir>/out.log` |

Any sink type loguru supports can appear in YAML when serialisable (file path strings are typical).
