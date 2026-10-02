# Study folder structure and init

This page describes the standard study layout and how to create a new study with `slumber study init`.

## Study folder structure

A study is a single folder identified by a **study ID** (the folder name). The **project root** is where you run `slumber study init`; it can contain one or more study folders.

Standard layout:

| Location | Path | Description |
|----------|------|-------------|
| **Study folder** | `<study_id>/study.yaml` | Study manifest: id, name, dirs, runs, logging, UI. Required. |
| **Study folder** | `<study_id>/conditions/` | One YAML file per condition (phases + pipelines). |
| **Study folder** | `<study_id>/assets/` | Optional assets (markdown, images) referenced via placeholders. |
| **Study folder** | `<study_id>/runs/` | Run output (created by init; written by `study run`). |
| **Study folder** | `<study_id>/.gitignore` | Ignores `.env` and `.env.*`. Created by init unless skipped. |

Example:

```text
<project-root>/
├── my-study/
│   ├── study.yaml
│   ├── conditions/
│   │   ├── control.yaml
│   │   └── treatment.yaml
│   ├── assets/
│   │   └── instructions/
│   ├── runs/
│   └── .gitignore
```

The manifest schema is described in the [Schema reference](../reference/schemas.md).

## Creating a new study: `slumber study init`

```bash
slumber study init
```

You will be prompted for:

- **Base directory** — default: `.`
- **Study ID** — folder name (default: `new_study`)
- **Name** — human-readable study name (written as `study_name`)

The command creates `<base_dir>/<study_id>/` with:

- A template `study.yaml` (`study_id`, `study_name`, default dirs, `ui.type: headless`)
- Empty `conditions/`, `assets/`, and `runs/` directories
- Optional `.env` and `.gitignore` inside the study folder

### Options

| Option | Description |
|--------|-------------|
| `--base-dir`, `-b` | Parent directory; study folder is `<base-dir>/<study-id>/`. Default: `.`. |
| `--study-id`, `-s` | Study identifier (folder name). |
| `--name`, `-n` | Human-readable study name; used as `study_name` in `study.yaml`. |
| `--no-env-example` | Do not create `.env` inside the study folder. |
| `--no-gitignore` | Do not create `.gitignore` inside the study folder. |

```bash
slumber study init --base-dir . --study-id ld-2025 --name "Lucid Dreaming Pilot"
```

### After init

1. `cd` into the study folder.
2. Add condition YAML files under `conditions/` (see [Schema reference](../reference/schemas.md) and `examples/demo/`).
3. Run `slumber study validate --study-dir .` (see [Config loading and validation](config-validation.md)).
4. Run with `slumber study run --study-dir . --condition <name>` (see [Running a study](study-run.md)).

Local study run does not require a remote backend.
