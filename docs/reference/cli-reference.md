# CLI reference

All commands are invoked as `slumber <command> [options]`. Use `slumber --help` or `slumber <command> --help` for context-sensitive help.

Core 0.1 ships `study` and `doctor`. Optional packages may attach more groups via the `slumber.cli` entry-point group.

## Global options

| Option | Description |
|--------|-------------|
| `--env`, `-e` PATH | Load a specific environment file (overrides auto-discovered `.env`). |
| `--verbose`, `-v` | Enable verbose (DEBUG) logging. |
| `--version` | Show the installed slumber version and exit. |
| `--help` | Show help and exit. |

```bash
slumber --verbose study validate --study-dir .
```

## slumber doctor

Check local environment variables and optional dependencies.

```bash
slumber doctor
```

| Symbol | Meaning |
|--------|---------|
| ✓ | OK / set / installed |
| ✗ | Failed / missing (required) |
| — | Not set / not installed (optional) |

**Environment**

| Variable | Required | Purpose |
|----------|----------|---------|
| `STUDY_DIR` | No | Default study folder for study commands. |
| `PARTICIPANT_ID` | No | Used when `runs.layout` includes `{participant_id}`. |

**Dependencies**

| Package | Required | Notes |
|---------|----------|-------|
| `ezmsg` | Yes | Processing backbone. |
| `nicegui` | No | GUI participant UI (`uv sync --extra nicegui`). |

Exit `0` if all required checks pass; `1` otherwise.

## slumber study

### slumber study init

```bash
slumber study init --base-dir . --study-id my-study --name "My Study"
```

| Option | Default | Description |
|--------|---------|-------------|
| `--base-dir`, `-b` | `.` | Parent directory. |
| `--study-id`, `-s` | `new_study` | Study identifier (folder name). |
| `--name`, `-n` | study-id | Written as `study_name` in `study.yaml`. |
| `--no-env-example` | — | Skip creating `.env`. |
| `--no-gitignore` | — | Skip creating `.gitignore`. |

Creates `study.yaml`, empty `conditions/`, `assets/`, and `runs/`. Default UI is `headless`. Does not register a remote study.

See [Study setup](../user-guide/study-setup.md).

### slumber study validate

```bash
slumber study validate --study-dir path/to/my-study
```

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Study folder. Also read from `STUDY_DIR`. |

Validates the manifest, conditions, and plugins. See [Config loading and validation](../user-guide/config-validation.md).

### slumber study run

```bash
slumber study run --study-dir path/to/my-study --condition demo
slumber study run --study-dir path/to/my-study --condition demo --ui headless
```

| Option | Default | Description |
|--------|---------|-------------|
| `--study-dir`, `-d` | — | Study folder. Also read from `STUDY_DIR`. |
| `--condition`, `-c` | — | Condition name. Required. |
| `--ui` | — | Override `study.ui.type` (`gui` or `headless`). |

Local file-based run: new UUID `run_id`, no remote backend. See [Running a study](../user-guide/study-run.md).
