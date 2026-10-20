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

The manifest schema is described in the [Configuration reference](../reference/configuration.md).

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

To skip the prompts, pass the values as options (see the [CLI reference](../reference/cli.md#slumber-study-init) for all options):

```bash
slumber study init --base-dir . --study-id ld-2025 --name "Lucid Dreaming Pilot"
```

### After init

1. `cd` into the study folder.
2. Add condition YAML files under `conditions/` (see [Configuration reference](../reference/configuration.md) and `examples/demo/`).
3. Run `slumber study validate --study-dir .` (see [Validating a study](validating-a-study.md)).
4. Run with `slumber study run --study-dir . --condition <name>` (see [Running a study](running-a-study.md)).

Local study run does not require a remote backend.
