# Study folder structure and init

This page describes the standard study layout and how to create a new study with `slumber study init`.

## Study folder structure

A study is a single folder identified by a **study ID** (the folder name). The **project root** (base directory) is where you run `slumber study init`; it can contain one or more study folders and shared files like `.env` and `.gitignore`.

Standard layout:

| Location | Path | Description |
|----------|------|-------------|
| **Study folder** | `<study_id>/study.yaml` | Study manifest: metadata, conditions dir, run layout, logging, UI. Required. |
| **Study folder** | `<study_id>/conditions/` | One YAML file per condition (e.g. `condition_1.yaml`). |
| **Study folder** | `<study_id>/assets/` | Optional assets (images, instructions, etc.) referenced by procedures. |
| **Study folder** | `<study_id>/.env` | Env file created by init from config template (SUPABASE_URL, SUPABASE_ANON_KEY). Gitignored. |
| **Study folder** | `<study_id>/.gitignore` | Ensures `.env` and `.env.*` are not committed. Created by init. |

Example:

```text
<project-root>/
├── my-study/
│   ├── study.yaml
│   ├── conditions/
│   │   ├── control.yaml
│   │   └── treatment.yaml
│   ├── assets/
│   ├── .env            # from config template; fill in values (gitignored)
│   └── .gitignore     # includes .env and .env.*
```

The manifest schema (fields in `study.yaml`) is described in the [Schema reference](../reference/schemas.md).

## Creating a new study: `slumber study init`

From your project root (or any base directory), run:

```bash
slumber study init
```

You will be prompted for:

- **Base directory (project root)** — default: `.` (current directory).
- **Study ID** — folder name (default: `new_study`). Must be non-empty.

The command creates `<base_dir>/<study_id>/` with:

- A template `study.yaml` (study_id, name, `conditions_dir: conditions`, default run layout, logging, and `ui.backend: headless`).
- Empty `conditions/` and `assets/` directories.
- **`.env`** inside the study folder (from the study env template in config: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, optional `SENTRY_DSN`), unless `--no-env-example` is used.
- **`.gitignore`** inside the study folder (includes `.env` and `.env.*`), unless `--no-gitignore` is used.

### Options

| Option | Description |
|--------|-------------|
| `--base-dir`, `-b` | Base directory (project root); study folder is `<base-dir>/<study-id>/`. Default: `.`. |
| `--study-id`, `-s` | Study identifier (folder name). If omitted, the command prompts for base dir and study ID. |
| `--name`, `-n` | Human-readable study name; used in `study.yaml`. Defaults to the study ID. |
| `--no-env-example` | Do not create `.env` inside the study folder. |
| `--no-gitignore` | Do not create `.gitignore` inside the study folder. |

Non-interactive example (e.g. for scripts or CI):

```bash
slumber study init --base-dir . --study-id ld-2025 --name "Lucid Dreaming Pilot"
```

### After init

1. `cd` into the study folder.
2. Add condition YAML files under `conditions/`.
3. Run `slumber study validate --study-dir .` (or set `STUDY_DIR`) to check the manifest and conditions (see [Config loading and validation](config-validation.md)).
4. When ready, run the study with `slumber study run` (see run documentation).

## .gitignore and .env (inside study folder)

When you run `slumber study init`, optional files are created **inside the study folder** (`<study_id>/`):

- **`.env`** — Created from the study env template in `slumber.config.templates` (commented placeholders for `SUPABASE_URL`, `SUPABASE_ANON_KEY`, optional `SENTRY_DSN`). It does **not** include `DATABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` (those are for researcher setup; see [Backend](../reference/backend.md)). Fill in values; do not commit `.env`.
- **`.gitignore`** — Ensures `.env` and `.env.*` (e.g. `.env.dev`, `.env.prod`) are ignored by Git so secrets are never committed.

Use `--no-env-example` or `--no-gitignore` to skip creating these files.
