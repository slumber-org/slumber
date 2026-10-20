# Study setup

This page shows how to create a new study package with `slumber study init` and what goes where inside it.

## Create a study

Run the command and answer the prompts:

```bash
slumber study init
```

You are asked for:

- **Base directory**: where the study folder is created (default: `.`)
- **Study ID**: the folder name and `study_id` (default: `new_study`)
- **Name**: the human-readable `study_name`

To skip the prompts, pass the values as options:

```bash
slumber study init --base-dir . --study-id sleep-study --name "Sleep Study"
```

For all options, see the [CLI reference](../reference/cli.md#slumber-study-init).

## The study folder

`study init` creates `<base_dir>/<study_id>/`:

```text
sleep-study/
├── study.yaml      # the study manifest
├── conditions/     # one YAML file per condition (empty)
├── assets/         # instruction texts, images, logo (empty)
├── runs/           # one folder per run, written by `study run`
└── .gitignore
```

## Fill in `study.yaml`

The generated manifest already validates. The fields you are most likely to change:

- **`study_id`** and **`study_name`**: set by `init`. `study_name` is available as `{study_name}`, for example in the GUI header.
- **`ui.type`**: `init` writes `headless`. Change it to `gui` to show the participant window. See [Participant UI](nicegui-ui.md).
- **`conditions_dir`** and **`assets_dir`**: only change these if you want different folder names.
- **`runs`**: where run folders go and how they are named. See [Run output and logging](run-output-and-logging.md).
- **`logging`**: log level and log files. See [Run output and logging](run-output-and-logging.md).

For every field and its default, see the [Configuration reference](../reference/configuration.md#study-manifest-studyyaml).

## Add assets

Put files that conditions refer to, such as instruction texts, in `assets/`. Subfolders are fine:

```text
assets/
└── instructions/
    ├── intro.md
    └── morning.md
```

Refer to them from YAML with the `{assets_dir}` placeholder, for example `"{assets_dir}/instructions/intro.md"`. See [Paths and placeholders](paths-and-placeholders.md).

## Next: write a condition

A study can't run until it has at least one condition. Continue with [Writing conditions](writing-conditions.md).
