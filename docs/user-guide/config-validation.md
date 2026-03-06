# Config loading and validation

This page describes how the framework discovers a study folder, loads the manifest and condition files, and how validation errors are reported.

## Study discovery

The study folder is discovered in one of two ways:

1. **Current directory** — When you run a command (e.g. `slumber study validate`) **from inside** a study folder, the framework looks for `study.yaml` in the current working directory. If present, that directory is the study folder.
2. **Explicit path** — You can pass `--study-dir <path>` to point to a study folder from anywhere. The path must be a directory that contains `study.yaml`.

If no study folder is found (no `study.yaml` in cwd and no valid `--study-dir`), commands that need a study will exit with an error and a short hint.

**Typical workflow:** After `slumber study init`, `cd` into the study folder and run subsequent commands from there. Use `--study-dir` when scripting or when you are not in the study directory.

## Validate command: `slumber study validate`

Validates the study manifest and all condition files in the study folder.

```bash
# From inside the study folder
slumber study validate

# From anywhere, with explicit path
slumber study validate --study-dir /path/to/my-study
```

**Behavior:**

- Discovers the study folder (cwd or `--study-dir`).
- Loads and validates `study.yaml` against the Study schema.
- Loads every `.yaml` and `.yml` file in the manifest’s `conditions_dir` (default `conditions/`) and validates each as a Condition.
- On success: prints study name, study ID, and the list of condition names.
- On failure: prints a path-specific error (see [Error format](#error-format)) and exits with code 1.

### Options

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Path to the study folder. If omitted, the current directory is used. |

## Error format

Validation errors are printed in a consistent, path-specific form so you can fix the right file.

**Study manifest errors** (invalid `study.yaml`):

```text
Study manifest error: /path/to/study/study.yaml
  name: Field required
```

**Condition file errors** (invalid YAML in `conditions/*.yaml`):

```text
Condition file error: /path/to/study/conditions/control.yaml
  procedures: Field required
  dag: Field required
```

Each line after the first lists a field path (or location) and the validation message. Multiple errors for the same file are listed together. This format is produced by the config layer when Pydantic validation fails; the same formatting is used by the `validate` command and can be used programmatically via `slumber.utils.errors.format_validation_error()` or `slumber.config.format_validation_error()`.

## Loading config programmatically

You can load and validate config without running the CLI:

- **`slumber.config.discover_study_dir(study_dir=None)`** — Returns the study directory `Path` if found, else `None`. When `study_dir` is omitted, uses the current working directory.
- **`slumber.config.load_study(study_dir)`** — Loads the manifest and returns a `Study` with its path set to `study_dir`. Use **`study.conditions`** to load and validate condition YAML files (raises `FileNotFoundError` or `ValueError` with path if invalid).
- **`slumber.config.load_study_conditions(study, study_dir)`** — Low-level: loads and returns the list of `Condition` from `study_dir / study.conditions_dir`. Prefer **`study.conditions`** when the study was returned from `load_study()`.
- **`slumber.config.load_and_validate(path, model)`** — Loads YAML from `path` and validates as the given Pydantic model (e.g. `Study`, `Condition`). From `slumber.utils.yaml`; also exported from `slumber.config`. For a single `study.yaml`: `load_and_validate(manifest_path, Study)`. For a single condition file: `load_and_validate(condition_path, Condition)`.
- **`slumber.config.init_study(base_dir, study_id, ...)`** — Create a new study folder (manifest, conditions/, assets/). From `slumber.config.study`; also exported from `slumber.config`.
- **`slumber.schemas.load_conditions_from_dir(conditions_dir)`** — Low-level: load and validate all condition YAML files from a directory path; returns `list[Condition]`. Also exported from `slumber.config`.
- **`slumber.config.format_validation_error(error, path=..., prefix=...)`** — Formats a Pydantic `ValidationError` with an optional file path for clear, path-specific messages. From `slumber.utils.errors`; also exported from `slumber.config`.

All paths are interpreted as in the filesystem; the study manifest’s `conditions_dir` is relative to the study directory.
