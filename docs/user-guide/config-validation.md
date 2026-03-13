# Config loading and validation

This page describes how the framework discovers a study folder, loads the manifest and condition files, and how validation errors are reported.

## Study discovery

For commands that accept a study folder:

1. **Explicit path** — Prefer passing `--study-dir <path>` to point to a study folder. The path must be a directory that contains `study.yaml`.
2. **Environment** — You can set `STUDY_DIR` to the study folder path; the CLI uses it when `--study-dir` is not passed (Typer envvar).

**`slumber study validate`** validates a single study folder. In practice you will either:

- run it from inside the study folder and pass `--study-dir .`, or
- set `STUDY_DIR=/path/to/my-study` and run `slumber study validate`.

Other researcher commands (`participant`, `session`, `db`) do not require a study directory; when they need a study (e.g. participant create, session create/list), they use `--study-id` or `STUDY_ID`.

## Validate command: `slumber study validate`

Validates the study manifest and all condition files in the study folder.

```bash
# With explicit path
slumber study validate --study-dir /path/to/my-study

# Or set STUDY_DIR
export STUDY_DIR=/path/to/my-study
slumber study validate
```

**Behavior:**

- Resolves study folder from `--study-dir` or `STUDY_DIR`; exits with an error if neither is set.
- Loads and validates `study.yaml` against the Study schema.
- Loads every `.yaml` and `.yml` file in the manifest’s `conditions_dir` (default `conditions/`) and validates each as a Condition.
- On success: prints study name, study ID, and the list of condition names.
- On failure: prints a path-specific error (see [Error format](#error-format)) and exits with code 1.

### Options

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Path to the study folder. Recommended; alternatively use `STUDY_DIR`. |

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

Each line after the first lists a field path (or location) and the validation message. Multiple errors for the same file are listed together. This format is produced by the config layer when Pydantic validation fails; the same formatting is used by the `validate` command and can be used programmatically via `slumber.utils.errors.format_validation_error()`.

## Loading config programmatically

You can load and validate config without running the CLI:

- **`slumber.config.resolve_study_dir(study_dir=None)`** — Returns the study directory `Path` when it contains `study.yaml`. When `study_dir` is omitted, uses the current working directory. Raises **`ValueError`** if the given path is not a directory; raises **`FileNotFoundError`** if the directory does not contain a study manifest.
- **`slumber.config.load_study(study_dir)`** — Loads the manifest and returns a `Study` with its path set to `study_dir`. Use **`study.conditions`** to load and validate condition YAML files (raises `FileNotFoundError` or `ValueError` with path if invalid).
- **`slumber.utils.yaml.load_and_validate(path, model)`** — Loads YAML from `path` and validates as the given Pydantic model (e.g. `Study`, `Condition`). For a single `study.yaml`: `load_and_validate(manifest_path, Study)`. For a single condition file: `load_and_validate(condition_path, Condition)`.
- **`slumber.config.init_study(base_dir, study_id, ...)`** — Create a new study folder (manifest, conditions/, assets/). From `slumber.config.study`; also exported from `slumber.config`.
- **`slumber.schemas.load_conditions_from_dir(conditions_dir)`** — Low-level: load and validate all condition YAML files from a directory path; returns `list[Condition]`.
- **`slumber.utils.errors.format_validation_error(error, path=..., prefix=...)`** — Formats a Pydantic `ValidationError` with an optional file path for clear, path-specific messages.

All paths are interpreted as in the filesystem; the study manifest’s `conditions_dir` is relative to the study directory.
