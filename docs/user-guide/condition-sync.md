# Condition sync

Conditions are defined as YAML files in the study folder and must be pushed to Supabase before participants can be assigned to them or sessions can reference them. The `slumber condition sync` command reads every condition file from the study's `conditions/` directory, validates it, and upserts each row into the Supabase `condition` table.

## When to run it

Run `condition sync` whenever you:

- Add a new condition YAML file.
- Edit an existing condition (procedures, DAG, or any other field).
- Set up a new Supabase project and need to populate the `condition` table for the first time.

## Requirements

The `condition` table write requires the Supabase service role. Set `SUPABASE_SERVICE_ROLE_KEY` in your `.env` before running:

```bash
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # Supabase project settings → API → service_role key
```

## Usage

From the study folder (or pass `--study-dir`):

```bash
# Sync all conditions
slumber condition sync --study-dir path/to/my-study

# Sync only specific conditions (repeat the flag for multiple)
slumber condition sync --study-dir path/to/my-study --conditions condition_1
slumber condition sync --study-dir path/to/my-study --conditions condition_1 --conditions condition_2
```

`--study-dir` can also be set via the `STUDY_DIR` environment variable:

```bash
export STUDY_DIR=path/to/my-study
slumber condition sync
```

### Options

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Path to the study folder (must contain `study.yaml`). Can also be set with `STUDY_DIR`. |
| `--conditions`, `-c` | Condition names to sync. Repeat for each name. If omitted, all conditions in the study folder are synced. |

## How it works

For each condition to sync:

1. The YAML file is loaded from `<study_id>/conditions/<name>.yaml` and validated against the `Condition` schema.
2. A row is upserted into the `condition` table with `id = {study_id}_{name}`, linking it to the study.
3. The `procedures` and `dag` fields are stored as JSONB.

If a condition with the same `id` already exists it is updated; otherwise it is inserted. The command prints a status line for each condition and a summary count on success.

## Condition YAML format

Each file in `conditions/` must match the `Condition` schema. At minimum:

```yaml
name: condition_1

procedures:
  pre_sleep:
    steps:
      - task: instruction
        settings:
          text: "Time to prepare for sleep."

dag:
  components:
    - name: MASTER
      unit_type: Master
  connections: []
  process_components: []
```

The `name` field must match the stem of the file (e.g. `condition_1.yaml` → `name: condition_1`). See the [Schema reference](../reference/schemas.md) for the full Condition, Procedure, and DAG schemas.

## Connecting sessions to conditions

After syncing, you can reference a condition when creating a session:

```bash
slumber session create \
  --participant-id my-study_sub-001 \
  --earliest-start-at 2025-10-01T22:00:00+00:00 \
  --latest-start-at   2025-10-02T02:00:00+00:00 \
  --condition-id my-study_condition_1
```

The `condition-id` value is `{study_id}_{condition_name}` — the same composite key used by `condition sync`.
