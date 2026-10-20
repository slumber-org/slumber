# Validating a study

This page describes how the framework discovers a study folder, loads the manifest and condition files, and how validation errors are reported.

## Study discovery

For commands that accept a study folder:

1. **Explicit path** — Prefer `--study-dir <path>` (must contain `study.yaml`).
2. **Environment** — Set `STUDY_DIR` when `--study-dir` is omitted.

**`slumber study validate`** validates a single study folder:

```bash
slumber study validate --study-dir /path/to/my-study

export STUDY_DIR=/path/to/my-study
slumber study validate
```

## Validate command: `slumber study validate`

**Behavior:**

- Resolves the study folder from `--study-dir` or `STUDY_DIR`.
- Loads and validates `study.yaml` against the Study schema.
- Loads every `.yaml` / `.yml` file in `conditions_dir` and validates each as a Condition.
- Resolves plugins (`validate_study_plugins`): UI type, layouts, activities, units; unknown `entry`, phase/pipeline ids, and connection endpoints are errors.
- On success: prints study name, study ID, and condition names.
- On failure: prints a path-specific error and exits with code 1.

For options, see the [CLI reference](../reference/cli.md#slumber-study-validate).

## Error format

**Study manifest errors** (invalid `study.yaml`):

```text
Study manifest error: /path/to/study/study.yaml
  study_name: Field required
```

**Condition file errors**:

```text
Condition file error: /path/to/study/conditions/control.yaml
  entry: Field required
  phases: Field required
```

Each line after the first lists a field path and message. The same formatting is available via `slumber.utils.errors.format_validation_error()`.

## Loading config programmatically

- **`slumber.config.resolve_study_dir(study_dir=None)`** — Returns the study directory `Path` when it contains `study.yaml`.
- **`slumber.config.load_study(study_dir)`** — Loads the manifest and conditions into a `Study`.
- **`slumber.config.validate_study_plugins(study)`** — Resolves UI, layouts, activities, and units; checks ids and connections.
- **`slumber.config.init_study(base_dir, study_id, ...)`** — Creates a new study folder.
- **`slumber.schemas.load_conditions_from_dir(conditions_dir)`** — Load and validate condition YAML files from a directory.
- **`slumber.utils.yaml.load_and_validate(path, model)`** — Load YAML and validate as a Pydantic model.
