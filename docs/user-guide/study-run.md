# Running a study

There are two ways to run a study, and both share the run directory, run logging, and Sentry behaviour described below:

- **`slumber study run`** — local run from disk. You pass `--condition` explicitly; nothing is read from or written to a database. Useful for local testing/development, and for running SLUMBER without the `supabase` extra at all.
- **`slumber study run-scheduled`** *(requires `slumber[supabase]`)* — resolves the authenticated user's scheduled session and condition from Supabase and records a run row.

## slumber study run (local)

```bash
slumber study run --study-dir path/to/my-study --condition ctrl
```

| Option | Default | Description |
|--------|---------|-------------|
| `--study-dir`, `-d` | — | Path to the study folder. Also read from `STUDY_DIR`. |
| `--condition`, `-c` | — | Required. Condition `name` from the study's condition files. |

### What happens during a local run

1. **Study is loaded** — manifest and all condition files are validated.
2. **A new run id is generated** (UUID). Set `PARTICIPANT_ID` in the environment only if your run layout uses `{participant_id}`; there is no session.
3. **Sentry is initialized** (optional) — if `SENTRY_DSN` is set, Sentry is started and tagged with `study_id`.
4. **Run directory is created** — resolved from `study.runs.base_directory` and `study.runs.layout` with the run context placeholders.
5. **Run logging is applied** — loguru handlers from `study.logging.handlers` are added (placeholders like `{run_id}` are expanded).
6. **Procedures are executed** — each procedure in the condition is passed to the UI backend (`study.ui.backend`, default: `headless`).
7. **Logging handlers are removed** when the run finishes (even on error).

## slumber study run-scheduled

*Requires `slumber[supabase]`.*

Looks up the authenticated user's scheduled session, creates the run output directory, configures loguru from `study.logging`, runs each procedure in the session's condition through the configured UI backend, and writes a metadata file to the run directory.

Requires `slumber auth login` before running.

```bash
slumber study run-scheduled --study-dir path/to/my-study
```

| Option | Default | Description |
|--------|---------|-------------|
| `--study-dir`, `-d` | — | Path to the study folder. Also read from `STUDY_DIR`. |

Condition, participant, session, and run ID are all resolved from Supabase automatically. No manual arguments are needed.

### What happens during a scheduled run

1. **Study is loaded** — manifest and all condition files are validated.
2. **Participant is resolved** — the authenticated user's participant record is fetched from Supabase.
3. **Active session is found** — the session whose `earliest_start_at ≤ now ≤ latest_start_at` is selected for the participant.
4. **Run record is created** — a `Run` row is inserted into Supabase with `status=running`; its integer primary key is used as `run_id`.
5. **Sentry is initialized** (optional) — if `SENTRY_DSN` is set, Sentry is started and tagged with `study_id`.
6. **Run directory is created** — resolved from `study.runs.base_directory` and `study.runs.layout` with the run context placeholders.
7. **`run.json` is written** to the run directory with `study_id`, `condition_name`, `participant_id`, `session_id`, `run_id`, and `started_at`.
8. **Run logging is applied** — loguru handlers from `study.logging.handlers` are added (placeholders like `{run_id}` are expanded).
9. **Procedures are executed** — each procedure in the condition is passed to the UI backend (`study.ui.backend`, default: `headless`).
10. **Run record is updated** — status is set to `completed` (or `failed` on error) and `run_directory` is stored in Supabase.
11. **Logging handlers are removed** when the run finishes (even on error).

## Run directory

The run directory is `<study_dir>/<runs.base_directory>/<runs.layout>` with placeholders expanded. With the default layout:

```yaml
runs:
  base_directory: runs
  layout: sub-{participant_id}/ses-{session_id}/run-{run_id}
```

for participant `sub-001`, session ID `3`, and run ID `7` (the database primary keys):

```
my-study/runs/sub-sub-001/ses-3/run-7/
├── run.json
└── (log files from study.logging.handlers)
```

## Run logging

File-sink log handlers are configured in `study.yaml`:

```yaml
logging:
  level: INFO
  handlers:
    - sink: "{run_id}.log"
      level: DEBUG
      rotation: "10 MB"
```

See [Run directory layout and logging](run-layout-logging.md) for the full reference.

## Optional Sentry monitoring

Set `SENTRY_DSN` in your `.env` (or environment) to enable Sentry:

```bash
SENTRY_DSN=https://key@o0.ingest.sentry.io/0
```

All Sentry events during the run are tagged with `study_id`. When `SENTRY_DSN` is not set the Sentry code path is skipped entirely. `sentry-sdk` is an optional dependency:

```bash
pip install slumber[sentry]
# or
uv sync --extra sentry
```

## First study walkthrough

From a clean project directory:

```bash
# 1. Sign in
slumber auth login --email researcher@example.com

# 2. Create the study folder
slumber study init --base-dir . --study-id my-study --name "My Study"

# 3. Register the study in Supabase
slumber study register --study-dir my-study

# 4. Add a condition YAML
cat > my-study/conditions/ctrl.yaml << 'EOF'
name: ctrl
procedures:
  pre_sleep:
    steps:
      - task: instruction
        settings:
          text: "Please lie down and close your eyes."
dag:
  components:
    - name: MASTER
      unit_type: Master
  connections: []
  process_components: []
EOF

# 5. Sync conditions into Supabase
slumber condition sync --study-dir my-study

# 6. Create a participant and schedule a session (researcher side)
slumber participant create --study-id my-study --participant-id sub-001 --user-id <auth-user-uuid>
slumber session create --study-id my-study --participant-id sub-001 \
  --earliest-start-at 2025-10-01T20:00:00Z --latest-start-at 2025-10-01T23:59:00Z \
  --condition-id my-study_ctrl

# 7. Validate the study
slumber study validate --study-dir my-study

# 8. Run the study (participant side, during the scheduled window)
slumber study run-scheduled --study-dir my-study
```

The run output is written to `my-study/runs/sub-sub-001/ses-<session-id>/run-<run-id>/`.
